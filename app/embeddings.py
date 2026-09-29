"""
Modelo de embeddings (convierte texto en vectores para buscar en el corpus).

Siempre es el mismo modelo, paraphrase-multilingual-MiniLM-L12-v2, en una de
estas versiones (EMBEDDING_BACKEND):

  - onnx (por defecto): versión ONNX cuantizada (~120 MB) con onnxruntime.
    Liviana, es la que usa Vercel.
  - fastembed: versión ONNX de fastembed (~235 MB).
  - sentence-transformers: la versión original en PyTorch (~2 GB).

En todos los casos: 128 tokens máximo, mean pooling y vectores normalizados,
igual que sentence-transformers.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import List

import numpy as np

from .config import settings

log = logging.getLogger("ecyd.embeddings")

if os.getenv("VERCEL"):  # en Vercel solo /tmp es escribible y tiene poco espacio
    os.environ.setdefault("HF_HOME", "/tmp/hf")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # evita copias extra en caché
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

MAX_TOKENS = 128

# Versión ONNX del modelo (exportada por Xenova desde el original)
ONNX_REPOS = {
    "paraphrase-multilingual-MiniLM-L12-v2": "Xenova/paraphrase-multilingual-MiniLM-L12-v2",
}
ONNX_FILE = os.getenv("EMBEDDING_ONNX_FILE", "onnx/model_quantized.onnx")


def _hf_name(name: str) -> str:
    return name if "/" in name else f"sentence-transformers/{name}"


def _free_mb(path: str) -> int:
    import shutil
    try:
        return shutil.disk_usage(path).free // 2**20
    except OSError:
        return -1


def download_onnx(model_name: str, target_dir: str | None = None) -> str:
    """Descarga (una vez) el modelo ONNX y el tokenizer. Devuelve la carpeta."""
    from huggingface_hub import hf_hub_download

    repo = ONNX_REPOS.get(model_name.split("/")[-1])
    if not repo:
        raise RuntimeError(f"No hay versión ONNX configurada para {model_name}")
    target = target_dir or os.path.join(settings.embedding_cache, repo.replace("/", "__"))
    os.makedirs(target, exist_ok=True)
    for f in ("tokenizer.json", ONNX_FILE):
        dest = os.path.join(target, f)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            continue
        try:
            hf_hub_download(repo_id=repo, filename=f, local_dir=target)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"No se pudo descargar {repo}/{f}: {type(e).__name__}: {e} "
                               f"(espacio libre: {_free_mb(target)} MB)") from e
    return target


class _OnnxModel:
    def __init__(self, folder: str):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.tok = Tokenizer.from_file(os.path.join(folder, "tokenizer.json"))
        self.tok.enable_truncation(max_length=MAX_TOKENS)
        pad_id = self.tok.token_to_id("<pad>")
        self.tok.enable_padding(pad_id=pad_id if pad_id is not None else 1, pad_token="<pad>")
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = int(os.getenv("EMBEDDING_THREADS", "1"))
        self.sess = ort.InferenceSession(os.path.join(folder, ONNX_FILE), opts,
                                         providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}

    def embed(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        out = []
        for i in range(0, len(texts), batch_size):
            enc = self.tok.encode_batch(texts[i:i + batch_size])
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feed = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self.inputs:
                feed["token_type_ids"] = np.zeros_like(ids)
            hidden = self.sess.run(None, {k: v for k, v in feed.items() if k in self.inputs})[0]
            m = mask[..., None].astype(np.float32)
            out.append((hidden * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None))  # mean pooling
        return np.concatenate(out, axis=0)


class Embedder:
    def __init__(self, model_name: str | None = None, backend: str | None = None):
        self.model_name = model_name or settings.embedding_model
        backend = (backend or settings.embedding_backend or "auto").lower()
        if backend == "auto":
            backend = "onnx"
        self.backend = backend
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is not None:
                return
            log.info("Cargando modelo de embeddings %s (%s)…", self.model_name, self.backend)
            if self.backend == "onnx":
                self._model = _OnnxModel(download_onnx(self.model_name))
            elif self.backend == "fastembed":
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name=_hf_name(self.model_name),
                                            cache_dir=settings.embedding_cache, threads=1)
                try:
                    self._model.model.tokenizer.enable_truncation(max_length=MAX_TOKENS)
                except Exception:  # noqa: BLE001
                    log.warning("No se pudo limitar a %d tokens", MAX_TOKENS)
            else:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)

    def encode(self, texts: List[str], batch_size: int = 32, show_progress: bool = False) -> np.ndarray:
        self._load()
        if self.backend == "onnx":
            if show_progress:
                v = []
                for i in range(0, len(texts), 256):
                    v.append(self._model.embed(texts[i:i + 256], batch_size))
                    print(f"   {min(i + 256, len(texts))}/{len(texts)}", end="\r")
                v = np.concatenate(v)
            else:
                v = self._model.embed(texts, batch_size)
        elif self.backend == "fastembed":
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
