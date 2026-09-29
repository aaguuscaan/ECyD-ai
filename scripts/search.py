"""
Buscador semántico de consola (sin LLM). Útil para revisar qué recupera el RAG.

    python scripts/search.py
    python scripts/search.py "cómo acompañar a un adolescente que se aísla" --etapa 2
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.retrieval import Retriever  # noqa: E402


def show(r: Retriever, q: str, etapa):
    hits = r.search(q, etapa=etapa)
    print("\n" + "-" * 70)
    if r.is_weak(hits):
        print("⚠️  Evidencia débil para esta consulta")
    for h in hits:
        print(f"[F{h.n}] {h.titulo}  ·  {h.tipo}  ·  etapas {h.etapas or '-'}  ·  "
              f"sim {h.similitud:.3f}  score {h.score:.3f}")
        print("      " + h.texto[:220].replace("\n", " ") + "…")
    print("-" * 70)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("consulta", nargs="?")
    ap.add_argument("--etapa", type=int)
    a = ap.parse_args()
    r = Retriever()
    if a.consulta:
        show(r, a.consulta, a.etapa)
        return
    print("Escribí una consulta ('salir' para terminar).")
    while True:
        try:
            q = input("\n🔎 ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"salir", "exit", "q"}:
            break
        if q:
            show(r, q, a.etapa)


if __name__ == "__main__":
    main()
