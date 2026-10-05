"""
Memoria persistente (SQLite local o Supabase). Datos por RESPONSABLE:

  0. Cuentas                 → tabla `users` (cada responsable ve solo lo suyo)
  4. Encuentros preparados   → tabla `encuentros` (etapa, tema, fichas, grupo,
                               propuesta, observaciones…)

y tres niveles de memoria:

  1. Memoria del equipo      → tabla `teams` (perfil) + tabla `memories`
                               (hechos duraderos: editables y borrables)
  2. Historial               → tablas `conversations` + `messages`
  3. Información temporal     → `conversations.notas`: resumen vivo de UNA
     de una conversación        conversación; se borra con ella.

Un solo archivo (data/memoria.db). Para desplegar, montá DB_PATH en un
volumen persistente.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import settings

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS teams (
    id          TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    perfil      TEXT NOT NULL DEFAULT '{}',
    auto_memoria INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id         TEXT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    texto           TEXT NOT NULL,
    categoria       TEXT NOT NULL DEFAULT 'general',
    origen          TEXT NOT NULL DEFAULT 'manual',
    conversation_id TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memories_team ON memories(team_id);
CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY,
    team_id     TEXT REFERENCES teams(id) ON DELETE CASCADE,
    titulo      TEXT NOT NULL DEFAULT 'Nueva conversación',
    notas       TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conv_team ON conversations(team_id, updated_at);
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user','assistant')),
    content         TEXT NOT NULL,
    sources         TEXT NOT NULL DEFAULT '[]',
    meta            TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, id);
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    nombre        TEXT NOT NULL DEFAULT '',
    rol           TEXT NOT NULL DEFAULT 'Responsable de equipo',
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS encuentros (
    id              TEXT PRIMARY KEY,
    user_id         TEXT,
    team_id         TEXT REFERENCES teams(id) ON DELETE SET NULL,
    titulo          TEXT NOT NULL DEFAULT 'Encuentro',
    fecha           TEXT,
    etapa           INTEGER,
    tema            TEXT NOT NULL DEFAULT '',
    origen_tema     TEXT NOT NULL DEFAULT 'otro',
    periodo         TEXT NOT NULL DEFAULT '',
    fichas          TEXT NOT NULL DEFAULT '[]',
    cantidad        INTEGER,
    composicion     TEXT NOT NULL DEFAULT '',
    edades          TEXT NOT NULL DEFAULT '',
    duracion        TEXT NOT NULL DEFAULT '',
    propuesta       TEXT NOT NULL DEFAULT '',
    observaciones   TEXT NOT NULL DEFAULT '',
    estado          TEXT NOT NULL DEFAULT 'borrador',
    conversation_id TEXT,
    meta            TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_enc_user ON encuentros(user_id, fecha);
CREATE INDEX IF NOT EXISTS idx_enc_team ON encuentros(team_id, fecha);
"""

# Columnas agregadas después de la primera versión (migración segura, aditiva)
MIGRATIONS = [("teams", "user_id", "TEXT"), ("conversations", "user_id", "TEXT")]

ENCUENTRO_FIELDS = ["titulo", "fecha", "etapa", "tema", "origen_tema", "periodo", "fichas", "cantidad",
                    "composicion", "edades", "duracion", "propuesta", "observaciones", "estado",
                    "conversation_id", "meta", "team_id"]
ESTADOS = ["borrador", "planificado", "realizado"]

