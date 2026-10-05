"""
Cuentas individuales de responsables.

- Contraseñas con scrypt (sal aleatoria por usuario).
- Sesión en cookie firmada con HMAC (no se guarda nada en el servidor):
  user_id.expira.firma
- Para crear una cuenta hace falta el CÓDIGO DE ACCESO del ECyD
  (REGISTRATION_CODE, o el APP_PASSWORD que ya existía). Así nadie ajeno
  puede registrarse.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from .config import settings

COOKIE = "ecyd_user"
SESSION_DAYS = 30
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_secret_cache: Optional[bytes] = None


def _secret() -> bytes:
    global _secret_cache
    if _secret_cache:
        return _secret_cache
    base = settings.secret_key or settings.db_secret
    if not base:
        # local sin configuración: secreto aleatorio persistido junto a los datos
        path = Path(settings.data_dir) / ".session_secret"
        try:
            base = path.read_text().strip()
        except OSError:
            base = secrets.token_urlsafe(32)
            try:
                path.write_text(base)
            except OSError:
                pass
    _secret_cache = hashlib.sha256(("ecyd-session:" + base).encode()).digest()
    return _secret_cache


def registration_code() -> str:
    return os.getenv("REGISTRATION_CODE", "").strip() or settings.app_password


# ------------------------------------------------------------------ contraseñas
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    n, r, p = 2 ** 14, 8, 1
    dk = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=32)
    return "scrypt${}${}${}${}${}".format(n, r, p, base64.b64encode(salt).decode(), base64.b64encode(dk).decode())


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, dk = stored.split("$")
        if algo != "scrypt":
            return False
        calc = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p),
                              dklen=len(base64.b64decode(dk)))
        return hmac.compare_digest(calc, base64.b64decode(dk))
    except Exception:  # noqa: BLE001
        return False


def validate_new_account(email: str, password: str, nombre: str) -> Optional[str]:
    if not EMAIL_RE.match(email or ""):
        return "Ingresá un email válido."
    if len(password or "") < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    if not (nombre or "").strip():
        return "Ingresá tu nombre."
    return None


# ------------------------------------------------------------------ sesión
def make_token(user_id: str, days: int = SESSION_DAYS) -> str:
    exp = int(time.time()) + days * 86400
    msg = f"{user_id}.{exp}"
    sig = hmac.new(_secret(), msg.encode(), hashlib.sha256).hexdigest()
    return f"{msg}.{sig}"


def read_token(token: str) -> Optional[str]:
    try:
        user_id, exp, sig = (token or "").split(".")
        if int(exp) < time.time():
            return None
        good = hmac.new(_secret(), f"{user_id}.{exp}".encode(), hashlib.sha256).hexdigest()
        return user_id if hmac.compare_digest(sig, good) else None
    except ValueError:
        return None


def public_user(u: Optional[Dict]) -> Optional[Dict]:
    if not u:
        return None
    return {k: u.get(k) for k in ("id", "email", "nombre", "rol", "created_at")}


# ------------------------------------------------------------------ límite de intentos
_attempts: Dict[str, Tuple[int, float]] = {}


def too_many_attempts(key: str, limit: int = 10, window: int = 600) -> bool:
    count, start = _attempts.get(key, (0, time.time()))
    if time.time() - start > window:
        count, start = 0, time.time()
    _attempts[key] = (count + 1, start)
    return count + 1 > limit


def reset_attempts(key: str):
    _attempts.pop(key, None)
