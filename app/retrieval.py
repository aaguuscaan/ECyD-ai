"""
Recuperación en dos etapas sobre el corpus ECyD.

    consulta
      → FAISS documentos  (qué documentos tratan el tema)
      → FAISS chunks      (qué fragmentos responden)
      → PROGRESIÓN DE ETAPAS (si el equipo tiene etapa N):
            · etapa N y material general (estatutos, estilo formativo): sí
            · etapa N+1: solo como complemento (penalizada, máx. 2 fragmentos)
            · etapa N-1: solo como complemento (penalizada, máx. 2 fragmentos)
            · otras etapas: NO, salvo que la consulta las nombre explícitamente
      → re-ranking: similitud del fragmento
                    + afinidad del documento
                    + prioridad de la fuente: programa > fichas > documentos > recursos
                    + autoridad (jerarquía del prompt)
      → diversificación (máx. N fragmentos por documento)
      → contexto numerado [F1], [F2], …
"""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional

import numpy as np

from .config import settings

log = logging.getLogger("ecyd.rag")

AUTHORITY_BONUS = {1: 0.05, 2: 0.04, 3: 0.02, 4: 0.01, 5: 0.0}
DOC_WEIGHT = 0.12
FOREIGN_LANG_PENALTY = 0.03
# Prioridad de fuentes pedida: programa > fichas > documentos > recursos
CATEGORIA_BONUS = {"programa": 0.06, "ficha": 0.04, "documento": 0.02, "recurso": 0.0}
ETAPA_ACTUAL_BONUS = 0.06
ETAPA_VECINA_PENALTY = 0.06     # siguiente / anterior: solo complemento
MAX_VECINA = 2                  # fragmentos de la etapa siguiente o anterior
FOCUS_BONUS = 0.25              # ficha elegida explícitamente por el responsable

ETAPA_RE = re.compile(r"\b(?:([1-4])\s*(?:ª|ra|da|ta|era|a|°|º)?\s*etapa|etapa\s*([1-4])|"
                      r"(primera|segunda|tercera|cuarta)\s+etapa)\b", re.I)
_ORD = {"primera": 1, "segunda": 2, "tercera": 3, "cuarta": 4}


def etapas_mencionadas(text: str) -> set:
    out = set()
    for m in ETAPA_RE.finditer(text or ""):
        n = m.group(1) or m.group(2)
        out.add(int(n) if n else _ORD[m.group(3).lower()])
    return out


def relacion_etapa(chunk_etapas: List[int], etapa: Optional[int], explicitas: set) -> str:
    """actual | general | siguiente | anterior | explicita | fuera"""
    if not chunk_etapas:
        return "general"
    if not etapa:
        return "explicita" if (explicitas and set(chunk_etapas) & explicitas) else (
            "fuera" if explicitas else "general")
    if etapa in chunk_etapas:
        return "actual"
    if explicitas and set(chunk_etapas) & explicitas:
        return "explicita"
    if etapa + 1 in chunk_etapas:
        return "siguiente"
    if etapa - 1 in chunk_etapas:
        return "anterior"
    return "fuera"


@dataclass
class Hit:
    n: int
    chunk_id: str
    doc_id: str
    titulo: str
    tipo: str
    etapas: List[int]
    autoridad: int
    similitud: float
    score: float
    texto: str
    doc_score: float = 0.0
    categoria: str = "documento"
    relacion: str = "general"
    extra: Dict = field(default_factory=dict)

    def public(self, preview: int = 420) -> dict:
        d = asdict(self)
        d["texto"] = self.texto[:preview] + ("…" if len(self.texto) > preview else "")
        return d


