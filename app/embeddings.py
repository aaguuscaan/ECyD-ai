"""
Modelo de embeddings (el que convierte texto en vectores para buscar).

Dos formas de correr el MISMO modelo (paraphrase-multilingual-MiniLM-L12-v2):
  - fastembed (ONNX): liviano (~70 MB de librerías), es el que se usa en Vercel.
  - sentence-transformers (PyTorch): la versión original, pesada (~2 GB).

EMBEDDING_BACKEND=auto usa fastembed si está instalado.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import List

import numpy as np

from .config import settings

log = logging.getLogger("ecyd.embeddings")

if os.getenv("VERCEL"):  # en Vercel solo /tmp es escribible (512 MB)
    os.environ.setdefault("HF_HOME", "/tmp/hf")
    # Descarga HTTP simple: el protocolo "xet" guarda una copia extra en caché
    # y llena /tmp ("No space left on device").
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")


def _hf_name(name: str) -> str:
    return name if "/" in name else f"sentence-transformers/{name}"


class Embedder:
    def __init__(self, model_name: str | None = None, backend: str | None = None):
        self.model_name = model_name or settings.embedding_model
        backend = (backend or settings.embedding_backend or "auto").lower()
        if backend == "auto":
            try:
                import fastembed  # noqa: F401
                backend = "fastembed"
            except ImportError:
                backend = "sentence-transformers"
        self.backend = backend
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is not None:
                return
            log.info("Cargando modelo de embeddings %s (%s)…", self.model_name, self.backend)
            if self.backend == "fastembed":
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name=_hf_name(self.model_name),
                                            cache_dir=settings.embedding_cache, threads=1)
            else:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)

    def encode(self, texts: List[str], batch_size: int = 64, show_progress: bool = False) -> np.ndarray:
        self._load()
        if self.backend == "fastembed":
            v = np.array(list(self._model.embed(texts, batch_size=batch_size)), dtype=np.float32)
        else:
            v = self._model.encode(texts, batch_size=batch_size, show_progress_bar=show_progress,
                                   convert_to_numpy=True, normalize_embeddings=True)
        v = np.asarray(v, dtype=np.float32)
        v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
        return v


_embedder: Embedder | None = None


def get_embedder(model_name: str | None = None) -> Embedder:
    global _embedder
    if _embedder is None or (model_name and _embedder.model_name != model_name):
        _embedder = Embedder(model_name)
    return _embedder
