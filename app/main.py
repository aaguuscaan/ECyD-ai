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


# ------------------------------------------------------------------ permisos
# Equipo personal (sin comunidad): lo usa quien lo creó (y sus co-responsables).
# Equipo de una comunidad: lo usan sus responsables asignados. El coordinador de
# la comunidad ve la planificación (encuentros) pero NO la memoria del equipo,
# que puede tener información de los adolescentes.
def _community_rol(cid: Optional[str], uid: str) -> Optional[str]:
    if not cid:
        return None
    return next((m["rol"] for m in get_store().list_community_members(cid) if m["user_id"] == uid), None)


def _team_access(team: dict, uid: str) -> Optional[str]:
    store = get_store()
    miembros = {m["user_id"] for m in store.list_team_members([team["id"]])}
    if uid in miembros or (not team.get("community_id") and team.get("user_id") == uid):
        return "responsable"
    if team.get("community_id") and _community_rol(team["community_id"], uid) == "coordinador":
        return "coordinador"
    return None


def _team_or_404(team_id, request: Request, allow_coord: bool = False):
    t = get_store().get_team(team_id)
    acceso = _team_access(t, _uid(request)) if t else None
    if not acceso or (acceso == "coordinador" and not allow_coord):
        raise HTTPException(404, "Equipo no encontrado")
    t["acceso"] = acceso
    return t


def _my_teams(uid: str) -> list:
    """Equipos que el responsable usa: los personales que creó y aquellos donde está asignado."""
    store = get_store()
    propios = [t for t in store.list_teams(user_id=uid) if not t.get("community_id")]
    ids = {t["id"] for t in propios}
    asignados = [t for t in store.list_teams(ids=[i for i in store.member_team_ids(uid) if i not in ids])]
    teams = sorted(propios + asignados, key=lambda t: t["nombre"].lower())
    return _annotate_teams(teams, uid)


def _annotate_teams(teams: list, uid: str) -> list:
    store = get_store()
    miembros = store.list_team_members([t["id"] for t in teams])
    coms = {c["id"]: c for c in store.list_user_communities(uid)}
    for t in teams:
        t["responsables"] = [{"user_id": m["user_id"], "nombre": m["nombre"]} for m in miembros if m["team_id"] == t["id"]]
        c = coms.get(t.get("community_id"))
        t["comunidad"] = {"id": c["id"], "nombre": c["nombre"]} if c else None
    return teams


@app.get("/api/teams")
def list_teams(request: Request):
    return _my_teams(_uid(request))


@app.post("/api/teams")
def create_team(body: TeamIn, request: Request):
    perfil = {k: str(v)[:1000] for k, v in body.perfil.items() if v not in (None, "")}
    return get_store().create_team(body.nombre, perfil, body.auto_memoria, user_id=_uid(request))


@app.get("/api/teams/{team_id}")
def get_team(team_id: str, request: Request):
    return _annotate_teams([_team_or_404(team_id, request)], _uid(request))[0]


@app.put("/api/teams/{team_id}")
def update_team(team_id: str, body: TeamUpdate, request: Request):
    _team_or_404(team_id, request)
    perfil = None if body.perfil is None else {k: str(v)[:1000] for k, v in body.perfil.items() if v not in (None, "")}
    return get_store().update_team(team_id, nombre=body.nombre, perfil=perfil, auto_memoria=body.auto_memoria)


@app.delete("/api/teams/{team_id}")
def delete_team(team_id: str, request: Request):
    _team_or_404(team_id, request, allow_coord=True)
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
    feedback: Optional[dict] = None


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


