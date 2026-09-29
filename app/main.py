"""
Servidor web del Asistente ECyD (FastAPI).

    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import prompts
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


def _ensure_rag_loading():
    """Arranca la carga del corpus en segundo plano (una sola vez por instancia)."""
    if _state["loader"] is None:
        t = threading.Thread(target=_load_rag, daemon=True)
        _state["loader"] = t
        t.start()


def _load_rag():
    try:
        r = get_retriever()
        r.warmup()
        _state["rag"] = "listo"
    except Exception as e:  # noqa: BLE001
        log.exception("No se pudo cargar el RAG")
        _state["rag"] = "error"
        _state["rag_error"] = str(e)


@app.on_event("startup")
def startup():
    _ensure_rag_loading()


# ------------------------------------------------------------------ auth
COOKIE = "ecyd_session"


def _secret() -> bytes:
    base = settings.secret_key or ("ecyd:" + settings.app_password)
    return hashlib.sha256(base.encode()).digest()


def _token() -> str:
    return hmac.new(_secret(), b"ecyd-ok", hashlib.sha256).hexdigest()


def _authed(request: Request) -> bool:
    if not settings.app_password:
        return True
    return hmac.compare_digest(request.cookies.get(COOKIE, ""), _token())


PUBLIC = {"/", "/api/session", "/api/login", "/api/health", "/favicon.ico"}


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in PUBLIC and not _authed(request):
        return JSONResponse({"detail": "No autorizado"}, status_code=401)
    return await call_next(request)


class LoginIn(BaseModel):
    password: str


@app.get("/api/session")
def session(request: Request):
    return {"auth_required": bool(settings.app_password), "authenticated": _authed(request)}


@app.post("/api/login")
def login(body: LoginIn):
    if not settings.app_password:
        return {"ok": True}
    if not hmac.compare_digest(body.password, settings.app_password):
        raise HTTPException(401, "Contraseña incorrecta")
    resp = JSONResponse({"ok": True})
    resp.set_cookie(COOKIE, _token(), httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return resp


@app.post("/api/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(COOKIE)
    return resp


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
        get_store().list_teams()
        info["memoria_ok"] = True
    except Exception as e:  # noqa: BLE001
        info["memoria_ok"] = False
        info["memoria_error"] = str(e)[:300]
    return info


@app.get("/api/config")
def ui_config():
    portada = next((f"/static/img/{f}" for f in ("portada.jpg", "portada.webp", "portada.png")
                    if (WEB_DIR / "img" / f).exists()), None)
    return {"team_fields": [{"key": k, "label": l} for k, l in prompts.TEAM_FIELDS],
            "categorias": CATEGORIAS, "portada": portada}


@app.get("/api/documents")
def documents():
    return get_retriever().document_list()


# ------------------------------------------------------------------ equipos
class TeamIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    perfil: dict = {}
    auto_memoria: bool = True


class TeamUpdate(BaseModel):
    nombre: Optional[str] = None
    perfil: Optional[dict] = None
    auto_memoria: Optional[bool] = None


def _team_or_404(team_id):
    t = get_store().get_team(team_id)
    if not t:
        raise HTTPException(404, "Equipo no encontrado")
    return t


@app.get("/api/teams")
def list_teams():
    return get_store().list_teams()


@app.post("/api/teams")
def create_team(body: TeamIn):
    perfil = {k: str(v)[:1000] for k, v in body.perfil.items() if v not in (None, "")}
    return get_store().create_team(body.nombre, perfil, body.auto_memoria)


@app.get("/api/teams/{team_id}")
def get_team(team_id: str):
    return _team_or_404(team_id)


@app.put("/api/teams/{team_id}")
def update_team(team_id: str, body: TeamUpdate):
    _team_or_404(team_id)
    perfil = None if body.perfil is None else {k: str(v)[:1000] for k, v in body.perfil.items() if v not in (None, "")}
    return get_store().update_team(team_id, nombre=body.nombre, perfil=perfil, auto_memoria=body.auto_memoria)


@app.delete("/api/teams/{team_id}")
def delete_team(team_id: str):
    if not get_store().delete_team(team_id):
        raise HTTPException(404, "Equipo no encontrado")
    return {"ok": True}


@app.get("/api/teams/{team_id}/export")
def export_team(team_id: str):
    _team_or_404(team_id)
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
def list_memories(team_id: str):
    _team_or_404(team_id)
    return get_store().list_memories(team_id)


@app.post("/api/teams/{team_id}/memories")
def add_memory(team_id: str, body: MemoryIn):
    _team_or_404(team_id)
    return get_store().add_memory(team_id, body.texto, body.categoria, origen="manual")


@app.put("/api/teams/{team_id}/memories/{memory_id}")
def update_memory(team_id: str, memory_id: int, body: MemoryUpdate):
    r = get_store().update_memory(memory_id, texto=body.texto, categoria=body.categoria, team_id=team_id)
    if not r:
        raise HTTPException(404, "Recuerdo no encontrado")
    return r


@app.delete("/api/teams/{team_id}/memories/{memory_id}")
def delete_memory(team_id: str, memory_id: int):
    if not get_store().delete_memory(memory_id, team_id):
        raise HTTPException(404, "Recuerdo no encontrado")
    return {"ok": True}


@app.delete("/api/teams/{team_id}/memories")
def clear_memories(team_id: str):
    _team_or_404(team_id)
    return {"borrados": get_store().clear_memories(team_id)}


# ------------------------------------------------------------------ conversaciones
class ConversationUpdate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=120)
    notas: Optional[str] = Field(None, max_length=3000)


@app.get("/api/conversations")
def list_conversations(team_id: Optional[str] = None):
    return get_store().list_conversations(team_id)


@app.get("/api/conversations/{cid}")
def get_conversation(cid: str):
    s = get_store()
    conv = s.get_conversation(cid)
    if not conv:
        raise HTTPException(404, "Conversación no encontrada")
    return {**conv, "messages": s.get_messages(cid)}


@app.patch("/api/conversations/{cid}")
def patch_conversation(cid: str, body: ConversationUpdate):
    r = get_store().update_conversation(cid, titulo=body.titulo, notas=body.notas)
    if not r:
        raise HTTPException(404, "Conversación no encontrada")
    return r


@app.delete("/api/conversations/{cid}")
def delete_conversation(cid: str):
    if not get_store().delete_conversation(cid):
        raise HTTPException(404, "Conversación no encontrada")
    return {"ok": True}


# ------------------------------------------------------------------ chat
class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    conversation_id: Optional[str] = None
    team_id: Optional[str] = None


@app.post("/api/chat")
def chat(body: ChatIn):
    _ensure_rag_loading()
    if _state["rag"] == "error":
        raise HTTPException(503, f"El corpus no está disponible: {_state['rag_error']}")
    if body.team_id:
        _team_or_404(body.team_id)

    def events():
        try:
            for ev in get_assistant().stream(body.message, body.conversation_id, body.team_id):
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except Exception as e:  # noqa: BLE001
            log.exception("Error en /api/chat")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ------------------------------------------------------------------ frontend
@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/favicon.ico")
def favicon():
    return FileResponse(WEB_DIR / "favicon.svg", media_type="image/svg+xml")
