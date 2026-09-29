"""
Esquema y utilidades del corpus ECyD (v2).

Todo lo que define "cómo se describe un documento" vive acá, para que la
ingesta de PDFs, la migración desde el formato viejo y la construcción de
índices usen exactamente la misma lógica.

Estructura de un documento en corpus.json (schema 2.x):

{
  "id": "doc_0001",
  "ids_legacy": ["doc_0001"],             # IDs del formato anterior (trazabilidad)
  "titulo": "La Confesión",
  "tipo": "ficha",                         # ver TIPOS
  "autoridad": {"nivel": 5, "descripcion": "..."},  # jerarquía de fuentes (1 = máxima)
  "etapas": [1],                           # [] si no corresponde a una etapa
  "idioma": "es",
  "temas": ["sacramentos", "..."],         # ver TEMAS
  "temas_origen": "automatico" | "manual",
  "nivel_escolar": ["1º de secundaria"],   # tal como aparece en el material (sistema MX)
  "calendario": {
      "ciclo_origen": "escolar_mexico",
      "mes_original": "octubre",
      "meses_originales": ["octubre"],
      "mes_argentino": "abril",
      "tiempo_liturgico": null | "cuaresma" | "navidad" | "cristo_rey" | "pascua"
  },
  "fuente": {
      "archivo": "La Confesión.pdf",
      "ruta": "E:\\ECyD\\...",
      "carpeta": "1ra etapa fichas/1era-etapa-etapa-octubre",
      "extension": ".pdf",
      "duplicados": [{"archivo": ..., "ruta": ..., "id_legacy": ...}]
  },
  "extraccion": {"metodo": "pypdf" | "ocr", "caracteres": 14929,
                 "calidad": "buena" | "media" | "baja", "sha1": "..."},
  "overrides": ["titulo"],                 # campos corregidos a mano (data/overrides.json)
  "texto": "..."
}
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import PureWindowsPath, PurePath
from typing import Any, Dict, Iterable, List, Optional

SCHEMA_VERSION = "2.0"

# ------------------------------------------------------------------
# Vocabularios controlados
# ------------------------------------------------------------------

TIPOS = {
    "documento_oficial": "Documento oficial (estatutos, estilo formativo)",
    "ensayo": "Ensayo del Regnum Christi / ECyD",
    "programa_territorial": "Programa territorial y guías de planificación",
    "retiro": "Material de retiros",
    "ficha": "Ficha de reunión por etapa",
    "guia": "Guía práctica",
    "formulario": "Formulario / registro",
    "otro": "Otro material",
}

# Jerarquía de fuentes del prompt formativo (1 = mayor autoridad)
AUTORIDAD = {
    1: "Estatutos del ECyD",
    2: "Documento que explica el estilo y camino formativo del ECyD",
    3: "Material oficial de etapas, itinerarios y espiritualidad",
    4: "Guía o material práctico",
    5: "Ficha o recurso concreto",
}

AUTORIDAD_POR_TIPO = {
    "documento_oficial": 2,
    "ensayo": 3,
    "programa_territorial": 4,
    "retiro": 4,
    "guia": 4,
    "ficha": 5,
    "formulario": 5,
    "otro": 5,
}

# Temas: palabras clave (sin tildes, en minúscula). Heurístico y corregible
# desde overrides.json.
TEMAS: Dict[str, Dict[str, Any]] = {
    "oracion": {"label": "Oración", "kw": ["oracion", "orar", "rezar", "rincon de la oracion", "hablar con jesus", "i pray"]},
    "sacramentos": {"label": "Sacramentos", "kw": ["confesion", "eucaristia", "misa", "sacramento", "reconciliacion", "comunion", "vida de gracia"]},
    "amistad_con_cristo": {"label": "Amistad con Cristo / Alianza", "kw": ["alianza", "amistad con cristo", "encuentro con cristo", "jesucristo", "cristo me ama"]},
    "identidad": {"label": "Identidad y autoconocimiento", "kw": ["quien soy", "identidad", "autoestima", "conocete", "interioridad", "autenticidad", "reconocerme", "me gusto", "que me pasa"]},
    "amistad": {"label": "Amistad", "kw": ["amigo", "amigos", "amistad", "amistades"]},
    "vida_de_equipo": {"label": "Vida de equipo", "kw": ["mi equipo", "vida de equipo", "equipo ecyd", "pertenencia", "sello ecyd"]},
    "afectividad": {"label": "Afectividad, amor y sexualidad", "kw": ["pureza", "sexualidad", "amor verdadero", "noviazgo", "afectividad", "lenguaje del cuerpo", "forma de amar", "amor chatarra", "homosexualidad", "castidad"]},
    "familia": {"label": "Familia", "kw": ["familia", "padres", "papas"]},
    "conciencia_virtudes": {"label": "Conciencia y virtudes", "kw": ["conciencia", "virtud", "voluntad", "fidelidad", "sinceridad", "mandamientos", "perdon", "excesos"]},
    "mision_apostolado": {"label": "Misión y apostolado", "kw": ["apostol", "apostolado", "mision", "evangeliz", "heroe"]},
    "fe_razones": {"label": "Fe y razones para creer", "kw": ["razones para creer", "razones de mi fe", "si dios es bueno", "creer", "sabana santa", "dios actua"]},
    "maria": {"label": "María", "kw": ["maria", "virgen"]},
    "tiempo_liturgico": {"label": "Tiempos litúrgicos", "kw": ["navidad", "cuaresma", "pascua", "cristo rey", "adviento", "viacrucis"]},
    "iglesia": {"label": "Iglesia", "kw": ["iglesia", "papa", "regnum christi"]},
    "tecnologia_redes": {"label": "Redes y tecnología", "kw": ["redes sociales", "redes", "celular", "internet", "pantalla"]},
    "emociones": {"label": "Emociones y salud interior", "kw": ["emociones", "sentimientos", "tristeza", "estar bien", "ansiedad", "soledad"]},
    "servicio_social": {"label": "Servicio y doctrina social", "kw": ["casa comun", "doctrina social", "dsi", "pobre", "servicio", "materialismo"]},
    "vocacion_sentido": {"label": "Vocación y sentido de vida", "kw": ["vocacion", "sentido de mi vida", "meta", "proyecto de vida", "llamado", "aqui estoy"]},
    "acompanamiento_formacion": {"label": "Acompañamiento y estilo formativo", "kw": ["responsable", "acompanar", "acompanamiento", "formacion", "convicciones", "formador"]},
    "retiros": {"label": "Retiros", "kw": ["retiro"]},
    "reino": {"label": "Reino de Cristo", "kw": ["reino", "venga tu reino"]},
}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_ABREV = {"ene": "enero", "feb": "febrero", "mar": "marzo", "abr": "abril",
               "may": "mayo", "jun": "junio", "jul": "julio", "ago": "agosto",
               "sep": "septiembre", "sept": "septiembre", "set": "septiembre",
               "oct": "octubre", "nov": "noviembre", "dic": "diciembre"}

# Las fichas siguen el ciclo escolar mexicano; equivalencia para Argentina.
MES_ARGENTINO = {
    "septiembre": "marzo", "octubre": "abril", "noviembre": "mayo",
    "diciembre": "junio", "enero": "julio_agosto", "febrero": "agosto_septiembre",
    "marzo": "septiembre", "abril": "octubre", "mayo": "noviembre", "junio": "diciembre",
}

LITURGICOS = [("cristo-rey", "cristo_rey"), ("cristo rey", "cristo_rey"),
              ("cuaresma", "cuaresma"), ("navidad", "navidad"), ("pascua", "pascua")]


# ------------------------------------------------------------------
# Normalización
# ------------------------------------------------------------------

def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def norm(text: str) -> str:
    """Minúsculas y sin tildes, para matching."""
    return strip_accents(text).lower()


def clean_text(text: str) -> str:
    """Limpieza conservadora del texto extraído (no altera contenido)."""
    if not text:
        return ""
    text = text.replace("\x00", " ").replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sha1(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def as_path(ruta: str) -> PurePath:
    return PureWindowsPath(ruta) if "\\" in (ruta or "") else PurePath(ruta or "")


# ------------------------------------------------------------------
# Detección de metadata
# ------------------------------------------------------------------

_ETAPA_PATTERNS = [
    (r"\b(1ra|1era|1a|primera)[ _-]?etapa", 1),
    (r"\b(2da|2a|segunda)[ _-]?etapa", 2),
    (r"\b(3ra|3era|3a|tercera)[ _-]?etapa", 3),
    (r"\b(4ta|4a|cuarta)[ _-]?etapa", 4),
    (r"final([1-4])etapa", None),
    (r"\b([1-4])etapa", None),
]


def detect_etapas(ruta: str) -> List[int]:
    name = norm(ruta)
    for pattern, etapa in _ETAPA_PATTERNS:
        m = re.search(pattern, name)
        if m:
            return [etapa if etapa else int(m.group(1))]
    return []


def detect_calendario(ruta: str) -> Dict[str, Any]:
    name = norm(ruta)
    liturgico = None
    for key, value in LITURGICOS:
        if key in name:
            liturgico = value
            break
    # meses en carpetas / nombres (orden de aparición)
    found: List[str] = []
    for m in re.finditer(r"[a-z]+", name):
        w = m.group(0)
        mes = w if w in MESES else None
        if mes and mes not in found:
            found.append(mes)
    if not found:
        # abreviaturas pegadas al inicio del nombre de archivo: "novUNREY", "oct. Dios"
        stem = norm(as_path(ruta).name)
        m = re.match(r"^(ene|feb|mar|abr|may|jun|jul|ago|sept|sep|set|oct|nov|dic)(?=[\.\sA-Z_-]|[a-z]*[A-Z])", stem)
        m2 = re.match(r"^(ene|feb|mar|abr|may|jun|jul|ago|sept|sep|set|oct|nov|dic)", as_path(ruta).name)
        if m2 and m:
            found.append(MESES_ABREV[m2.group(1).lower()])
    mes_original = found[0] if found else None
    return {
        "ciclo_origen": "escolar_mexico" if mes_original or liturgico else None,
        "mes_original": mes_original,
        "meses_originales": found,
        # Las festividades litúrgicas tienen prioridad sobre el mes.
        "mes_argentino": None if liturgico else MES_ARGENTINO.get(mes_original),
        "tiempo_liturgico": liturgico,
    }


def detect_tipo(ruta: str) -> str:
    name = norm(ruta)
    if "documentos oficiales" in name:
        return "documento_oficial"
    if "ensayos rc" in name:
        return "ensayo"
    if "retiros espirituales" in name:
        return "retiro"
    if "programa territorial" in name:
        return "programa_territorial"
    if "fichas" in name or "etapa" in name:
        return "ficha"
    return "otro"


def detect_idioma(archivo: str, texto: str = "") -> str:
    name = norm(archivo)
    if any(k in name for k in ["english", "pledge", "statutes"]):
        return "en"
    return "es"


def detect_nivel_escolar(texto: str) -> List[str]:
    found = []
    for m in re.finditer(r"([1-6])\s*[º°o]\s*de\s*(secundaria|preparatoria|primaria)", norm(texto[:4000])):
        val = f"{m.group(1)}º de {m.group(2)}"
        if val not in found:
            found.append(val)
    return found


def detect_temas(titulo: str, texto: str, max_temas: int = 4) -> List[str]:
    t_title = norm(titulo)
    t_body = norm(texto)
    size = max(len(t_body), 1)
    scores = {}
    for tema, cfg in TEMAS.items():
        s = 0.0
        for kw in cfg["kw"]:
            pat = r"\b" + re.escape(kw)
            if re.search(pat, t_title):
                s += 6
            s += len(re.findall(pat, t_body)) * 10000 / size / 4
        if s > 0:
            scores[tema] = s
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [t for t, s in ranked if s >= 2.5][:max_temas]


def calidad_extraccion(metodo: str, texto: str) -> str:
    if not texto or len(texto) < 500:
        return "baja"
    # proporción de "palabras raras" típica de OCR ruidoso
    words = re.findall(r"\w+", texto[:20000])
    if not words:
        return "baja"
    weird = sum(1 for w in words if re.search(r"\d", w) and re.search(r"[a-zA-Z]", w))
    ratio = weird / len(words)
    if metodo == "ocr":
        return "media" if ratio < 0.02 else "baja"
    return "buena" if ratio < 0.02 else "media"


_TITLE_PREFIX = re.compile(
    r"^((final)?\d?etapa[a-z]*|(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|nov|oct|dic|sept?)\.?)(?=[A-ZÁÉÍÓÚÑ ¿]|$)",
    re.IGNORECASE)


def clean_title(archivo: str) -> str:
    stem = as_path(archivo).stem if "." in archivo else archivo
    stem = re.sub(r"(\.docx|\.pdf)$", "", stem, flags=re.I)
    stem = re.sub(r"[._ ]?compressed$", "", stem, flags=re.I)
    stem = re.sub(r"\s*\(\d+\)\s*", " ", stem)
    stem = re.sub(r"\s+pdf$", "", stem, flags=re.I)
    stem = _TITLE_PREFIX.sub("", stem)
    stem = re.sub(r"[_ ]?[1-4](ra|da|era|ta)?[ _]etapa[ _]?", " ", stem, flags=re.I)
    stem = stem.replace("_", " ")
    stem = re.sub(r"\s+", " ", stem).strip(" -_.")
    return stem


def autoridad(nivel: int) -> Dict[str, Any]:
    return {"nivel": nivel, "descripcion": AUTORIDAD.get(nivel, "")}


def autoridad_para(tipo: str, titulo: str) -> int:
    t = norm(titulo)
    if "estatut" in t or "statutes" in t:
        return 1
    return AUTORIDAD_POR_TIPO.get(tipo, 5)


def carpeta_relativa(ruta: str, base_names: Iterable[str] = ("ECyD",)) -> str:
    parts = list(as_path(ruta).parts)
    for i, p in enumerate(parts):
        if p in base_names:
            return "/".join(parts[i + 1:-1])
    return "/".join(parts[-3:-1])


# ------------------------------------------------------------------
# Overrides
# ------------------------------------------------------------------

def load_overrides(path) -> Dict[str, Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("archivos", {})
    except FileNotFoundError:
        return {}


def apply_overrides(doc: Dict[str, Any], overrides: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    ov = overrides.get(doc["fuente"]["archivo"])
    if not ov:
        return doc
    applied = []
    for key, value in ov.items():
        if key == "autoridad_nivel":
            doc["autoridad"] = autoridad(int(value))
        elif key in ("mes_original", "tiempo_liturgico"):
            doc["calendario"][key] = value
        elif key == "temas":
            doc["temas"] = list(value)
            doc["temas_origen"] = "manual"
        else:
            doc[key] = value
        applied.append(key)
    if "tipo" in ov and "autoridad_nivel" not in ov:
        doc["autoridad"] = autoridad(autoridad_para(doc["tipo"], doc["titulo"]))
    doc["overrides"] = applied
    return doc


# ------------------------------------------------------------------
# Construcción de un documento v2
# ------------------------------------------------------------------

def build_document(*, doc_id: str, archivo: str, ruta: str, texto: str,
                   metodo: str, ids_legacy: Optional[List[str]] = None,
                   overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    texto = clean_text(texto)
    tipo = detect_tipo(ruta)
    titulo = clean_title(archivo) or as_path(archivo).stem
    doc = {
        "id": doc_id,
        "ids_legacy": ids_legacy or [],
        "titulo": titulo,
        "tipo": tipo,
        "autoridad": autoridad(autoridad_para(tipo, titulo)),
        "etapas": detect_etapas(ruta),
        "idioma": detect_idioma(archivo, texto),
        "temas": [],
        "temas_origen": "automatico",
        "nivel_escolar": detect_nivel_escolar(texto),
        "calendario": detect_calendario(ruta),
        "fuente": {
            "archivo": archivo,
            "ruta": ruta,
            "carpeta": carpeta_relativa(ruta),
            "extension": as_path(archivo).suffix.lower(),
            "duplicados": [],
        },
        "extraccion": {
            "metodo": metodo,
            "caracteres": len(texto),
            "calidad": calidad_extraccion(metodo, texto),
            "sha1": sha1(texto),
        },
        "overrides": [],
        "texto": texto,
    }
    if overrides:
        apply_overrides(doc, overrides)
    if doc["temas_origen"] == "automatico":
        doc["temas"] = detect_temas(doc["titulo"], texto)
    return doc


def merge_duplicates(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Unifica documentos con texto idéntico sin perder información:
    se suman etapas, rutas e IDs legacy al primero."""
    by_hash: Dict[str, Dict[str, Any]] = {}
    out = []
    for d in docs:
        h = d["extraccion"]["sha1"]
        if h in by_hash and d["texto"]:
            main = by_hash[h]
            for e in d["etapas"]:
                if e not in main["etapas"]:
                    main["etapas"].append(e)
            main["etapas"].sort()
            main["ids_legacy"] += [i for i in d["ids_legacy"] if i not in main["ids_legacy"]]
            main["fuente"]["duplicados"].append({
                "archivo": d["fuente"]["archivo"],
                "ruta": d["fuente"]["ruta"],
                "ids_legacy": d["ids_legacy"],
                "etapas": d["etapas"],
                "calendario": d["calendario"],
            })
            continue
        by_hash[h] = d
        out.append(d)
    return out