def _enc_or_404(eid: str, request: Request, read_only: bool = False):
    """Autor o responsable del equipo: acceso completo. Coordinador de la
    comunidad: solo lectura de la propuesta (sin observaciones)."""
    e = get_store().get_encuentro(eid)
    uid = _uid(request)
    if e and e.get("user_id") == uid:
        return e
    team = get_store().get_team(e["team_id"]) if e and e.get("team_id") else None
    acceso = _team_access(team, uid) if team else None
    if acceso == "responsable":
        return e
    if acceso == "coordinador" and read_only:
        fb = e.get("feedback") or None
        e = {**e, "observaciones": "", "solo_lectura": True,
             "feedback": {"puntuacion": fb.get("puntuacion"), "asistentes": fb.get("asistentes")} if fb else None}
        e["meta"] = {k: v for k, v in (e.get("meta") or {}).items() if k in ("sources", "aviso")}
        return e
    raise HTTPException(404, "Encuentro no encontrado")


def _with_team_name(items, request: Request):
    store = get_store()
    ids = list({e["team_id"] for e in items if e.get("team_id")})
    teams = {t["id"]: t["nombre"] for t in store.list_teams(ids=ids)} if ids else {}
    for e in items:
        e["team_nombre"] = teams.get(e.get("team_id"), "")
    return items


@app.get("/api/encuentros")
def list_encuentros(request: Request, team_id: Optional[str] = None):
    uid = _uid(request)
    if team_id:
        _team_or_404(team_id, request)
        return _with_team_name(get_store().list_encuentros(team_id=team_id), request)
    ids = [t["id"] for t in _my_teams(uid)]
    return _with_team_name(get_store().list_encuentros(user_id=uid, team_ids=ids), request)


@app.post("/api/encuentros")
def create_encuentro(body: EncuentroIn, request: Request):
    data = body.model_dump(exclude_none=True)
    if data.get("team_id"):
        _team_or_404(data["team_id"], request)
    return get_store().create_encuentro(_uid(request), data)


@app.get("/api/encuentros/{eid}")
def get_encuentro(eid: str, request: Request):
    return _with_team_name([_enc_or_404(eid, request, read_only=True)], request)[0]


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


class PdfIn(BaseModel):
    propuesta: Optional[str] = Field(None, max_length=60000)
    titulo: Optional[str] = Field(None, max_length=140)