class Retriever:
    def __init__(self, data_dir=None, embed_fn: Optional[Callable[[List[str]], np.ndarray]] = None):
        import faiss

        self.data_dir = data_dir or settings.data_dir
        self.manifest = self._load("index_manifest.json")
        self.documents = self._load("documents.json")["documentos"]
        chunks_file = self._load("chunks.json")
        self.chunks = chunks_file["chunks"]
        self.chunker = chunks_file.get("chunker", {})
        self.doc_index = faiss.read_index(str(self.data_dir / "documents.index"))
        self.chunk_index = faiss.read_index(str(self.data_dir / "chunks.index"))

        if self.doc_index.ntotal != len(self.documents) or self.chunk_index.ntotal != len(self.chunks):
            raise RuntimeError(
                "Los índices FAISS no coinciden con documents.json/chunks.json. "
                "Ejecutá: python scripts/build_index.py")

        self.doc_by_id = {d["id"]: d for d in self.documents}
        self.chunks_by_doc: Dict[str, List[int]] = {}
        for i, c in enumerate(self.chunks):
            self.chunks_by_doc.setdefault(c["doc_id"], []).append(i)
        # Vectores de chunks en memoria (≈3 MB) para puntuar los chunks de los
        # documentos preseleccionados aunque no hayan salido en la búsqueda global.
        self.chunk_vectors = self.chunk_index.reconstruct_n(0, self.chunk_index.ntotal)
        self.expand_neighbors = self.chunker.get("metodo") != "legacy_v1"

        self._embed_fn = embed_fn
        self.embedding_check: dict = {}
        model_name = self.manifest.get("embedding_model")
        if model_name and model_name != settings.embedding_model:
            log.warning("EMBEDDING_MODEL=%s pero los índices se construyeron con %s. Se usa el del índice.",
                        settings.embedding_model, model_name)
        self.model_name = model_name or settings.embedding_model
        log.info("RAG listo: %d documentos, %d chunks (%s)", len(self.documents), len(self.chunks),
                 self.chunker.get("metodo"))

    # ------------------------------------------------------------------
    def _load(self, name):
        path = self.data_dir / name
        if not path.exists():
            raise FileNotFoundError(
                f"Falta {path}. Si venís de la versión anterior ejecutá: python scripts/migrate_v1.py")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def embed(self, texts: List[str]) -> np.ndarray:
        if self._embed_fn:
            v = np.asarray(self._embed_fn(texts), dtype=np.float32)
            return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
        from .embeddings import get_embedder
        return get_embedder(self.model_name).encode(texts)

    def warmup(self):
        self.embed(["calentamiento"])
        self.embedding_check = self.check_embeddings()

    def check_embeddings(self, n: int = 5) -> dict:
        """Compara vectores recalculados con los guardados en el índice: si el
        modelo en ejecución es compatible con el que armó el índice, la
        similitud promedio debe ser muy alta (> 0.9)."""
        try:
            idx = list(range(0, len(self.chunks), max(1, len(self.chunks) // n)))[:n]
            legacy = self.chunker.get("metodo") == "legacy_v1"
            from .corpus import embedding_text_for_chunk
            texts = [self.chunks[i]["texto"] if legacy else
                     embedding_text_for_chunk(self.chunks[i]["titulo"], self.chunks[i]["texto"]) for i in idx]
            sims = (self.embed(texts) * self.chunk_vectors[idx]).sum(axis=1)
            res = {"similitud_promedio": round(float(sims.mean()), 4), "muestras": len(idx)}
            res["compatible"] = res["similitud_promedio"] > 0.9
            log.info("Chequeo de embeddings: %s", res)
            return res
        except Exception as e:  # noqa: BLE001
            return {"error": str(e)}

    # ------------------------------------------------------------------
    def search(self, query: str, *, etapa: Optional[int] = None, top_k: Optional[int] = None,
               focus_docs: Optional[List[str]] = None, focus_k: int = 3) -> List[Hit]:
        """Busca respetando la progresión de etapas.

        focus_docs: fichas/documentos elegidos por el responsable (se incluyen
        sus fragmentos más relevantes primero, aunque sean de otra etapa)."""
        top_k = top_k or settings.top_k_chunks
        q = self.embed([query])
        explicitas = etapas_mencionadas(query)
        focus = set(focus_docs or [])

        # 1) documentos
        d_scores, d_idx = self.doc_index.search(q, settings.top_k_documents)
        doc_scores = {self.documents[i]["id"]: float(s) for s, i in zip(d_scores[0], d_idx[0]) if i >= 0}

        # 2) chunks: búsqueda global + chunks de los documentos preseleccionados y elegidos
        c_scores, c_idx = self.chunk_index.search(q, settings.chunk_candidates)
        sims: Dict[int, float] = {int(i): float(s) for s, i in zip(c_scores[0], c_idx[0]) if i >= 0}
        for doc_id in list(doc_scores) + list(focus):
            idxs = self.chunks_by_doc.get(doc_id, [])
            if idxs:
                s = self.chunk_vectors[idxs] @ q[0]
                for i, v in zip(idxs, s):
                    sims[i] = float(v)
        if etapa:  # el programa de la etapa siempre compite
            prog = [i for i, c in enumerate(self.chunks) if c.get("rol") == "programa" and etapa in c.get("etapas", [])]
            if prog:
                s = self.chunk_vectors[prog] @ q[0]
                for i, v in zip(prog, s):
                    sims.setdefault(i, float(v))

        # 3) re-ranking con progresión de etapas
        scored = []
        for i, sim in sims.items():
            c = self.chunks[i]
            rel = "foco" if c["doc_id"] in focus else relacion_etapa(c.get("etapas") or [], etapa, explicitas)
            if rel == "fuera":
                continue
            score = sim + DOC_WEIGHT * doc_scores.get(c["doc_id"], 0.0)
            score += AUTHORITY_BONUS.get(c.get("autoridad", 5), 0.0)
            score += CATEGORIA_BONUS.get(c.get("categoria", "documento"), 0.0)
            if rel in ("actual", "explicita"):
                score += ETAPA_ACTUAL_BONUS
            elif rel in ("siguiente", "anterior"):
                score -= ETAPA_VECINA_PENALTY
            elif rel == "foco":
                score += FOCUS_BONUS
            if c.get("idioma") and c["idioma"] != "es":
                score -= FOREIGN_LANG_PENALTY
            scored.append((score, sim, i, rel))
        scored.sort(key=lambda x: x[0], reverse=True)

        # 4) diversificación + deduplicación de texto + topes por relación
        hits: List[Hit] = []
        per_doc: Dict[str, int] = {}
        vecinas = 0
        seen_text = set()
        for score, sim, i, rel in scored:
            c = self.chunks[i]
            cap = focus_k if rel == "foco" else settings.max_chunks_per_doc
            if per_doc.get(c["doc_id"], 0) >= cap:
                continue
            if rel in ("siguiente", "anterior"):
                if vecinas >= MAX_VECINA:
                    continue
            key = re.sub(r"\W+", "", c["texto"][:200].lower())
            if key in seen_text:
                continue
            seen_text.add(key)
            if rel in ("siguiente", "anterior"):
                vecinas += 1
            per_doc[c["doc_id"]] = per_doc.get(c["doc_id"], 0) + 1
            hits.append(Hit(
                n=len(hits) + 1, chunk_id=c["id"], doc_id=c["doc_id"], titulo=c["titulo"],
                tipo=c["tipo"], etapas=c.get("etapas") or [], autoridad=c.get("autoridad", 5),
                similitud=round(sim, 4), score=round(score, 4), texto=self._text_with_neighbors(i),
                doc_score=round(doc_scores.get(c["doc_id"], 0.0), 4),
                categoria=c.get("categoria", "documento"), relacion=rel))
            if len(hits) >= top_k:
                break
        return hits

    def _text_with_neighbors(self, i: int) -> str:
        c = self.chunks[i]
        if not self.expand_neighbors:
            return c["texto"]
        idxs = self.chunks_by_doc[c["doc_id"]]
        pos = idxs.index(i)
        text = c["texto"]
        if pos + 1 < len(idxs):  # el siguiente fragmento suele completar la idea
            nxt = self.chunks[idxs[pos + 1]]["texto"]
            # quita el solapamiento entre fragmentos consecutivos
            head = nxt[:40]
            k = text.rfind(head, max(0, len(text) - 300)) if head else -1
            if k >= 0 and nxt.startswith(text[k:]):
                nxt = nxt[len(text) - k:]
            text += " " + nxt.lstrip()
        return text

    # ------------------------------------------------------------------
    @staticmethod
    def is_weak(hits: List[Hit]) -> bool:
        return not hits or max(h.similitud for h in hits) < settings.min_relevance

    @staticmethod
    def build_context(hits: List[Hit], max_chars: Optional[int] = None) -> str:
        max_chars = max_chars or settings.max_context_chars
        if not hits:
            return "No se recuperaron fragmentos pertinentes del corpus para esta consulta."
        parts, total = [], 0
        if Retriever.is_weak(hits):
            parts.append("⚠️ EVIDENCIA DÉBIL: los fragmentos recuperados tienen baja relevancia para la "
                         "consulta. No atribuyas al ECyD nada que no esté claramente en ellos.\n")
        from .corpus import CATEGORIAS, AUTORIDAD
        rel_txt = {"actual": " (etapa del equipo)", "siguiente": " (ETAPA SIGUIENTE: solo como complemento)",
                   "anterior": " (etapa anterior: solo como complemento)",
                   "explicita": " (etapa pedida en la consulta)", "foco": " (elegido por el responsable)",
                   "general": ""}
        for h in hits:
            etapas = (", ".join(str(e) for e in h.etapas) or "general") + rel_txt.get(h.relacion, "")
            text = re.sub(r"\s+", " ", h.texto).strip()
            categoria = CATEGORIAS.get(h.categoria, h.categoria)
            if h.categoria == "programa":
                categoria = "Programa de la etapa (Formando apóstoles, Tomo III)"
            block = (f"[F{h.n}] {h.titulo}\n"
                     f"Tipo: {categoria} · Etapa: {etapas} · "
                     f"Autoridad: {h.autoridad} ({AUTORIDAD.get(h.autoridad, '')}) · Relevancia: {h.similitud:.2f}\n"
                     f"{text}\n")
            if total + len(block) > max_chars:
                room = max_chars - total
                if room > 400:
                    parts.append(block[:room] + "…\n")
                break
            parts.append(block)
            total += len(block)
        return "\n".join(parts)

    def document_list(self) -> List[dict]:
        keys = ["id", "titulo", "tipo", "categoria", "autoridad", "etapas", "idioma", "temas", "calendario",
                "nivel_escolar", "num_chunks", "resumen"]
        out = []
        for d in self.documents:
            item = {k: d.get(k) for k in keys}
            item["archivo"] = d["fuente"]["archivo"]
            item["carpeta"] = d["fuente"].get("carpeta")
            item["duplicados"] = [{"etapas": x.get("etapas"), "calendario": x.get("calendario")}
                                  for x in d["fuente"].get("duplicados", [])]
            out.append(item)
        return out

    def document_text(self, doc_id: str, max_chars: int = 0) -> str:
        """Texto de un documento reconstruido desde sus fragmentos (para leer una ficha)."""
        parts = [self.chunks[i]["texto"] for i in self.chunks_by_doc.get(doc_id, [])]
        text = "\n".join(parts)
        return text[:max_chars] if max_chars else text

    def stats(self) -> dict:
        return {"documentos": len(self.documents), "chunks": len(self.chunks),
                "embedding_model": self.model_name, "chunker": self.chunker.get("metodo"),
                "generado": self.manifest.get("generado"), "embeddings": self.embedding_check}


_retriever: Optional[Retriever] = None
_rlock = threading.Lock()


def get_retriever() -> Retriever:
    global _retriever
    with _rlock:
        if _retriever is None:
            _retriever = Retriever()
    return _retriever
