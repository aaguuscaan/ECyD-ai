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


# Repositorio ONNX que usa fastembed para cada modelo y archivos necesarios
_ONNX_FILES = ["config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]


def _download_onnx(model_name: str):
    """Descarga explícita del modelo ONNX (sin caché extra) con errores claros.
    Devuelve la carpeta local o None si fastembed debe resolverlo solo."""
    try:
        from fastembed import TextEmbedding
        info = next((m for m in TextEmbedding.list_supported_models() if m["model"] == model_name), None)
        repo = ((info or {}).get("sources") or {}).get("hf")
        if not repo:
            return None
        from huggingface_hub import hf_hub_download
        target = os.path.join(settings.embedding_cache, repo.replace("/", "__"))
        os.makedirs(target, exist_ok=True)
        files = [info["model_file"], *(info.get("additional_files") or []), *_ONNX_FILES]
        for f in files:
            dest = os.path.join(target, f)
            if os.path.exists(dest) and os.path.getsize(dest) > 0:
                continue
            try:
                hf_hub_download(repo_id=repo, filename=f, local_dir=target)
            except Exception as e:  # noqa: BLE001
                if f == info["model_file"] or f == "tokenizer.json":
                    import shutil
                    free = shutil.disk_usage(settings.embedding_cache).free // 2**20
                    raise RuntimeError(f"No se pudo descargar {repo}/{f}: {type(e).__name__}: {e} "
                                       f"(espacio libre: {free} MB)") from e
        return target
    except RuntimeError:
        raise
    except Exception as e:  # noqa: BLE001
        log.warning("Descarga explícita no disponible (%s); la resuelve fastembed", e)
        return None


def _limit_tokens(model, max_len: int):
    """sentence-transformers usa 128 tokens para este modelo; fastembed 512.
    Se iguala para que los vectores coincidan con los del índice."""
    for path in (("model", "tokenizer"), ("model", "model", "tokenizer"), ("tokenizer",)):
        obj = model
        try:
            for attr in path:
                obj = getattr(obj, attr)
            obj.enable_truncation(max_length=max_len)
            return True
        except Exception:  # noqa: BLE001
            continue
    log.warning("No se pudo ajustar el largo máximo de tokens del modelo")
    return False


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
                path = _download_onnx(_hf_name(self.model_name))
                kwargs = {"specific_model_path": path} if path else {}
                self._model = TextEmbedding(model_name=_hf_name(self.model_name),
                                            cache_dir=settings.embedding_cache, threads=1, **kwargs)
                _limit_tokens(self._model, 128)  # igual que sentence-transformers
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