@app.post("/api/encuentros/{eid}/pdf")
def encuentro_pdf(eid: str, body: PdfIn, request: Request):
    """Descarga el encuentro como PDF (con lo que está en pantalla, aunque no se haya guardado)."""
    from fastapi.responses import Response
    from . import pdf
    enc = dict(_enc_or_404(eid, request, read_only=True))
    if not enc.get("solo_lectura"):
        if body.propuesta is not None:
            enc["propuesta"] = body.propuesta
        if body.titulo:
            enc["titulo"] = body.titulo
    equipo = ""
    if enc.get("team_id"):
        t = get_store().get_team(enc["team_id"])
        equipo = (t or {}).get("nombre", "")
    data = pdf.encuentro_pdf(enc, equipo=equipo, incluir_observaciones=not enc.get("solo_lectura"))
    nombre = pdf.nombre_archivo(enc)
    return Response(data, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


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


# ------------------------------------------------------------------ comunidades
class ComunidadIn(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    lugar: str = Field("", max_length=120)


class ComunidadUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    lugar: Optional[str] = Field(None, max_length=120)


class UnirseIn(BaseModel):
    codigo: str = Field(..., min_length=4, max_length=20)


class MiembroUpdate(BaseModel):
    rol: str


class EquipoComunidadIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    etapa: Optional[int] = Field(None, ge=1, le=4)
    edades: str = Field("", max_length=60)
    responsables: list = []


class EquipoComunidadUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=80)
    etapa: Optional[int] = Field(None, ge=1, le=4)
    responsables: Optional[list] = None


class MoverEquipoIn(BaseModel):
    community_id: str


def _com_or_404(cid: str, request: Request, coord: bool = False):
    com = get_store().get_community(cid)
    rol = _community_rol(cid, _uid(request)) if com else None
    if not rol:
        raise HTTPException(404, "Comunidad no encontrada")
    if coord and rol != "coordinador":
        raise HTTPException(403, "Solo la coordinación de la comunidad puede hacer esto")
    return {**com, "rol": rol}


def _com_public(c: dict) -> dict:
    out = {k: c.get(k) for k in ("id", "nombre", "lugar", "rol", "created_at")}
    if c.get("rol") == "coordinador":
        out["codigo"] = c.get("codigo")
    return out


def _check_responsables(cid: str, ids: list) -> list:
    miembros = {m["user_id"] for m in get_store().list_community_members(cid)}
    ids = [str(i) for i in ids if i]
    if any(i not in miembros for i in ids):
        raise HTTPException(400, "Los responsables tienen que ser miembros de la comunidad")
    return list(dict.fromkeys(ids))


def _mes_rango(mes: Optional[str]):
    from datetime import date as _d
    hoy = _d.today()
    try:
        y, m = (int(x) for x in (mes or "").split("-")[:2])
    except ValueError:
        y, m = hoy.year, hoy.month
    return f"{y:04d}-{m:02d}", y, m


@app.get("/api/comunidades")
def list_comunidades(request: Request):
    store, uid = get_store(), _uid(request)
    out = []
    for c in store.list_user_communities(uid):
        item = _com_public(c)
        item["equipos"] = len(store.list_teams(community_id=c["id"]))
        out.append(item)
    return out


@app.post("/api/comunidades")
def create_comunidad(body: ComunidadIn, request: Request):
    c = get_store().create_community(body.nombre, body.lugar, _uid(request))
    return _com_public({**c, "rol": "coordinador"})


@app.post("/api/comunidades/unirse")
def unirse_comunidad(body: UnirseIn, request: Request):
    uid = _uid(request)
    ip = request.client.host if request.client else "?"
    if auth.too_many_attempts(f"join:{ip}:{uid}", limit=12):
        raise HTTPException(429, "Demasiados intentos. Probá de nuevo en unos minutos.")
    store = get_store()
    c = store.get_community_by_code(body.codigo)
    if not c:
        raise HTTPException(404, "No hay ninguna comunidad con ese código. Revisalo con tu coordinador.")
    rol = _community_rol(c["id"], uid)
    if not rol:
        store.set_community_member(c["id"], uid, "responsable")
        rol = "responsable"
    return _com_public({**c, "rol": rol})


@app.get("/api/comunidades/{cid}")
def get_comunidad(cid: str, request: Request, mes: Optional[str] = None):
    """Comunidad con sus equipos por etapa y la planificación del mes."""
    from .assistant import parse_etapa
    store, uid = get_store(), _uid(request)
    com = _com_or_404(cid, request)
    coord = com["rol"] == "coordinador"
    miembros = store.list_community_members(cid)
    teams = _annotate_teams(store.list_teams(community_id=cid), uid)
    mes_txt, y, m = _mes_rango(mes)
    encs = store.list_encuentros(team_ids=[t["id"] for t in teams], limit=1000)
    from datetime import date as _d
    ref = _d(y, m, 15)
    sug_cache = {}
    equipos = []
    for t in teams:
        etapa = parse_etapa((t.get("perfil") or {}).get("etapa"))
        mios = [e for e in encs if e.get("team_id") == t["id"]]
        del_mes = [e for e in mios if (e.get("fecha") or "")[:7] == mes_txt]
        if etapa not in sug_cache:
            s = programas.sugerencias(etapa, ref) if etapa else {}
            sug_cache[etapa] = [f["titulo"] for f in s.get("fichas", [])] if s.get("disponible") else []
        soy = any(r["user_id"] == uid for r in t["responsables"])
        equipos.append({
            "id": t["id"], "nombre": t["nombre"], "etapa": etapa,
            "edades": (t.get("perfil") or {}).get("edades", ""),
            "cantidad": (t.get("perfil") or {}).get("cantidad_chicos", ""),
            "responsables": t["responsables"],
            "acceso": "responsable" if soy else ("coordinador" if coord else None),
            "encuentros_mes": [{**{k: e.get(k) for k in ("id", "titulo", "fecha", "estado", "tema")},
                                "puntuacion": (e.get("feedback") or {}).get("puntuacion"),
                                "asistentes": (e.get("feedback") or {}).get("asistentes"),
                                "falta_feedback": e.get("estado") == "realizado" and not e.get("feedback")}
                               for e in del_mes],
            "ultimo": next((e.get("fecha") for e in mios if e.get("fecha")), None),
            "total_encuentros": len(mios),
            "programa_mes": sug_cache[etapa],
        })
    resumen = {
        "equipos": len(equipos), "miembros": len(miembros),
        "con_plan": sum(1 for e in equipos if e["encuentros_mes"]),
        "sin_responsable": sum(1 for e in equipos if not e["responsables"]),
        "encuentros_mes": sum(len(e["encuentros_mes"]) for e in equipos),
        "realizados_mes": sum(1 for e in equipos for x in e["encuentros_mes"] if x["estado"] == "realizado"),
        "falta_feedback": sum(1 for e in equipos for x in e["encuentros_mes"] if x["falta_feedback"]),
    }
    notas = [x["puntuacion"] for e in equipos for x in e["encuentros_mes"] if x.get("puntuacion")]
    resumen["promedio"] = round(sum(notas) / len(notas), 1) if notas else None
    return {**_com_public(com), "mes": mes_txt, "resumen": resumen, "equipos": equipos,
            "miembros": [{"user_id": x["user_id"], "nombre": x["nombre"], "rol": x["rol"],
                          **({"email": x["email"]} if coord else {})} for x in miembros]}


@app.put("/api/comunidades/{cid}")
def update_comunidad(cid: str, body: ComunidadUpdate, request: Request):
    _com_or_404(cid, request, coord=True)
    c = get_store().update_community(cid, nombre=body.nombre, lugar=body.lugar)
    return _com_public({**c, "rol": "coordinador"})


@app.post("/api/comunidades/{cid}/codigo")
def regenerar_codigo(cid: str, request: Request):
    from .memory import nuevo_codigo
    _com_or_404(cid, request, coord=True)
    c = get_store().update_community(cid, codigo=nuevo_codigo())
    return _com_public({**c, "rol": "coordinador"})


@app.delete("/api/comunidades/{cid}")
def delete_comunidad(cid: str, request: Request):
    _com_or_404(cid, request, coord=True)
    get_store().delete_community(cid)
    return {"ok": True}


def _coordinadores(cid: str) -> set:
    return {m["user_id"] for m in get_store().list_community_members(cid) if m["rol"] == "coordinador"}


@app.put("/api/comunidades/{cid}/miembros/{user_id}")
def update_miembro(cid: str, user_id: str, body: MiembroUpdate, request: Request):
    _com_or_404(cid, request, coord=True)
    if not _community_rol(cid, user_id):
        raise HTTPException(404, "Esa persona no es miembro de la comunidad")
    if body.rol not in ("coordinador", "responsable"):
        raise HTTPException(400, "Rol inválido")
    if body.rol == "responsable" and _coordinadores(cid) == {user_id}:
        raise HTTPException(400, "La comunidad tiene que tener al menos un coordinador")
    get_store().set_community_member(cid, user_id, body.rol)
    return {"ok": True}


@app.delete("/api/comunidades/{cid}/miembros/{user_id}")
def remove_miembro(cid: str, user_id: str, request: Request):
    """El coordinador puede quitar a alguien; cualquiera puede salir de la comunidad."""
    uid = _uid(request)
    _com_or_404(cid, request, coord=(user_id != uid))
    if _coordinadores(cid) == {user_id}:
        raise HTTPException(400, "Sos el único coordinador: nombrá a otra persona antes de salir")
    get_store().remove_community_member(cid, user_id)
    return {"ok": True}


@app.post("/api/comunidades/{cid}/equipos")
def create_equipo_comunidad(cid: str, body: EquipoComunidadIn, request: Request):
    store, uid = get_store(), _uid(request)
    com = _com_or_404(cid, request)
    if com["rol"] == "coordinador":
        responsables = _check_responsables(cid, body.responsables)
    else:
        responsables = [uid]  # un responsable crea su propio equipo dentro de la comunidad
    perfil = {k: v for k, v in {"etapa": f"Etapa {body.etapa}" if body.etapa else "", "edades": body.edades}.items() if v}
    if body.etapa and not perfil.get("edades"):
        info = programas.etapa_info(body.etapa)
        if info:
            perfil["edades"] = info.get("edades", "")
    t = store.create_team(body.nombre, perfil, True, user_id=uid)
    store.update_team(t["id"], community_id=cid)
    store.set_team_members(t["id"], responsables)
    return _annotate_teams([store.get_team(t["id"])], uid)[0]


@app.put("/api/comunidades/{cid}/equipos/{tid}")
def update_equipo_comunidad(cid: str, tid: str, body: EquipoComunidadUpdate, request: Request):
    store, uid = get_store(), _uid(request)
    _com_or_404(cid, request, coord=True)
    t = store.get_team(tid)
    if not t or t.get("community_id") != cid:
        raise HTTPException(404, "Equipo no encontrado")
    perfil = None
    if body.etapa is not None:
        perfil = {**(t.get("perfil") or {}), "etapa": f"Etapa {body.etapa}"}
    if body.nombre is not None or perfil is not None:
        store.update_team(tid, nombre=body.nombre, perfil=perfil)
    if body.responsables is not None:
        store.set_team_members(tid, _check_responsables(cid, body.responsables))
    return _annotate_teams([store.get_team(tid)], uid)[0]


@app.post("/api/teams/{team_id}/comunidad")
def mover_equipo(team_id: str, body: MoverEquipoIn, request: Request):
    """Lleva un equipo personal a una comunidad; quien lo usaba queda como responsable."""
    store, uid = get_store(), _uid(request)
    t = _team_or_404(team_id, request)
    _com_or_404(body.community_id, request)
    if t.get("community_id") and t["community_id"] != body.community_id:
        raise HTTPException(400, "Este equipo ya pertenece a otra comunidad")
    store.add_team_member(team_id, uid)
    store.update_team(team_id, community_id=body.community_id)
    return _annotate_teams([store.get_team(team_id)], uid)[0]


# ------------------------------------------------------------------ chat entre responsables
# Canales: "com-<id>" (todos los miembros de la comunidad) y "eq-<id>" (los
# responsables de un equipo). La coordinación no ve el chat de un equipo, que
# puede tener información de los adolescentes.
class MensajeIn(BaseModel):
    texto: str = Field(..., min_length=1, max_length=2000)


def _canal(tipo: str, cid: str, request: Request) -> dict:
    uid = _uid(request)
    store = get_store()
    if tipo == "comunidad":
        com = store.get_community(cid)
        rol = _community_rol(cid, uid) if com else None
        if rol:
            return {"canal": f"com-{cid}", "tipo": "comunidad", "id": cid, "nombre": com["nombre"],
                    "subtitulo": "Toda la comunidad", "rol": rol}
    elif tipo == "equipo":
        t = store.get_team(cid)
        if t and _team_access(t, uid) == "responsable":
            com = store.get_community(t["community_id"]) if t.get("community_id") else None
            return {"canal": f"eq-{cid}", "tipo": "equipo", "id": cid, "nombre": t["nombre"],
                    "subtitulo": (com or {}).get("nombre") or "Equipo", "rol": "responsable"}
    raise HTTPException(404, "Chat no encontrado")


def _mis_canales(uid: str) -> list:
    store = get_store()
    canales = [{"canal": f"com-{c['id']}", "tipo": "comunidad", "id": c["id"], "nombre": c["nombre"],
                "subtitulo": "Toda la comunidad"} for c in store.list_user_communities(uid)]
    for t in _my_teams(uid):
        # chat de equipo: cuando está en una comunidad o tiene más de un responsable
        if t.get("community_id") or len(t.get("responsables") or []) > 1:
            canales.append({"canal": f"eq-{t['id']}", "tipo": "equipo", "id": t["id"], "nombre": t["nombre"],
                            "subtitulo": (t.get("comunidad") or {}).get("nombre") or "Equipo",
                            "responsables": [r["nombre"] for r in t.get("responsables") or []]})
    return canales


def _msg_public(m: dict, uid: str) -> dict:
    return {**{k: m.get(k) for k in ("id", "user_id", "nombre", "texto", "created_at")}, "mio": m.get("user_id") == uid}


@app.get("/api/chats")
def list_chats(request: Request):
    uid = _uid(request)
    canales = _mis_canales(uid)
    resumen = get_store().chat_summary(uid, [c["canal"] for c in canales])
    for c in canales:
        r = resumen.get(c["canal"]) or {}
        c["no_leidos"] = r.get("no_leidos", 0)
        c["ultimo"] = _msg_public(r["ultimo"], uid) if r.get("ultimo") else None
    canales.sort(key=lambda c: (c["ultimo"] or {}).get("created_at") or "", reverse=True)
    return {"canales": canales, "no_leidos": sum(c["no_leidos"] for c in canales)}


@app.get("/api/chats/{tipo}/{cid}/mensajes")
def list_mensajes(tipo: str, cid: str, request: Request, after: Optional[str] = None,
                  before: Optional[str] = None, leer: bool = True):
    uid = _uid(request)
    canal = _canal(tipo, cid, request)
    store = get_store()
    msgs = store.list_chat_messages(canal["canal"], after=after, before=before, limit=60 if not after else 200)
    if leer and msgs and not before:
        store.set_chat_read(uid, canal["canal"], msgs[-1]["created_at"])
    return {**canal, "mensajes": [_msg_public(m, uid) for m in msgs]}


@app.post("/api/chats/{tipo}/{cid}/mensajes")
def enviar_mensaje(tipo: str, cid: str, body: MensajeIn, request: Request):
    uid = _uid(request)
    canal = _canal(tipo, cid, request)
    texto = body.texto.strip()
    if not texto:
        raise HTTPException(400, "El mensaje está vacío")
    if auth.too_many_attempts(f"chat:{uid}", limit=40, window=60):
        raise HTTPException(429, "Estás mandando muchos mensajes seguidos. Esperá un momento.")
    m = get_store().add_chat_message(canal["canal"], uid, texto)
    get_store().set_chat_read(uid, canal["canal"], m["created_at"])
    return _msg_public(m, uid)


@app.delete("/api/chats/mensajes/{mid}")
def borrar_mensaje(mid: str, request: Request):
    """Cada uno borra sus mensajes; la coordinación puede borrar mensajes del canal de la comunidad."""
    uid = _uid(request)
    store = get_store()
    m = store.get_chat_message(mid)
    if not m:
        raise HTTPException(404, "Mensaje no encontrado")
    tipo, _, cid = m["canal"].partition("-")
    canal = _canal("comunidad" if tipo == "com" else "equipo", cid, request)
    if m.get("user_id") != uid and not (canal["tipo"] == "comunidad" and canal.get("rol") == "coordinador"):
        raise HTTPException(403, "Solo podés borrar tus propios mensajes")
    store.delete_chat_message(mid)
    return {"ok": True}


# ------------------------------------------------------------------ frontend
@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/favicon.ico")
def favicon():
    return FileResponse(WEB_DIR / "favicon.svg", media_type="image/svg+xml")
