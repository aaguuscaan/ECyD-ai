"""
Construye los índices del RAG a partir de data/corpus.json (schema v2).

    python scripts/build_index.py            # rechunk + embeddings (recomendado)
    python scripts/build_index.py --check    # solo verifica consistencia

Genera en data/:
    documents.json      metadata de documentos (sin texto completo)
    chunks.json         fragmentos con su metadata
    documents.index     FAISS (1 vector por documento)
    chunks.index        FAISS (1 vector por fragmento)
    index_manifest.json descripción y verificación de todo lo anterior
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import corpus as C  # noqa: E402
from app.config import settings  # noqa: E402

DATA = settings.data_dir


def load_corpus() -> dict:
    path = DATA / "corpus.json"
    with open(path, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    if not str(corpus.get("schema_version", "")).startswith("2"):
        sys.exit("❌ corpus.json no está en formato v2. Ejecutá antes: python scripts/migrate_v1.py")
    # re-aplica overrides por si fueron editados
    overrides = C.load_overrides(DATA / "overrides.json")
    for d in corpus["documentos"]:
        C.apply_overrides(d, overrides)
    return corpus


def make_chunks(docs, target, max_chars, overlap):
    chunks = []
    for d in docs:
        if not d.get("texto"):
            continue
        for i, t in enumerate(C.chunk_text(d["texto"], target, max_chars, overlap)):
            chunks.append(chunk_record(d, i, t))
    return chunks


def chunk_record(doc, orden, texto):
    return {
        "id": f"{doc['id']}::c{orden:03d}",
        "vector_id": None,
        "doc_id": doc["id"],
        "orden": orden,
        "titulo": doc["titulo"],
        "tipo": doc["tipo"],
        "categoria": doc.get("categoria") or C.detect_categoria(doc),
        "etapas": doc["etapas"],
        "autoridad": doc["autoridad"]["nivel"],
        "idioma": doc["idioma"],
        "caracteres": len(texto),
        "texto": texto,
    }


def write_outputs(corpus, chunks, chunk_vecs, doc_vecs, *, embedding_model, chunker):
    import faiss

    docs = corpus["documentos"]
    assert len(chunks) == len(chunk_vecs), "chunks y vectores no coinciden"
    assert len(docs) == len(doc_vecs), "documentos y vectores no coinciden"

    counts = {}
    for i, ch in enumerate(chunks):
        ch["vector_id"] = i
        counts[ch["doc_id"]] = counts.get(ch["doc_id"], 0) + 1

    documents = []
    for i, d in enumerate(docs):
        pub = C.document_public(d)
        pub["vector_id"] = i
        pub["num_chunks"] = counts.get(d["id"], 0)
        documents.append(pub)

    chunk_vecs = np.ascontiguousarray(chunk_vecs, dtype=np.float32)
    doc_vecs = np.ascontiguousarray(doc_vecs, dtype=np.float32)
    faiss.normalize_L2(chunk_vecs)
    faiss.normalize_L2(doc_vecs)

    ci = faiss.IndexFlatIP(chunk_vecs.shape[1]); ci.add(chunk_vecs)
    di = faiss.IndexFlatIP(doc_vecs.shape[1]); di.add(doc_vecs)
    faiss.write_index(ci, str(DATA / "chunks.index"))
    faiss.write_index(di, str(DATA / "documents.index"))

    def dump(name, obj):
        with open(DATA / name, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)

    dump("documents.json", {
        "schema_version": C.SCHEMA_VERSION, "generado": C.now_iso(),
        "total": len(documents), "vocabularios": corpus.get("vocabularios"),
        "documentos": documents,
    })
    dump("chunks.json", {
        "schema_version": C.SCHEMA_VERSION, "generado": C.now_iso(),
        "embedding_model": embedding_model, "chunker": chunker,
        "total": len(chunks), "chunks": chunks,
    })
    manifest = {
        "schema_version": C.SCHEMA_VERSION,
        "generado": C.now_iso(),
        "embedding_model": embedding_model,
        "dimension": int(chunk_vecs.shape[1]),
        "corpus_sha1": C.sha1("".join(d["extraccion"]["sha1"] for d in docs)),
        "documentos": {"archivo": "documents.json", "index": "documents.index", "vectores": di.ntotal},
        "chunks": {"archivo": "chunks.json", "index": "chunks.index", "vectores": ci.ntotal, "chunker": chunker},
    }
    dump("index_manifest.json", manifest)
    return manifest


def build(args):
    from app.embeddings import Embedder

    corpus = load_corpus()
    docs = corpus["documentos"]
    chunker = {"metodo": "parrafos_con_solapamiento", "objetivo": args.target,
               "maximo": args.max_chars, "solapamiento": args.overlap}
    chunks = make_chunks(docs, args.target, args.max_chars, args.overlap)
    print(f"📚 {len(docs)} documentos → 🧩 {len(chunks)} chunks")

    model = Embedder(settings.embedding_model, args.backend)
    print(f"🧠 Modelo: {settings.embedding_model} ({model.backend})")
    chunk_vecs = model.encode(
        [C.embedding_text_for_chunk(c["titulo"], c["texto"]) for c in chunks], batch_size=64, show_progress=True)

    # Vector de documento = centroide de sus chunks + descripción (título/etapa/temas).
    desc = model.encode([C.embedding_text_for_document(d) for d in docs])
    doc_vecs = np.zeros_like(desc)
    for i, d in enumerate(docs):
        idx = [j for j, c in enumerate(chunks) if c["doc_id"] == d["id"]]
        centroid = chunk_vecs[idx].mean(axis=0) if idx else desc[i]
        centroid /= (np.linalg.norm(centroid) + 1e-9)
        doc_vecs[i] = centroid + 0.5 * desc[i]

    with open(DATA / "corpus.json", "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=1)
    m = write_outputs(corpus, chunks, chunk_vecs, doc_vecs,
                      embedding_model=settings.embedding_model, chunker=chunker)
    print("✅ Índices generados:", json.dumps(m, ensure_ascii=False, indent=2))


def check():
    import faiss
    man = json.load(open(DATA / "index_manifest.json", encoding="utf-8"))
    docs = json.load(open(DATA / "documents.json", encoding="utf-8"))["documentos"]
    chunks = json.load(open(DATA / "chunks.json", encoding="utf-8"))["chunks"]
    ci = faiss.read_index(str(DATA / "chunks.index"))
    di = faiss.read_index(str(DATA / "documents.index"))
    ok = True
    ids = {d["id"] for d in docs}
    for name, a, b in [("chunks", len(chunks), ci.ntotal), ("documentos", len(docs), di.ntotal)]:
        print(f"{'✅' if a == b else '❌'} {name}: metadata={a} vectores={b}")
        ok &= a == b
    orphans = [c["id"] for c in chunks if c["doc_id"] not in ids]
    print(f"{'✅' if not orphans else '❌'} chunks huérfanos: {len(orphans)}")
    bad_vid = [c["id"] for i, c in enumerate(chunks) if c["vector_id"] != i]
    print(f"{'✅' if not bad_vid else '❌'} vector_id consistentes")
    print(f"ℹ️  modelo: {man['embedding_model']} · chunker: {man['chunks']['chunker'].get('metodo')}")
    return ok and not orphans and not bad_vid


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--target", type=int, default=650)
    p.add_argument("--max-chars", type=int, default=900)
    p.add_argument("--overlap", type=int, default=120)
    p.add_argument("--backend", default=None, help="onnx (recomendado, igual que en Vercel), fastembed o sentence-transformers")
    a = p.parse_args()
    if a.check:
        sys.exit(0 if check() else 1)
    build(a)