def corpus_stats(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    from collections import Counter
    return {
        "total_documentos": len(docs),
        "documentos_con_texto": sum(1 for d in docs if d["texto"]),
        "por_tipo": dict(Counter(d["tipo"] for d in docs)),
        "por_etapa": dict(Counter(str(e) for d in docs for e in (d["etapas"] or ["sin_etapa"]))),
        "por_idioma": dict(Counter(d["idioma"] for d in docs)),
        "por_calidad": dict(Counter(d["extraccion"]["calidad"] for d in docs)),
        "duplicados_unificados": sum(len(d["fuente"]["duplicados"]) for d in docs),
    }


def build_corpus(docs: List[Dict[str, Any]], origen: str) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "nombre": "Corpus ECyD",
        "generado": now_iso(),
        "origen": origen,
        "estadisticas": corpus_stats(docs),
        "vocabularios": {
            "tipos": TIPOS,
            "autoridad": {str(k): v for k, v in AUTORIDAD.items()},
            "temas": {k: v["label"] for k, v in TEMAS.items()},
        },
        "documentos": docs,
    }


def document_public(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Metadata del documento sin el texto completo."""
    d = {k: v for k, v in doc.items() if k != "texto"}
    d["resumen"] = re.sub(r"\s+", " ", doc.get("texto", ""))[:280]
    return d


# ------------------------------------------------------------------
# Chunking
# ------------------------------------------------------------------

def _paragraphs(text: str) -> List[str]:
    text = clean_text(text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)          # palabras cortadas por guión
    blocks = re.split(r"\n\s*\n", text)
    paras = []
    for b in blocks:
        lines = [l.strip() for l in b.split("\n") if l.strip()]
        if not lines:
            continue
        buf = lines[0]
        for l in lines[1:]:
            # une líneas cortadas (OCR / maquetación) salvo que parezca título o viñeta
            if re.match(r"^([-•·*]|\d+[.)]\s)", l) or (buf.endswith((".", "?", "!", ":")) and l[:1].isupper()):
                paras.append(buf)
                buf = l
            else:
                buf += " " + l
        paras.append(buf)
    return [re.sub(r"\s+", " ", p).strip() for p in paras if p.strip()]


def _split_long(p: str, max_chars: int) -> List[str]:
    if len(p) <= max_chars:
        return [p]
    sentences = re.split(r"(?<=[.!?;])\s+", p)
    out, buf = [], ""
    for s in sentences:
        while len(s) > max_chars:                      # frase gigante (OCR sin puntos)
            cut = s.rfind(" ", 0, max_chars)
            cut = cut if cut > max_chars // 2 else max_chars
            if buf:
                out.append(buf)
                buf = ""
            out.append(s[:cut].strip())
            s = s[cut:].strip()
        if len(buf) + len(s) + 1 > max_chars and buf:
            out.append(buf)
            buf = s
        else:
            buf = (buf + " " + s).strip()
    if buf:
        out.append(buf)
    return out


def chunk_text(text: str, target: int = 650, max_chars: int = 900, overlap: int = 120) -> List[str]:
    """Chunks por párrafos, ~target caracteres, con solapamiento.

    Tamaño elegido para el modelo de embeddings (máx. 128 tokens ≈ 500-650
    caracteres en español): chunks más largos se truncan al vectorizar y la
    parte final nunca se vuelve "buscable".
    """
    pieces: List[str] = []
    for p in _paragraphs(text):
        pieces.extend(_split_long(p, max_chars))
    chunks, buf = [], ""
    for piece in pieces:
        if buf and len(buf) + len(piece) + 1 > target:
            chunks.append(buf)
            tail = buf[-overlap:]
            cut = tail.find(" ")
            tail = tail[cut + 1:] if cut >= 0 else tail
            buf = (tail + " " + piece).strip() if overlap else piece
            if len(buf) > max_chars:
                buf = piece
        else:
            buf = (buf + " " + piece).strip()
    if buf.strip():
        chunks.append(buf)
    # funde restos muy cortos con el anterior
    merged: List[str] = []
    for c in chunks:
        if merged and len(c) < 120 and len(merged[-1]) + len(c) < max_chars + 150:
            merged[-1] = merged[-1] + " " + c
        else:
            merged.append(c)
    return merged


def embedding_text_for_chunk(titulo: str, texto: str) -> str:
    return f"{titulo}. {texto}"


def embedding_text_for_document(doc: Dict[str, Any]) -> str:
    etapas = ", ".join(f"etapa {e}" for e in doc.get("etapas", []))
    temas = ", ".join(TEMAS[t]["label"] for t in doc.get("temas", []) if t in TEMAS)
    return f"{doc['titulo']}. {TIPOS.get(doc['tipo'], '')}. {etapas}. {temas}"