CATEGORIAS = ["equipo", "adolescente", "proceso", "preferencia", "pendiente", "general"]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class MemoryStore:
    def __init__(self, path=None):
        self.path = str(path or settings.db_path)
        if self.path != ":memory:":
            from pathlib import Path
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)
            for table, col, typ in MIGRATIONS:
                cols = {r["name"] for r in c.execute(f"PRAGMA table_info({table})")}
                if col not in cols:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ---------------------------------------------------------- equipos
    def _team(self, row) -> Dict[str, Any]:
        d = dict(row)
        d["perfil"] = json.loads(d["perfil"] or "{}")
        d["auto_memoria"] = bool(d["auto_memoria"])
        return d

    def list_teams(self, user_id: Optional[str] = None) -> List[Dict]:
        with self._conn() as c:
            if user_id:
                rows = c.execute("SELECT * FROM teams WHERE user_id=? ORDER BY nombre COLLATE NOCASE", (user_id,))
            else:
                rows = c.execute("SELECT * FROM teams ORDER BY nombre COLLATE NOCASE")
            return [self._team(r) for r in rows]

    def get_team(self, team_id: str) -> Optional[Dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM teams WHERE id=?", (team_id,)).fetchone()
            return self._team(r) if r else None

    def create_team(self, nombre: str, perfil: Optional[dict] = None, auto_memoria: bool = True,
                    user_id: Optional[str] = None) -> Dict:
        tid = uuid.uuid4().hex[:12]
        now = _now()
        with self._conn() as c:
            c.execute("INSERT INTO teams (id, nombre, perfil, auto_memoria, created_at, updated_at, user_id) "
                      "VALUES (?,?,?,?,?,?,?)",
                      (tid, nombre.strip() or "Mi equipo", json.dumps(perfil or {}, ensure_ascii=False),
                       int(auto_memoria), now, now, user_id))
        return self.get_team(tid)

    def update_team(self, team_id: str, *, nombre=None, perfil=None, auto_memoria=None) -> Optional[Dict]:
        team = self.get_team(team_id)
        if not team:
            return None
        with self._conn() as c:
            c.execute("UPDATE teams SET nombre=?, perfil=?, auto_memoria=?, updated_at=? WHERE id=?",
                      ((nombre or team["nombre"]).strip(),
                       json.dumps(perfil if perfil is not None else team["perfil"], ensure_ascii=False),
                       int(team["auto_memoria"] if auto_memoria is None else auto_memoria), _now(), team_id))
        return self.get_team(team_id)

    def delete_team(self, team_id: str) -> bool:
        with self._conn() as c:
            return c.execute("DELETE FROM teams WHERE id=?", (team_id,)).rowcount > 0

    # ---------------------------------------------------------- memoria
    def list_memories(self, team_id: str) -> List[Dict]:
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT * FROM memories WHERE team_id=? ORDER BY categoria, id", (team_id,))]

    def add_memory(self, team_id: str, texto: str, categoria: str = "general", origen: str = "manual",
                   conversation_id: Optional[str] = None) -> Dict:
        categoria = categoria if categoria in CATEGORIAS else "general"
        now = _now()
        with self._conn() as c:
            cur = c.execute("INSERT INTO memories (team_id, texto, categoria, origen, conversation_id, created_at, updated_at)"
                            " VALUES (?,?,?,?,?,?,?)",
                            (team_id, texto.strip(), categoria, origen, conversation_id, now, now))
            return dict(c.execute("SELECT * FROM memories WHERE id=?", (cur.lastrowid,)).fetchone())

    def update_memory(self, memory_id: int, *, texto=None, categoria=None, team_id=None) -> Optional[Dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone()
            if not r or (team_id and r["team_id"] != team_id):
                return None
            cat = categoria if categoria in CATEGORIAS else r["categoria"]
            c.execute("UPDATE memories SET texto=?, categoria=?, updated_at=? WHERE id=?",
                      ((texto or r["texto"]).strip(), cat, _now(), memory_id))
            return dict(c.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone())

    def delete_memory(self, memory_id: int, team_id: Optional[str] = None) -> bool:
        with self._conn() as c:
            if team_id:
                return c.execute("DELETE FROM memories WHERE id=? AND team_id=?", (memory_id, team_id)).rowcount > 0
            return c.execute("DELETE FROM memories WHERE id=?", (memory_id,)).rowcount > 0

    def clear_memories(self, team_id: str) -> int:
        with self._conn() as c:
            return c.execute("DELETE FROM memories WHERE team_id=?", (team_id,)).rowcount

    # ---------------------------------------------------------- conversaciones
    def create_conversation(self, team_id: Optional[str], titulo: str = "Nueva conversación",
                            user_id: Optional[str] = None) -> Dict:
        cid = uuid.uuid4().hex
        now = _now()
        with self._conn() as c:
            c.execute("INSERT INTO conversations (id, team_id, titulo, notas, created_at, updated_at, user_id) "
                      "VALUES (?,?,?,?,?,?,?)", (cid, team_id, titulo, "", now, now, user_id))
        return self.get_conversation(cid)

    def get_conversation(self, cid: str) -> Optional[Dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM conversations WHERE id=?", (cid,)).fetchone()
            return dict(r) if r else None

    def list_conversations(self, team_id: Optional[str] = None, limit: int = 100,
                           user_id: Optional[str] = None) -> List[Dict]:
        q = ("SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.conversation_id=c.id) AS mensajes "
             "FROM conversations c WHERE 1=1 ")
        args: list = []
        if team_id:
            q += "AND c.team_id=? "
            args.append(team_id)
        if user_id:
            q += "AND c.user_id=? "
            args.append(user_id)
        q += "ORDER BY c.updated_at DESC LIMIT ?"
        args.append(limit)
        with self._conn() as c:
            return [dict(r) for r in c.execute(q, args)]

    def update_conversation(self, cid: str, *, titulo=None, notas=None, team_id=...) -> Optional[Dict]:
        conv = self.get_conversation(cid)
        if not conv:
            return None
        with self._conn() as c:
            c.execute("UPDATE conversations SET titulo=?, notas=?, team_id=?, updated_at=? WHERE id=?",
                      (titulo if titulo is not None else conv["titulo"],
                       notas if notas is not None else conv["notas"],
                       conv["team_id"] if team_id is ... else team_id, _now(), cid))
        return self.get_conversation(cid)

    def delete_conversation(self, cid: str) -> bool:
        with self._conn() as c:
            return c.execute("DELETE FROM conversations WHERE id=?", (cid,)).rowcount > 0

    def add_message(self, cid: str, role: str, content: str, sources=None, meta=None) -> Dict:
        now = _now()
        with self._conn() as c:
            cur = c.execute("INSERT INTO messages (conversation_id, role, content, sources, meta, created_at)"
                            " VALUES (?,?,?,?,?,?)",
                            (cid, role, content, json.dumps(sources or [], ensure_ascii=False),
                             json.dumps(meta or {}, ensure_ascii=False), now))
            c.execute("UPDATE conversations SET updated_at=? WHERE id=?", (now, cid))
            return {"id": cur.lastrowid, "role": role, "content": content,
                    "sources": sources or [], "meta": meta or {}, "created_at": now}

    def get_messages(self, cid: str, limit: Optional[int] = None) -> List[Dict]:
        with self._conn() as c:
            if limit:
                rows = c.execute("SELECT * FROM (SELECT * FROM messages WHERE conversation_id=? "
                                 "ORDER BY id DESC LIMIT ?) ORDER BY id", (cid, limit)).fetchall()
            else:
                rows = c.execute("SELECT * FROM messages WHERE conversation_id=? ORDER BY id", (cid,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["sources"] = json.loads(d["sources"] or "[]")
            d["meta"] = json.loads(d["meta"] or "{}")
            out.append(d)
        return out

    # ---------------------------------------------------------- cuentas
    def create_user(self, email: str, nombre: str, password_hash: str, rol: str = "") -> Dict:
        uid = uuid.uuid4().hex
        now = _now()
        with self._conn() as c:
            c.execute("INSERT INTO users (id, email, nombre, rol, password_hash, created_at, updated_at) "
                      "VALUES (?,?,?,?,?,?,?)",
                      (uid, email.strip().lower(), nombre.strip(), rol or "Responsable de equipo",
                       password_hash, now, now))
        return self.get_user(uid)

    def get_user(self, user_id: str) -> Optional[Dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            return dict(r) if r else None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
            return dict(r) if r else None

    def update_user(self, user_id: str, **fields) -> Optional[Dict]:
        allowed = {k: v for k, v in fields.items() if k in ("nombre", "rol", "password_hash") and v is not None}
        if allowed:
            sets = ", ".join(f"{k}=?" for k in allowed)
            with self._conn() as c:
                c.execute(f"UPDATE users SET {sets}, updated_at=? WHERE id=?",
                          (*allowed.values(), _now(), user_id))
        return self.get_user(user_id)

    def count_users(self) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def claim_orphans(self, user_id: str) -> Dict[str, int]:
        """Asigna al responsable los datos creados antes de que existieran cuentas."""
        with self._conn() as c:
            t = c.execute("UPDATE teams SET user_id=? WHERE user_id IS NULL", (user_id,)).rowcount
            v = c.execute("UPDATE conversations SET user_id=? WHERE user_id IS NULL", (user_id,)).rowcount
            e = c.execute("UPDATE encuentros SET user_id=? WHERE user_id IS NULL", (user_id,)).rowcount
        return {"equipos": t, "conversaciones": v, "encuentros": e}

    # ---------------------------------------------------------- encuentros
    def _enc(self, row) -> Dict[str, Any]:
        d = dict(row)
        d["fichas"] = json.loads(d.get("fichas") or "[]")
        d["meta"] = json.loads(d.get("meta") or "{}")
        return d

    def create_encuentro(self, user_id: Optional[str], data: Dict[str, Any]) -> Dict:
        eid = uuid.uuid4().hex
        now = _now()
        row = _encuentro_row(data)
        cols = ["id", "user_id", "created_at", "updated_at", *row.keys()]
        vals = [eid, user_id, now, now, *[json.dumps(v, ensure_ascii=False) if k in ("fichas", "meta") else v
                                         for k, v in row.items()]]
        with self._conn() as c:
            c.execute(f"INSERT INTO encuentros ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", vals)
        return self.get_encuentro(eid)

    def get_encuentro(self, eid: str) -> Optional[Dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM encuentros WHERE id=?", (eid,)).fetchone()
            return self._enc(r) if r else None

    def list_encuentros(self, user_id: Optional[str] = None, team_id: Optional[str] = None,
                        limit: int = 200) -> List[Dict]:
        q, args = "SELECT * FROM encuentros WHERE 1=1 ", []
        if user_id:
            q += "AND user_id=? "
            args.append(user_id)
        if team_id:
            q += "AND team_id=? "
            args.append(team_id)
        q += "ORDER BY COALESCE(fecha, created_at) DESC, created_at DESC LIMIT ?"
        args.append(limit)
        with self._conn() as c:
            return [self._enc(r) for r in c.execute(q, args)]

    def update_encuentro(self, eid: str, data: Dict[str, Any]) -> Optional[Dict]:
        row = _encuentro_row(data, partial=True)
        if row:
            sets = ", ".join(f"{k}=?" for k in row)
            vals = [json.dumps(v, ensure_ascii=False) if k in ("fichas", "meta") else v for k, v in row.items()]
            with self._conn() as c:
                c.execute(f"UPDATE encuentros SET {sets}, updated_at=? WHERE id=?", (*vals, _now(), eid))
        return self.get_encuentro(eid)

    def delete_encuentro(self, eid: str) -> bool:
        with self._conn() as c:
            return c.execute("DELETE FROM encuentros WHERE id=?", (eid,)).rowcount > 0

    def export_team(self, team_id: str) -> Dict:
        return {"equipo": self.get_team(team_id), "memoria": self.list_memories(team_id),
                "encuentros": self.list_encuentros(team_id=team_id, limit=10000),
                "conversaciones": [dict(c, mensajes=self.get_messages(c["id"]))
                                   for c in self.list_conversations(team_id, limit=10000)]}


def _encuentro_row(data: Dict[str, Any], partial: bool = False) -> Dict[str, Any]:
    """Normaliza los campos de un encuentro (tipos y valores permitidos)."""
    row: Dict[str, Any] = {}
    for k in ENCUENTRO_FIELDS:
        if k not in data:
            continue
        v = data[k]
        if k in ("etapa", "cantidad"):
            try:
                v = int(v) if v not in (None, "") else None
            except (TypeError, ValueError):
                v = None
        elif k in ("fichas",):
            v = [{"doc_id": str(f.get("doc_id", "")), "titulo": str(f.get("titulo", ""))[:200]}
                 for f in (v or []) if isinstance(f, dict)]
        elif k == "meta":
            v = v if isinstance(v, dict) else {}
        elif k == "estado":
            v = v if v in ESTADOS else "borrador"
        elif k == "origen_tema":
            v = v if v in ("programa", "otro") else "otro"
        elif k in ("team_id", "conversation_id", "fecha"):
            v = (str(v).strip() or None) if v is not None else None
        else:
            v = "" if v is None else str(v)
        row[k] = v
    if not partial:
        row.setdefault("titulo", "Encuentro")
    return row


class SupabaseMemoryStore:
    """Misma interfaz que MemoryStore, guardando todo en Supabase (Postgres)
    mediante su API REST. Es la opción para Vercel, donde el disco se borra.

    Seguridad: las tablas tienen RLS y solo aceptan pedidos que traen el
    header x-ecyd-key con el secreto del servidor (ECYD_DB_SECRET). La clave
    publicable de Supabase sola no da acceso a nada. Nada de esto llega al
    navegador.
    """

    def __init__(self, url=None, key=None, secret=None):
        import httpx
        self.base = (url or settings.supabase_url).rstrip("/") + "/rest/v1"
        headers = {"apikey": key or settings.supabase_key, "x-ecyd-key": secret or settings.db_secret,
                   "Content-Type": "application/json"}
        k = key or settings.supabase_key
        if k.startswith("eyJ"):  # clave anon legacy (JWT)
            headers["Authorization"] = f"Bearer {k}"
        self.http = httpx.Client(base_url=self.base, headers=headers, timeout=20)

    # ---------------------------------------------------------- HTTP
    def _req(self, method, path, *, params=None, json_body=None, returning=False):
        headers = {"Prefer": "return=representation"} if returning else {}
        for attempt in range(3):
            try:
                r = self.http.request(method, path, params=params, json=json_body, headers=headers)
                break
            except Exception:  # noqa: BLE001
                if attempt == 2:
                    raise
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase {method} {path}: {r.status_code} {r.text[:300]}")
        return r.json() if r.content else []

    def _one(self, rows):
        return rows[0] if rows else None

    # ---------------------------------------------------------- equipos
    def list_teams(self, user_id=None):
        params = {"select": "*", "order": "nombre.asc"}
        if user_id:
            params["user_id"] = f"eq.{user_id}"
        return self._req("GET", "/teams", params=params)

    def get_team(self, team_id):
        return self._one(self._req("GET", "/teams", params={"id": f"eq.{team_id}", "select": "*"}))

    def create_team(self, nombre, perfil=None, auto_memoria=True, user_id=None):
        now = _now()
        row = {"id": uuid.uuid4().hex[:12], "nombre": nombre.strip() or "Mi equipo", "perfil": perfil or {},
               "auto_memoria": bool(auto_memoria), "created_at": now, "updated_at": now, "user_id": user_id}
        return self._one(self._req("POST", "/teams", json_body=row, returning=True))

    def update_team(self, team_id, *, nombre=None, perfil=None, auto_memoria=None):
        patch = {"updated_at": _now()}
        if nombre:
            patch["nombre"] = nombre.strip()
        if perfil is not None:
            patch["perfil"] = perfil
        if auto_memoria is not None:
            patch["auto_memoria"] = bool(auto_memoria)
        return self._one(self._req("PATCH", "/teams", params={"id": f"eq.{team_id}"}, json_body=patch, returning=True))

    def delete_team(self, team_id):
        return bool(self._req("DELETE", "/teams", params={"id": f"eq.{team_id}"}, returning=True))

    # ---------------------------------------------------------- memoria
    def list_memories(self, team_id):
        return self._req("GET", "/memories", params={"team_id": f"eq.{team_id}", "select": "*",
                                                     "order": "categoria.asc,id.asc"})

    def add_memory(self, team_id, texto, categoria="general", origen="manual", conversation_id=None):
        categoria = categoria if categoria in CATEGORIAS else "general"
        now = _now()
        row = {"team_id": team_id, "texto": texto.strip(), "categoria": categoria, "origen": origen,
               "conversation_id": conversation_id, "created_at": now, "updated_at": now}
        return self._one(self._req("POST", "/memories", json_body=row, returning=True))

    def update_memory(self, memory_id, *, texto=None, categoria=None, team_id=None):
        params = {"id": f"eq.{int(memory_id)}"}
        if team_id:
            params["team_id"] = f"eq.{team_id}"
        patch = {"updated_at": _now()}
        if texto:
            patch["texto"] = texto.strip()
        if categoria in CATEGORIAS:
            patch["categoria"] = categoria
        return self._one(self._req("PATCH", "/memories", params=params, json_body=patch, returning=True))

    def delete_memory(self, memory_id, team_id=None):
        params = {"id": f"eq.{int(memory_id)}"}
        if team_id:
            params["team_id"] = f"eq.{team_id}"
        return bool(self._req("DELETE", "/memories", params=params, returning=True))

    def clear_memories(self, team_id):
        return len(self._req("DELETE", "/memories", params={"team_id": f"eq.{team_id}"}, returning=True))

    # ---------------------------------------------------------- conversaciones
    def create_conversation(self, team_id, titulo="Nueva conversación", user_id=None):
        now = _now()
        row = {"id": uuid.uuid4().hex, "team_id": team_id, "titulo": titulo, "notas": "",
               "created_at": now, "updated_at": now, "user_id": user_id}
        return self._one(self._req("POST", "/conversations", json_body=row, returning=True))

    def get_conversation(self, cid):
        return self._one(self._req("GET", "/conversations", params={"id": f"eq.{cid}", "select": "*"}))

    def list_conversations(self, team_id=None, limit=100, user_id=None):
        params = {"select": "*,messages(count)", "order": "updated_at.desc", "limit": str(limit)}
        if team_id:
            params["team_id"] = f"eq.{team_id}"
        if user_id:
            params["user_id"] = f"eq.{user_id}"
        rows = self._req("GET", "/conversations", params=params)
        for r in rows:
            m = r.pop("messages", None) or [{}]
            r["mensajes"] = (m[0] or {}).get("count", 0)
        return rows

    def update_conversation(self, cid, *, titulo=None, notas=None, team_id=...):
        patch = {"updated_at": _now()}
        if titulo is not None:
            patch["titulo"] = titulo
        if notas is not None:
            patch["notas"] = notas
        if team_id is not ...:
            patch["team_id"] = team_id
        return self._one(self._req("PATCH", "/conversations", params={"id": f"eq.{cid}"},
                                   json_body=patch, returning=True))

    def delete_conversation(self, cid):
        return bool(self._req("DELETE", "/conversations", params={"id": f"eq.{cid}"}, returning=True))

    def add_message(self, cid, role, content, sources=None, meta=None):
        now = _now()
        row = {"conversation_id": cid, "role": role, "content": content, "sources": sources or [],
               "meta": meta or {}, "created_at": now}
        saved = self._one(self._req("POST", "/messages", json_body=row, returning=True))
        self._req("PATCH", "/conversations", params={"id": f"eq.{cid}"}, json_body={"updated_at": now})
        return saved

    def get_messages(self, cid, limit=None):
        params = {"conversation_id": f"eq.{cid}", "select": "*", "order": "id.desc" if limit else "id.asc"}
        if limit:
            params["limit"] = str(limit)
        rows = self._req("GET", "/messages", params=params)
        return list(reversed(rows)) if limit else rows

    # ---------------------------------------------------------- cuentas
    def create_user(self, email, nombre, password_hash, rol=""):
        now = _now()
        row = {"id": uuid.uuid4().hex, "email": email.strip().lower(), "nombre": nombre.strip(),
               "rol": rol or "Responsable de equipo", "password_hash": password_hash,
               "created_at": now, "updated_at": now}
        return self._one(self._req("POST", "/users", json_body=row, returning=True))

    def get_user(self, user_id):
        return self._one(self._req("GET", "/users", params={"id": f"eq.{user_id}", "select": "*"}))

    def get_user_by_email(self, email):
        return self._one(self._req("GET", "/users", params={"email": f"eq.{email.strip().lower()}",
                                                           "select": "*"}))

    def update_user(self, user_id, **fields):
        patch = {k: v for k, v in fields.items() if k in ("nombre", "rol", "password_hash") and v is not None}
        if not patch:
            return self.get_user(user_id)
        patch["updated_at"] = _now()
        return self._one(self._req("PATCH", "/users", params={"id": f"eq.{user_id}"}, json_body=patch,
                                   returning=True))

    def count_users(self):
        return len(self._req("GET", "/users", params={"select": "id", "limit": "1000"}))

    def claim_orphans(self, user_id):
        out = {}
        for table, key in (("teams", "equipos"), ("conversations", "conversaciones"), ("encuentros", "encuentros")):
            rows = self._req("PATCH", f"/{table}", params={"user_id": "is.null"},
                             json_body={"user_id": user_id}, returning=True)
            out[key] = len(rows)
        return out

    # ---------------------------------------------------------- encuentros
    def create_encuentro(self, user_id, data):
        now = _now()
        row = {"id": uuid.uuid4().hex, "user_id": user_id, "created_at": now, "updated_at": now,
               **_encuentro_row(data)}
        return self._one(self._req("POST", "/encuentros", json_body=row, returning=True))

    def get_encuentro(self, eid):
        return self._one(self._req("GET", "/encuentros", params={"id": f"eq.{eid}", "select": "*"}))

    def list_encuentros(self, user_id=None, team_id=None, limit=200):
        params = {"select": "*", "order": "fecha.desc.nullslast,created_at.desc", "limit": str(limit)}
        if user_id:
            params["user_id"] = f"eq.{user_id}"
        if team_id:
            params["team_id"] = f"eq.{team_id}"
        return self._req("GET", "/encuentros", params=params)

    def update_encuentro(self, eid, data):
        patch = _encuentro_row(data, partial=True)
        if not patch:
            return self.get_encuentro(eid)
        patch["updated_at"] = _now()
        return self._one(self._req("PATCH", "/encuentros", params={"id": f"eq.{eid}"}, json_body=patch,
                                   returning=True))

    def delete_encuentro(self, eid):
        return bool(self._req("DELETE", "/encuentros", params={"id": f"eq.{eid}"}, returning=True))

    def export_team(self, team_id):
        return {"equipo": self.get_team(team_id), "memoria": self.list_memories(team_id),
                "encuentros": self.list_encuentros(team_id=team_id, limit=10000),
                "conversaciones": [dict(c, mensajes=self.get_messages(c["id"]))
                                   for c in self.list_conversations(team_id, limit=10000)]}


_store = None


def get_store():
    """Supabase si está configurado (SUPABASE_URL, SUPABASE_KEY, ECYD_DB_SECRET);
    si no, SQLite local en DB_PATH."""
    global _store
    if _store is None:
        if settings.supabase_url and settings.supabase_key and settings.db_secret:
            _store = SupabaseMemoryStore()
        else:
            _store = MemoryStore()
    return _store


def store_kind() -> str:
    return "supabase" if isinstance(get_store(), SupabaseMemoryStore) else "sqlite"
