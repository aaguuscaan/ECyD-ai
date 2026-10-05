"""
Arma el PROGRAMA de cada etapa a partir de los materiales reales y organiza el
contenido por etapa. No inventa nada: todo sale de los documentos cargados.

    python scripts/build_programas.py

Fuentes:
  1. "Formando apóstoles en el ECyD", Tomo III, "El camino pedagógico del ECYD
     (las etapas)": por etapa, edades, lo que vive el adolescente, temas
     centrales, necesidades, Alianza, Amor, Virtud, Símbolo y pistas.
  2. Las fichas de cada etapa, organizadas por mes en sus carpetas originales
     (ciclo escolar mexicano, con equivalente argentino) y por tiempo litúrgico.
     Eso da los TEMAS POR MES.

Genera:
  data/programas.json   programa + calendario de temas por etapa
  y actualiza la metadata (sin recalcular embeddings):
  data/documents.json   "categoria" de cada documento
  data/chunks.json      "categoria"; los fragmentos de Formando apóstoles que
                        pertenecen a una etapa quedan con esa etapa y rol "programa"
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import corpus as C  # noqa: E402
from app.config import settings  # noqa: E402

DATA = settings.data_dir
FUENTE_TITULO = "formando apostoles en el ecyd"
ORDINALES = {1: "Primera", 2: "Segunda", 3: "Tercera", 4: "Cuarta"}

# Orden del año escolar argentino (equivalencias definidas en la ingesta)
PERIODOS_AR = ["marzo", "abril", "mayo", "junio", "julio_agosto", "agosto_septiembre",
               "septiembre", "octubre", "noviembre", "diciembre"]
LITURGICOS = ["cuaresma", "pascua", "cristo_rey", "navidad"]

SUBSECCIONES = [
    ("fisico", r"Lo que le (?:está )?pasa(?:ndo)? a nivel físico"),
    ("piensa_siente", r"Lo que piensa y siente"),
    ("le_ayuda", r"Lo que le ayuda"),
    ("temas_centrales", r"Temas centrales"),
    ("necesidades", r"Las necesidades que se enfatizan en esta etapa(?: son)?:"),
    ("alianza", r"Alianza"),
    ("amor", r"Amor"),
    ("virtud", r"Virtud"),
    ("simbolo", r"Símbolo"),
    ("pistas", r"(?:d\. )?Pistas para vivir los elementos de?l? la vida del ECYD"),
]


def clean_section(text: str) -> str:
    lines = []
    for l in text.split("\n"):
        s = l.strip()
        if not s:
            lines.append("")
            continue
        if s.startswith("Formando apóstoles en el ECYD") or s.startswith("El camino formativo del adolescente"):
            continue
        if re.fullmatch(r"\d{1,3}", s):
            continue
        if re.match(r"^\d{2,3} (cfr\.|Estatuto|Fascículo|Papa|Christus|Ibid|CEC|Jn|Mt|Lc|Mc)", s):
            continue  # notas al pie
        lines.append(s)
    t = "\n".join(lines)
    t = re.sub(r"(\w)- ?\n(\w)", r"\1\2", t)          # palabras cortadas
    t = re.sub(r"(\w) -\n(\w)", r"\1\2", t)
    t = re.sub(r"(?<![.:•\n])\n(?!\n|•|[A-ZÁÉÍÓÚ¿“])", " ", t)  # une renglones
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def first_sentences(text: str, n: int = 2, max_chars: int = 420) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s\d{1,3}\s?[Cc]fr\..*$", "", text)       # llamada/nota al pie
    text = re.sub(r"(?<=[.”\"])\s?\d{1,3}(?=\s|$)", "", text)  # número de nota tras el punto
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ“])", text)
    out = " ".join(parts[:n])
    return out[:max_chars].rsplit(" ", 1)[0] + "…" if len(out) > max_chars else out


def extract_stage_sections(doc_text: str):
    starts = []
    for n in range(1, 5):
        ms = list(re.finditer(rf"{n}\. {ORDINALES[n]} etapa \((\d+-\d+)", doc_text))
        if not ms:
            raise SystemExit(f"No encontré la sección de la etapa {n} en Formando apóstoles")
        m = ms[-1]  # la primera aparición es el índice
        starts.append((n, m.start(), m.group(1)))
    ends = [s[1] for s in starts[1:]]
    bib = [m.start() for m in re.finditer(r"\nBibliografía", doc_text)]
    ends.append(next((b for b in bib if b > starts[-1][1]), len(doc_text)))
    out = {}
    for (n, start, edades), end in zip(starts, ends):
        raw = doc_text[start:end]
        secs = {}
        heads = []
        for key, pat in SUBSECCIONES:
            m = re.search(r"(?:^|\n)\s*(?:[a-h]\. )?" + pat + r"\s*\n", raw)
            if m:
                heads.append((m.start(), m.end(), key))
        heads.sort()
        for i, (s0, s1, key) in enumerate(heads):
            e = heads[i + 1][0] if i + 1 < len(heads) else len(raw)
            secs[key] = clean_section(raw[s1:e])
        out[n] = {"edades": f"{edades} años", "start": start, "end": end, "secciones": secs}
    return out


def bullet_list(text: str):
    text = re.split(r"\s[a-h]\. [A-ZÁÉÍÓÚ]", text or "")[0]  # corta en el subtítulo siguiente
    items = []
    for x in re.split(r"•", text):
        x = re.sub(r"\s+", " ", x)
        x = re.sub(r"\s\d{2,3}\s?cfr.*$", "", x)            # nota al pie pegada
        x = re.sub(r"\.?\s*Alianza, [Aa]mor.*$", "", x)       # subtítulo pegado
        x = x.strip(" .")
        if x:
            items.append(x)
    return [i for i in items if 5 < len(i) < 200]


def build_calendar(docs, etapa: int):
    """Fichas de la etapa agrupadas por período (mes argentino) y tiempo litúrgico."""
    cal = {}

    def add(key, entry):
        cal.setdefault(key, [])
        if entry["doc_id"] not in [e["doc_id"] for e in cal[key]]:
            cal[key].append(entry)

    for d in docs:
        if d.get("categoria") not in ("ficha", "recurso") or d.get("tipo") != "ficha":
            continue
        variantes = [{"etapas": d["etapas"], "calendario": d["calendario"]}] + [
            {"etapas": x.get("etapas", []), "calendario": x.get("calendario", {})}
            for x in d["fuente"].get("duplicados", [])]
        for v in variantes:
            if etapa not in (v["etapas"] or []):
                continue
            cal_v = v["calendario"] or {}
            entry = {"doc_id": d["id"], "titulo": d["titulo"], "temas": d.get("temas", []),
                     "categoria": d.get("categoria")}
            if cal_v.get("tiempo_liturgico"):
                add(cal_v["tiempo_liturgico"], entry)
                continue
            for mes in cal_v.get("meses_originales") or ([cal_v["mes_original"]] if cal_v.get("mes_original") else []):
                ar = C.MES_ARGENTINO.get(mes)
                if ar:
                    add(ar, {**entry, "mes_original": mes})
    periodos = [{"periodo": p, "fichas": cal[p]} for p in PERIODOS_AR if p in cal]
    liturgicos = [{"tiempo_liturgico": p, "fichas": cal[p]} for p in LITURGICOS if p in cal]
    return periodos, liturgicos


def main():
    corpus = json.load(open(DATA / "corpus.json", encoding="utf-8"))
    docs = corpus["documentos"]
    for d in docs:
        d.setdefault("categoria", C.detect_categoria(d))
    fuente = next((d for d in docs if C.norm(d["titulo"]).startswith(FUENTE_TITULO)), None)
    if not fuente:
        raise SystemExit("No está 'Formando apóstoles en el ECyD' en el corpus")
    secciones = extract_stage_sections(fuente["texto"])

    nivel_escolar = {}
    for d in docs:
        for e in d.get("etapas", []):
            for n in d.get("nivel_escolar", []):
                nivel_escolar.setdefault(e, set()).add(n)

    etapas = {}
    for n, info in secciones.items():
        s = info["secciones"]
        periodos, liturgicos = build_calendar(docs, n)
        etapas[str(n)] = {
            "etapa": n,
            "nombre": f"{ORDINALES[n]} etapa",
            "edades": info["edades"],
            "nivel_escolar_mexico": sorted(nivel_escolar.get(n, [])),
            "resumen": {
                "alianza": first_sentences(s.get("alianza", "")),
                "amor": first_sentences(s.get("amor", ""), 1),
                "virtud": first_sentences(s.get("virtud", ""), 1),
                "simbolo": first_sentences(s.get("simbolo", ""), 1),
            },
            "necesidades": bullet_list(s.get("necesidades", "")) or [
                b for b in bullet_list(s.get("temas_centrales", "")) if b.lower().startswith("necesita")],
            "temas_centrales": s.get("temas_centrales", ""),
            "secciones": s,
            "calendario": periodos,
            "tiempos_liturgicos": liturgicos,
        }

    programas = {
        "schema_version": "1.0",
        "generado": C.now_iso(),
        "fuente": {"doc_id": fuente["id"], "titulo": fuente["titulo"],
                   "seccion": "Tomo III: El camino formativo del adolescente del ECYD — II. El camino pedagógico del ECYD (las etapas)"},
        "nota_calendario": ("Los temas por mes salen de las carpetas de fichas de cada etapa (ciclo escolar "
                            "mexicano) con su equivalente en el ciclo argentino; las fichas de tiempos "
                            "litúrgicos (Cuaresma, Navidad, Cristo Rey) se ubican según el calendario litúrgico."),
        "periodos": PERIODOS_AR,
        "etapas": etapas,
    }
    with open(DATA / "programas.json", "w", encoding="utf-8") as f:
        json.dump(programas, f, ensure_ascii=False, indent=1)

    # --- metadata de documentos y fragmentos (sin tocar los vectores) ---
    by_id = {d["id"]: d for d in docs}
    dj = json.load(open(DATA / "documents.json", encoding="utf-8"))
    for d in dj["documentos"]:
        d["categoria"] = by_id.get(d["id"], {}).get("categoria") or C.detect_categoria(d)
    dj["categorias"] = C.CATEGORIAS
    with open(DATA / "documents.json", "w", encoding="utf-8") as f:
        json.dump(dj, f, ensure_ascii=False, indent=1)

    cj = json.load(open(DATA / "chunks.json", encoding="utf-8"))
    flat = re.sub(r"\s+", " ", fuente["texto"])
    # límites de cada etapa en el texto "aplanado"
    bounds = []
    for n in range(1, 5):
        ms = list(re.finditer(rf"{n}\. {ORDINALES[n]} etapa \(\d+-\d+", flat))
        bounds.append((n, ms[-1].start()))
    bib = [m.start() for m in re.finditer(r"Bibliografía", flat)]
    end_all = next((b for b in bib if b > bounds[-1][1]), len(flat))
    tagged = 0
    for ch in cj["chunks"]:
        doc = by_id.get(ch["doc_id"])
        ch["categoria"] = (doc or {}).get("categoria") or ch.get("categoria") or "documento"
        ch.pop("rol", None)
        if ch["doc_id"] != fuente["id"]:
            continue
        ch["etapas"] = []
        pos = flat.find(re.sub(r"\s+", " ", ch["texto"])[:120])
        if pos < 0:
            continue
        for i, (n, start) in enumerate(bounds):
            end = bounds[i + 1][1] if i + 1 < len(bounds) else end_all
            if start <= pos < end:
                ch["etapas"] = [n]
                ch["rol"] = "programa"
                ch["categoria"] = "programa"
                tagged += 1
    with open(DATA / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(cj, f, ensure_ascii=False, indent=1)

    # corpus: guardar categoría
    with open(DATA / "corpus.json", "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=1)

    print(f"✅ programas.json: {len(etapas)} etapas")
    for k, e in etapas.items():
        print(f"   Etapa {k} ({e['edades']}): {sum(len(p['fichas']) for p in e['calendario'])} fichas en "
              f"{len(e['calendario'])} períodos + {len(e['tiempos_liturgicos'])} tiempos litúrgicos · "
              f"virtud: {e['resumen']['virtud'][:60]}")
    print(f"✅ fragmentos de programa marcados con su etapa: {tagged}")


if __name__ == "__main__":
    main()
