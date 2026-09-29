"""
Ingesta de PDFs → data/corpus.json (schema v2).

    python scripts/ingest_corpus.py                 # usa ECYD_DOCS_DIR o E:\\ECyD
    python scripts/ingest_corpus.py --docs "D:\\Material ECyD"
    python scripts/build_index.py                   # después: índices

Extracción: pypdf; si el PDF no tiene texto, OCR con Tesseract (spa+eng).
Los IDs de documentos ya existentes se conservan (por ruta), así la memoria y
las referencias no cambian al agregar material nuevo.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import corpus as C  # noqa: E402
from app.config import settings  # noqa: E402

DEFAULT_DOCS = os.getenv("ECYD_DOCS_DIR", r"E:\ECyD")


def extraer_pypdf(path: Path) -> str:
    from pypdf import PdfReader
    try:
        reader = PdfReader(str(path))
        return "\n\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ Error pypdf: {e}")
        return ""


def buscar_tesseract():
    for ruta in [r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                 r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]:
        if os.path.exists(ruta):
            return ruta
    return None


def extraer_ocr(path: Path) -> str:
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image
    except ImportError:
        print("   ❌ Para OCR instalá: pip install pymupdf pytesseract pillow (y Tesseract)")
        return ""
    t = buscar_tesseract()
    if t:
        pytesseract.pytesseract.tesseract_cmd = t
    paginas = []
    with fitz.open(str(path)) as doc:
        for n, pagina in enumerate(doc, start=1):
            print(f"      🔍 OCR página {n}/{len(doc)}", end="\r")
            pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            paginas.append(pytesseract.image_to_string(img, lang="spa+eng") or "")
    print(" " * 50, end="\r")
    return "\n\n".join(paginas)


def extraer_docx(path: Path) -> str:
    try:
        import docx  # python-docx
    except ImportError:
        print("   ⚠️ Para .docx instalá: pip install python-docx")
        return ""
    return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=DEFAULT_DOCS, help="Carpeta con el material ECyD")
    args = ap.parse_args()
    base = Path(args.docs)
    if not base.exists():
        sys.exit(f"❌ No existe la carpeta {base}")

    out = settings.data_dir / "corpus.json"
    previous = {}
    if out.exists():
        old = json.load(open(out, encoding="utf-8"))
        if str(old.get("schema_version", "")).startswith("2"):
            for d in old["documentos"]:
                previous[d["fuente"]["ruta"]] = d
                for dup in d["fuente"].get("duplicados", []):
                    previous.setdefault(dup["ruta"], d)
    next_n = 1 + max([int(d["id"].split("_")[1]) for d in previous.values()] or [0])

    overrides = C.load_overrides(settings.data_dir / "overrides.json")
    files = sorted(p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in {".pdf", ".docx"})
    print(f"📂 {base} → {len(files)} archivos")

    docs = []
    for path in files:
        print(f"📄 {path.name}")
        if path.suffix.lower() == ".docx":
            texto, metodo = extraer_docx(path), "docx"
        else:
            texto, metodo = extraer_pypdf(path), "pypdf"
            if len(texto.strip()) < 100:
                print("   ⚠️ Sin texto: intentando OCR…")
                texto, metodo = extraer_ocr(path), "ocr"
        prev = previous.get(str(path))
        if prev:
            doc_id, legacy = prev["id"], prev.get("ids_legacy", [])
        else:
            doc_id, legacy = f"doc_{next_n:04d}", []
            next_n += 1
        d = C.build_document(doc_id=doc_id, archivo=path.name, ruta=str(path), texto=texto,
                             metodo=metodo, ids_legacy=legacy, overrides=overrides)
        print(f"   ✅ {d['tipo']} · etapas={d['etapas']} · {d['calendario']['mes_original']} · "
              f"{d['extraccion']['caracteres']} caracteres · calidad {d['extraccion']['calidad']}"
              if texto.strip() else "   ❌ No se pudo extraer texto")
        docs.append(d)

    # si un documento duplicado quedó con id propio, se unifica
    docs = C.merge_duplicates(docs)
    corpus = C.build_corpus(docs, origen=f"ingest_corpus.py sobre {base}")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=1)
    print("\n✅ Corpus guardado en", out)
    print(json.dumps(corpus["estadisticas"], ensure_ascii=False, indent=2))
    print("\n➡️  Ahora ejecutá: python scripts/build_index.py")


if __name__ == "__main__":
    main()
