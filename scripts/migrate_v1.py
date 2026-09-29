"""
Migra los datos del formato anterior (v1) al esquema v2 SIN recalcular
embeddings (no necesita descargar el modelo).

Entrada (data/legacy/ o data/):
    corpus.json (v1), chunks_metadata.json, chunks.index, ecyd.index
Salida (data/):
    corpus.json (v2), documents.json, chunks.json, documents.index,
    chunks.index, index_manifest.json

Qué corrige:
  - claves inconsistentes (texto/text, titulo/document_name, doc_index/document_index)
  - documentos duplicados (se unifican conservando etapas, rutas e IDs viejos)
  - títulos vacíos o ilegibles (data/overrides.json)
  - agrega tipo/autoridad/temas/calendario/nivel escolar/calidad de extracción
  - vector de documento = centroide de sus chunks (el anterior solo "veía"
    las primeras ~100 palabras por el límite de 128 tokens del modelo)

Los chunks conservan el corte anterior (1600 caracteres). Para rechunkear con
el nuevo método (recomendado) ejecutá después: python scripts/build_index.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import corpus as C  # noqa: E402
from scripts.build_index import DATA, chunk_record, write_outputs  # noqa: E402

LEGACY = DATA / "legacy"
LEGACY_FILES = ["corpus.json", "chunks_metadata.json", "chunks_metadata_backup.json",
                "chunks.index", "ecyd.index", "index_metadata.json", "index_metadata_backup.json"]


def legacy_path(name: str) -> Path:
    p = LEGACY / name
    return p if p.exists() else DATA / name


def backup_legacy():
    """Mueve los archivos v1 a data/legacy/ (no borra nada)."""
    LEGACY.mkdir(exist_ok=True)
    corpus_p = DATA / "corpus.json"
    if corpus_p.exists():
        v = json.load(open(corpus_p, encoding="utf-8"))
        if str(v.get("schema_version", "")).startswith("2"):
            return  # ya migrado
    for name in LEGACY_FILES:
        src, dst = DATA / name, LEGACY / name
        if src.exists() and not dst.exists():
            shutil.move(str(src), str(dst))


def main():
    import faiss

    backup_legacy()
    v1 = json.load(open(legacy_path("corpus.json"), encoding="utf-8"))
    overrides = C.load_overrides(DATA / "overrides.json")

    docs = []
    for d in v1["documentos"]:
        docs.append(C.build_document(
            doc_id=d["id"], archivo=d["archivo"], ruta=d["ruta"], texto=d.get("texto") or "",
            metodo=d.get("metodo_extraccion") or "desconocido", ids_legacy=[d["id"]],
            overrides=overrides))
    n_before = len(docs)
    docs = C.merge_duplicates(docs)
    print(f"📚 Documentos: {n_before} → {len(docs)} (duplicados unificados: {n_before - len(docs)})")

    legacy_to_doc = {}
    for d in docs:
        for lid in d["ids_legacy"]:
            legacy_to_doc[lid] = d
    canonical_legacy = {d["ids_legacy"][0] for d in docs}

    old_chunks = json.load(open(legacy_path("chunks_metadata.json"), encoding="utf-8"))
    ci = faiss.read_index(str(legacy_path("chunks.index")))
    di = faiss.read_index(str(legacy_path("ecyd.index")))
    assert ci.ntotal == len(old_chunks), "chunks.index y chunks_metadata.json no coinciden"
    old_vecs = ci.reconstruct_n(0, ci.ntotal)
    old_doc_vecs = di.reconstruct_n(0, di.ntotal)

    chunks, keep = [], []
    order = {}
    for i, oc in enumerate(old_chunks):
        legacy_id = v1["documentos"][oc["doc_index"]]["id"]
        if legacy_id not in canonical_legacy:
            continue  # chunk de un documento duplicado: ya está representado
        doc = legacy_to_doc[legacy_id]
        n = order.get(doc["id"], 0)
        order[doc["id"]] = n + 1
        chunks.append(chunk_record(doc, n, C.clean_text(oc["texto"])))
        keep.append(i)
    chunk_vecs = old_vecs[keep]
    print(f"🧩 Chunks: {len(old_chunks)} → {len(chunks)}")

    legacy_index = {d["id"]: i for i, d in enumerate(v1["documentos"])}
    doc_vecs = np.zeros((len(docs), chunk_vecs.shape[1]), dtype=np.float32)
    for i, d in enumerate(docs):
        idx = [j for j, c in enumerate(chunks) if c["doc_id"] == d["id"]]
        old = old_doc_vecs[legacy_index[d["ids_legacy"][0]]]
        if idx:
            cen = chunk_vecs[idx].mean(axis=0)
            cen /= (np.linalg.norm(cen) + 1e-9)
            doc_vecs[i] = cen + 0.5 * old
        else:
            doc_vecs[i] = old

    corpus = C.build_corpus(docs, origen="migrado desde corpus v1 (ingest_corpus.py)")
    with open(DATA / "corpus.json", "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=1)

    manifest = write_outputs(
        corpus, chunks, chunk_vecs, doc_vecs,
        embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
        chunker={"metodo": "legacy_v1", "objetivo": 1600, "maximo": 1600, "solapamiento": 0,
                 "nota": "Chunks heredados. Ejecutar scripts/build_index.py para rechunkear."})
    print("✅ Migración completa")
    print(json.dumps(corpus["estadisticas"], ensure_ascii=False, indent=2))
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
