"""
Servidor web del Asistente ECyD (FastAPI).

    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import auth, programas, prompts
from .assistant import get_assistant
from .config import BASE_DIR, settings
from .memory import CATEGORIAS, get_store, store_kind
from .retrieval import get_retriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ecyd.web")

WEB_DIR = BASE_DIR / "web"
app = FastAPI(title="Asistente ECyD", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

_state = {"rag": "cargando", "rag_error": None, "loader": None}


_load_lock = threading.Lock()


def _ensure_rag_loading(block: bool = False):
    """Carga el corpus y el modelo (una sola vez por instancia).

    En Vercel las funciones se congelan entre pedidos, así que un hilo en
    segundo plano casi no avanza: ahí la carga se hace dentro del pedido."""
    if _state["rag"] == "error" and time.time() - _state.get("error_at", 0) > 20:
        # reintento automático: limpia descargas a medias y vuelve a cargar
        _cleanup_model_cache()
        _state.update(rag="cargando", rag_error=None, loader=None)
    if _state["rag"] != "cargando":
        return
    if block or os.getenv("VERCEL"):
        with _load_lock:
            if _state["rag"] == "cargando":
                _load_rag()
        return
    if _state["loader"] is None:
        t = threading.Thread(target=_load_rag, daemon=True)
        _state["loader"] = t
        t.start()


def _cleanup_model_cache():
    if not os.getenv("VERCEL"):
        return
    import shutil
    for d in ("/tmp/hf", settings.embedding_cache):
        shutil.rmtree(d, ignore_errors=True)


def _load_rag():
    try:
        r = get_retriever()
        r.warmup()
        _state["rag"] = "listo"
    except Exception as e:  # noqa: BLE001
        log.exception("No se pudo cargar el RAG")
        _state["rag"] = "error"
        _state["rag_error"] = str(e)
        _state["error_at"] = time.time()


@app.on_event("startup")
def startup():
    if not os.getenv("VERCEL"):
        _ensure_rag_loading()


# ------------------------------------------------------------------ cuentas y sesión
PUBLIC = {"/", "/api/session", "/api/login", "/api/register", "/api/logout", "/api/health", "/favicon.ico"}


def _current_user(request: Request):
    uid = auth.read_token(request.cookies.get(auth.COOKIE, ""))
    if not uid:
        return None
    try:
        return get_store().get_user(uid)
    except Exception:  # noqa: BLE001
        log.exception("No se pudo leer el usuario")
        return None


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in PUBLIC:
        user = _current_user(request)
        if not user:
            return JSONResponse({"detail": "Iniciá sesión para continuar"}, status_code=401)
        request.state.user = user
    return await call_next(request)


def _uid(request: Request) -> str:
    return request.state.user["id"]


def _set_session(resp: JSONResponse, user_id: str):
    resp.set_cookie(auth.COOKIE, auth.make_token(user_id), httponly=True, samesite="lax",
                    secure=bool(os.getenv("VERCEL")), max_age=60 * 60 * 24 * auth.SESSION_DAYS)


class LoginIn(BaseModel):
    email: str = Field(..., max_length=200)
    password: str = Field(..., max_length=200)


class RegisterIn(LoginIn):
    nombre: str = Field(..., max_length=120)
    rol: str = Field("", max_length=120)
    codigo: str = Field("", max_length=200)


@app.get("/api/session")
def session(request: Request):
    user = _current_user(request)
    try:
        sin_cuentas = get_store().count_users() == 0
    except Exception:  # noqa: BLE001
        sin_cuentas = False
    return {"authenticated": bool(user), "user": auth.public_user(user),
            "registration_requires_code": bool(auth.registration_code()), "first_user": sin_cuentas}


@app.post("/api/register")
def register(body: RegisterIn, request: Request):
    ip = request.client.host if request.client else "?"
    if auth.too_many_attempts("reg:" + ip, limit=8):
        raise HTTPException(429, "Demasiados intentos. Probá de nuevo en unos minutos.")
    code = auth.registration_code()
    if code and not hmac.compare_digest(body.codigo.strip(), code):
        raise HTTPException(403, "El código de acceso no es correcto. Pedíselo a quien administra el asistente.")
    err = auth.validate_new_account(body.email, body.password, body.nombre)
    if err:
        raise HTTPException(400, err)
    store = get_store()
    if store.get_user_by_email(body.email):
        raise HTTPException(409, "Ya existe una cuenta con ese email. Iniciá sesión.")
    primera = store.count_users() == 0
    user = store.create_user(body.email, body.nombre, auth.hash_password(body.password), body.rol)
    adoptados = store.claim_orphans(user["id"]) if primera else {}
    resp = JSONResponse({"ok": True, "user": auth.public_user(user), "datos_asignados": adoptados})
    _set_session(resp, user["id"])
    return resp


@app.post("/api/login")
def login(body: LoginIn, request: Request):
    ip = request.client.host if request.client else "?"
    key = f"login:{ip}:{body.email.strip().lower()}"
    if auth.too_many_attempts(key):
        raise HTTPException(429, "Demasiados intentos. Probá de nuevo en unos minutos.")
    user = get_store().get_user_by_email(body.email)
    if not user or not auth.verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Email o contraseña incorrectos")
    auth.reset_attempts(key)
    resp = JSONResponse({"ok": True, "user": auth.public_user(user)})
    _set_session(resp, user["id"])
    return resp


@app.post("/api/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(auth.COOKIE)
    return resp


class MeUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=120)
    rol: Optional[str] = Field(None, max_length=120)


class PasswordChange(BaseModel):
    actual: str = Field(..., max_length=200)
    nueva: str = Field(..., max_length=200)


@app.get("/api/me")
def me(request: Request):
    return auth.public_user(request.state.user)


@app.put("/api/me")
def update_me(body: MeUpdate, request: Request):
    u = get_store().update_user(_uid(request), nombre=(body.nombre or "").strip() or None,
                                rol=(body.rol or "").strip() or None)
    return auth.public_user(u)


@app.post("/api/me/password")
def change_password(body: PasswordChange, request: Request):
    user = request.state.user
    if not auth.verify_password(body.actual, user["password_hash"]):
        raise HTTPException(400, "La contraseña actual no es correcta")
    if len(body.nueva) < 8:
        raise HTTPException(400, "La contraseña nueva debe tener al menos 8 caracteres")
    get_store().update_user(user["id"], password_hash=auth.hash_password(body.nueva))
    return {"ok": True}


# ------------------------------------------------------------------ info
@app.get("/api/health")
def health():
    _ensure_rag_loading()
    info = {"rag": _state["rag"], "llm_provider": settings.llm_provider,
            "llm_configurado": bool(settings.groq_api_key if settings.llm_provider != "gemini" else settings.gemini_api_key),
            "modelo": settings.groq_model if settings.llm_provider != "gemini" else settings.gemini_model}
    if _state["rag"] == "listo":
        info["corpus"] = get_retriever().stats()
    if _state["rag_error"]:
        info["rag_error"] = _state["rag_error"]
    try:
        info["memoria"] = store_kind()
        get_store().count_users()
        info["memoria_ok"] = True
    except Exception as e:  # noqa: BLE001
        info["memoria_ok"] = False
        info["memoria_error"] = str(e)[:300]
    return info


@app.get("/api/config")
def ui_config():
    portada = next((f"/static/img/{f}" for f in ("portada.jpg", "portada.webp", "portada.png")
                    if (WEB_DIR / "img" / f).exists()), None)
    from .corpus import CATEGORIAS as CAT_DOCS
    return {"team_fields": [{"key": k, "label": l} for k, l in prompts.TEAM_FIELDS],
            "categorias": CATEGORIAS, "categorias_documentos": CAT_DOCS, "portada": portada}


@app.get("/api/documents")
def documents():
    return get_retriever().document_list()


@app.get("/api/documents/{doc_id}")
def document_detail(doc_id: str):
    r = get_retriever()
    d = r.doc_by_id.get(doc_id)
    if not d:
        raise HTTPException(404, "Documento no encontrado")
    item = next(x for x in r.document_list() if x["id"] == doc_id)
    return {**item, "texto": r.document_text(doc_id, max_chars=60000)}


# ------------------------------------------------------------------ programa por etapa
@app.get("/api/programas")
def programas_todos():
    data = programas.load()
    etapas = {}
    for k, e in data.get("etapas", {}).items():
        etapas[k] = {key: e.get(key) for key in ("etapa", "nombre", "edades", "nivel_escolar_mexico", "resumen",
                                                 "necesidades", "temas_centrales", "calendario", "tiempos_liturgicos")}
        etapas[k]["secciones"] = {key: e.get("secciones", {}).get(key, "") for key in
                                  ("fisico", "piensa_siente", "le_ayuda", "pistas")}
    return {"fuente": data.get("fuente"), "nota_calendario": data.get("nota_calendario"),
            "periodos": [{"periodo": p, "label": programas.PERIODO_LABEL.get(p, p)} for p in data.get("periodos", [])],
            "etapas": etapas}


@app.get("/api/programa")
def programa_actual(request: Request, etapa: Optional[int] = None, team_id: Optional[str] = None,
                    fecha: Optional[str] = None):
    if team_id and not etapa:
        from .assistant import parse_etapa
        etapa = parse_etapa(_team_or_404(team_id, request)["perfil"].get("etapa"))
    hoy = None
    if fecha:
        try:
            from datetime import date as _d
            hoy = _d.fromisoformat(fecha[:10])
        except ValueError:
            pass
    return programas.sugerencias(etapa, hoy)


# ------------------------------------------------------------------ equipos
class TeamIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    perfil: dict = {}
    auto_memoria: bool = True


class TeamUpdate(BaseModel):
    nombre: Optional[str] = None
    perfil: Optional[dict] = None
    auto_memoria: Optional[bool] = None


def _team_or_404(team_id, request: Request):
    t = get_store().get_team(team_id)
    if not t or t.get("user_id") != _uid(request):
        raise HTTPException(404, "Equipo no encontrado")
    return t


@app.get("/api/teams")
def list_teams(request: Request):
    return get_store().list_teams(user_id=_uid(request))


@app.post("/api/teams")
def create_team(body: TeamIn, request: Request):
    perfil = {k: str(v)[:1000] for k, v in body.perfil.items() if v not in (None, "")}
    return get_store().create_team(body.nombre, perfil, body.auto_memoria, user_id=_uid(request))


@app.get("/api/teams/{team_id}")
def get_team(team_id: str, request: Request):
    return _team_or_404(team_id, request)


@app.put("/api/teams/{team_id}")
def update_team(team_id: str, body: TeamUpdate, request: Request):
    _team_or_404(team_id, request)
    perfil = None if body.perfil is None else {k: str(v)[:1000] for k, v in body.perfil.items() if v not in (None, "")}
    return get_store().update_team(team_id, nombre=body.nombre, perfil=perfil, auto_memoria=body.auto_memoria)


@app.delete("/api/teams/{team_id}")
def delete_team(team_id: str, request: Request):
    _team_or_404(team_id, request)
    if not get_store().delete_team(team_id):
        raise HTTPException(404, "Equipo no encontrado")
    return {"ok": True}


@app.get("/api/teams/{team_id}/export")
def export_team(team_id: str, request: Request):
    _team_or_404(team_id, request)
    data = get_store().export_team(team_id)
    return JSONResponse(data, headers={"Content-Disposition": f'attachment; filename="equipo-{team_id}.json"'})


# ------------------------------------------------------------------ memoria
class MemoryIn(BaseModel):
    texto: str = Field(..., min_length=2, max_length=1000)
    categoria: str = "general"


class MemoryUpdate(BaseModel):
    texto: Optional[str] = Field(None, max_length=1000)
    categoria: Optional[str] = None


@app.get("/api/teams/{team_id}/memories")
def list_memories(team_id: str, request: Request):
    _team_or_404(team_id, request)
    return get_store().list_memories(team_id)


@app.post("/api/teams/{team_id}/memories")
def add_memory(team_id: str, body: MemoryIn, request: Request):
    _team_or_404(team_id, request)
    return get_store().add_memory(team_id, body.texto, body.categoria, origen="manual")


@app.put("/api/teams/{team_id}/memories/{memory_id}")
def update_memory(team_id: str, memory_id: int, body: MemoryUpdate, request: Request):
    _team_or_404(team_id, request)
    r = get_store().update_memory(memory_id, texto=body.texto, categoria=body.categoria, team_id=team_id)
    if not r:
        raise HTTPException(404, "Recuerdo no encontrado")
    return r


@app.delete("/api/teams/{team_id}/memories/{memory_id}")
def delete_memory(team_id: str, memory_id: int, request: Request):
    _team_or_404(team_id, request)
    if not get_store().delete_memory(memory_id, team_id):
        raise HTTPException(404, "Recuerdo no encontrado")
    return {"ok": True}


@app.delete("/api/teams/{team_id}/memories")
def clear_memories(team_id: str, request: Request):
    _team_or_404(team_id, request)
    return {"borrados": get_store().clear_memories(team_id)}


# ------------------------------------------------------------------ conversaciones
class ConversationUpdate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=120)
    notas: Optional[str] = Field(None, max_length=3000)


def _conv_or_404(cid: str, request: Request):
    conv = get_store().get_conversation(cid)
    if not conv or conv.get("user_id") != _uid(request):
        raise HTTPException(404, "Conversación no encontrada")
    return conv


@app.get("/api/conversations")
def list_conversations(request: Request, team_id: Optional[str] = None):
    return get_store().list_conversations(team_id, user_id=_uid(request))


@app.get("/api/conversations/{cid}")
def get_conversation(cid: str, request: Request):
    conv = _conv_or_404(cid, request)
    return {**conv, "messages": get_store().get_messages(cid)}


@app.patch("/api/conversations/{cid}")
def patch_conversation(cid: str, body: ConversationUpdate, request: Request):
    _conv_or_404(cid, request)
    return get_store().update_conversation(cid, titulo=body.titulo, notas=body.notas)


@app.delete("/api/conversations/{cid}")
def delete_conversation(cid: str, request: Request):
    _conv_or_404(cid, request)
    get_store().delete_conversation(cid)
    return {"ok": True}


# ------------------------------------------------------------------ chat
class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    conversation_id: Optional[str] = None
    team_id: Optional[str] = None


def _sse(gen):
    def events():
        try:
            for ev in gen:
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except Exception as e:  # noqa: BLE001
            log.exception("Error en el stream")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _require_rag():
    _ensure_rag_loading()
    if _state["rag"] == "error":
        raise HTTPException(503, f"El corpus no está disponible: {_state['rag_error']}")


@app.post("/api/chat")
def chat(body: ChatIn, request: Request):
    _require_rag()
    if body.team_id:
        _team_or_404(body.team_id, request)
    if body.conversation_id:
        _conv_or_404(body.conversation_id, request)
    return _sse(get_assistant().stream(body.message, body.conversation_id, body.team_id, user_id=_uid(request)))


# ------------------------------------------------------------------ encuentros
class EncuentroIn(BaseModel):
    team_id: Optional[str] = None
    titulo: Optional[str] = Field(None, max_length=140)
    fecha: Optional[str] = Field(None, max_length=10)
    etapa: Optional[int] = None
    tema: Optional[str] = Field(None, max_length=300)
    origen_tema: Optional[str] = None
    periodo: Optional[str] = Field(None, max_length=60)
    fichas: Optional[list] = None
    cantidad: Optional[int] = None
    composicion: Optional[str] = Field(None, max_length=40)
    edades: Optional[str] = Field(None, max_length=60)
    duracion: Optional[str] = Field(None, max_length=60)
    propuesta: Optional[str] = Field(None, max_length=60000)
    observaciones: Optional[str] = Field(None, max_length=8000)
    estado: Optional[str] = None
    meta: Optional[dict] = None


class GenerarIn(BaseModel):
    team_id: str
    tema: str = Field("", max_length=300)
    origen_tema: str = "otro"
    periodo: str = Field("", max_length=60)
    fichas: list = []
    fecha: Optional[str] = Field(None, max_length=10)
    cantidad: Optional[int] = None
    composicion: str = Field("", max_length=40)
    edades: str = Field("", max_length=60)
    duracion: str = Field("", max_length=60)
    notas: str = Field("", max_length=2000)
    encuentro_id: Optional[str] = None


def _enc_or_404(eid: str, request: Request):
    e = get_store().get_encuentro(eid)
    if not e or e.get("user_id") != _uid(request):
        raise HTTPException(404, "Encuentro no encontrado")
    return e


def _with_team_name(items, request: Request):
    teams = {t["id"]: t["nombre"] for t in get_store().list_teams(user_id=_uid(request))}
    for e in items:
        e["team_nombre"] = teams.get(e.get("team_id"), "")
    return items


@app.get("/api/encuentros")
def list_encuentros(request: Request, team_id: Optional[str] = None):
    if team_id:
        _team_or_404(team_id, request)
    return _with_team_name(get_store().list_encuentros(user_id=_uid(request), team_id=team_id), request)


@app.post("/api/encuentros")
def create_encuentro(body: EncuentroIn, request: Request):
    data = body.model_dump(exclude_none=True)
    if data.get("team_id"):
        _team_or_404(data["team_id"], request)
    return get_store().create_encuentro(_uid(request), data)


@app.get("/api/encuentros/{eid}")
def get_encuentro(eid: str, request: Request):
    return _with_team_name([_enc_or_404(eid, request)], request)[0]


@app.put("/api/encuentros/{eid}")
def update_encuentro(eid: str, body: EncuentroIn, request: Request):
    _enc_or_404(eid, request)
    data = body.model_dump(exclude_none=True)
    if data.get("team_id"):
        _team_or_404(data["team_id"], request)
    return get_store().update_encuentro(eid, data)


@app.delete("/api/encuentros/{eid}")
def delete_encuentro(eid: str, request: Request):
    _enc_or_404(eid, request)
    get_store().delete_encuentro(eid)
    return {"ok": True}


@app.post("/api/encuentros/generar")
def generar_encuentro(body: GenerarIn, request: Request):
    _require_rag()
    team = _team_or_404(body.team_id, request)
    if body.encuentro_id:
        _enc_or_404(body.encuentro_id, request)
    return _sse(get_assistant().stream_encuentro(team, body.model_dump(), user_id=_uid(request)))


class AjusteIn(BaseModel):
    instruccion: str = Field(..., min_length=2, max_length=2000)
    propuesta: Optional[str] = Field(None, max_length=60000)


@app.post("/api/encuentros/{eid}/ajustar")
def ajustar_encuentro(eid: str, body: AjusteIn, request: Request):
    """La IA modifica la propuesta según las aclaraciones del responsable."""
    _require_rag()
    enc = _enc_or_404(eid, request)
    team = _team_or_404(enc["team_id"], request) if enc.get("team_id") else None
    propuesta = body.propuesta if body.propuesta is not None else (enc.get("propuesta") or "")
    if not propuesta.strip():
        raise HTTPException(400, "Este encuentro todavía no tiene propuesta para ajustar")
    return _sse(get_assistant().stream_ajuste(enc, team, body.instruccion, propuesta))


# ------------------------------------------------------------------ frontend
@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/favicon.ico")
def favicon():
    return FileResponse(WEB_DIR / "favicon.svg", media_type="image/svg+xml")
