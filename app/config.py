"""Configuración central. Todo se lee de variables de entorno (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    v = _env(name, "")
    if not v:
        return default
    return v.lower() in ("1", "true", "si", "sí", "yes", "on")


@dataclass
class Settings:
    # --- LLM -------------------------------------------------------
    llm_provider: str = field(default_factory=lambda: _env("LLM_PROVIDER", "groq").lower())
    groq_api_key: str = field(default_factory=lambda: _env("GROQ_API_KEY"))
    groq_base_url: str = field(default_factory=lambda: _env("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
    # llama-3.3-70b-versatile fue retirado por Groq (16/08/2026) → gpt-oss-120b
    groq_model: str = field(default_factory=lambda: _env("GROQ_MODEL", "openai/gpt-oss-120b"))
    groq_fallback_model: str = field(default_factory=lambda: _env("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b"))
    groq_small_model: str = field(default_factory=lambda: _env("GROQ_SMALL_MODEL", "openai/gpt-oss-20b"))
    reasoning_effort: str = field(default_factory=lambda: _env("GROQ_REASONING_EFFORT", "medium"))
    gemini_api_key: str = field(default_factory=lambda: _env("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: _env("GEMINI_MODEL", "gemini-3.6-flash"))
    temperature: float = field(default_factory=lambda: _float("LLM_TEMPERATURE", 0.35))
    max_output_tokens: int = field(default_factory=lambda: _int("LLM_MAX_TOKENS", 6000))

    # --- RAG -------------------------------------------------------
    data_dir: Path = field(default_factory=lambda: Path(_env("DATA_DIR", str(BASE_DIR / "data"))))
    embedding_model: str = field(default_factory=lambda: _env("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"))
    # auto | fastembed (ONNX, liviano: el que se usa en Vercel) | sentence-transformers (PyTorch)
    embedding_backend: str = field(default_factory=lambda: _env("EMBEDDING_BACKEND", "auto").lower())
    embedding_cache: str = field(default_factory=lambda: _env("EMBEDDING_CACHE_DIR", "/tmp/ecyd-modelos" if os.getenv("VERCEL") else str(BASE_DIR / ".modelos")))
    top_k_documents: int = field(default_factory=lambda: _int("RAG_TOP_K_DOCUMENTS", 8))
    chunk_candidates: int = field(default_factory=lambda: _int("RAG_CHUNK_CANDIDATES", 80))
    top_k_chunks: int = field(default_factory=lambda: _int("RAG_TOP_K_CHUNKS", 8))
    max_chunks_per_doc: int = field(default_factory=lambda: _int("RAG_MAX_CHUNKS_PER_DOC", 3))
    max_context_chars: int = field(default_factory=lambda: _int("RAG_MAX_CONTEXT_CHARS", 12000))
    min_relevance: float = field(default_factory=lambda: _float("RAG_MIN_RELEVANCE", 0.30))

    # --- Memoria / historial ----------------------------------------
    db_path: Path = field(default_factory=lambda: Path(_env("DB_PATH", "/tmp/memoria.db" if os.getenv("VERCEL") else str(BASE_DIR / "data" / "memoria.db"))))
    history_messages: int = field(default_factory=lambda: _int("HISTORY_MESSAGES", 8))
    auto_memory: bool = field(default_factory=lambda: _bool("AUTO_MEMORY", True))
    # Memoria en Supabase (si están definidas se usa en lugar de SQLite; necesario en Vercel)
    supabase_url: str = field(default_factory=lambda: _env("SUPABASE_URL").rstrip("/"))
    supabase_key: str = field(default_factory=lambda: _env("SUPABASE_KEY"))
    db_secret: str = field(default_factory=lambda: _env("ECYD_DB_SECRET"))

    # --- Web --------------------------------------------------------
    app_password: str = field(default_factory=lambda: _env("APP_PASSWORD"))
    secret_key: str = field(default_factory=lambda: _env("SECRET_KEY"))
    host: str = field(default_factory=lambda: _env("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _int("PORT", 8000))


settings = Settings()
