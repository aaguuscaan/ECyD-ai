"""
Programa de cada etapa y temas por mes (datos en data/programas.json, armados
por scripts/build_programas.py a partir de los materiales reales).

El programa es una GUÍA para la IA y para el responsable, no una restricción.
"""

from __future__ import annotations

import json
import threading
from datetime import date, timedelta
from typing import Dict, List, Optional

from .config import settings

PERIODO_LABEL = {
    "marzo": "marzo", "abril": "abril", "mayo": "mayo", "junio": "junio",
    "julio_agosto": "julio/agosto", "agosto_septiembre": "agosto/septiembre",
    "septiembre": "septiembre", "octubre": "octubre", "noviembre": "noviembre",
    "diciembre": "diciembre",
}
LITURGICO_LABEL = {"cuaresma": "Cuaresma", "pascua": "Pascua", "cristo_rey": "Cristo Rey",
                   "navidad": "Navidad"}
MESES_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
            "septiembre", "octubre", "noviembre", "diciembre"]

# Mes calendario (Argentina) → períodos del programa que le corresponden
PERIODOS_POR_MES = {
    3: ["marzo"], 4: ["abril"], 5: ["mayo"], 6: ["junio"], 7: ["julio_agosto"],
    8: ["julio_agosto", "agosto_septiembre"], 9: ["agosto_septiembre", "septiembre"],
    10: ["octubre"], 11: ["noviembre"], 12: ["diciembre"], 1: [], 2: [],
}

_data: Optional[dict] = None
_lock = threading.Lock()


def load() -> dict:
    global _data
    with _lock:
        if _data is None:
            path = settings.data_dir / "programas.json"
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _data = json.load(f)
            except FileNotFoundError:
                _data = {"etapas": {}, "periodos": []}
    return _data


def etapa_info(etapa: Optional[int]) -> Optional[dict]:
    if not etapa:
        return None
    return load().get("etapas", {}).get(str(etapa))


# ------------------------------------------------------------------ calendario litúrgico
def easter(year: int) -> date:
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def tiempos_liturgicos(year: int) -> Dict[str, tuple]:
    pascua = easter(year)
    navidad = date(year, 12, 25)
    adviento = navidad - timedelta(days=navidad.weekday() + 1 + 21)  # 4º domingo antes de Navidad
    cristo_rey = adviento - timedelta(days=7)
    return {
        "cuaresma": (pascua - timedelta(days=46), pascua - timedelta(days=1)),
        "pascua": (pascua, pascua + timedelta(days=49)),
        "cristo_rey": (cristo_rey - timedelta(days=20), cristo_rey + timedelta(days=6)),
        "navidad": (adviento, date(year + 1, 1, 6)),
    }


def liturgico_activo(hoy: date, anticipacion: int = 14) -> Optional[dict]:
    """Tiempo litúrgico en curso o que empieza dentro de `anticipacion` días."""
    for year in (hoy.year - 1, hoy.year):
        for key, (desde, hasta) in tiempos_liturgicos(year).items():
            if desde - timedelta(days=anticipacion) <= hoy <= hasta:
                return {"clave": key, "nombre": LITURGICO_LABEL[key], "desde": desde.isoformat(),
                        "hasta": hasta.isoformat(), "en_curso": desde <= hoy}
    return None


# ------------------------------------------------------------------ sugerencias
def _fichas_de(info: dict, periodos: List[str]) -> List[dict]:
    out, seen = [], set()
    for p in info.get("calendario", []):
        if p["periodo"] in periodos:
            for f in p["fichas"]:
                if f["doc_id"] not in seen:
                    seen.add(f["doc_id"])
                    out.append({**f, "periodo": p["periodo"]})
    return out


def sugerencias(etapa: Optional[int], hoy: Optional[date] = None) -> dict:
    """Qué propone el programa para esta etapa en este momento del año."""
    hoy = hoy or date.today()
    info = etapa_info(etapa)
    data = load()
    res = {"fecha": hoy.isoformat(), "mes": MESES_ES[hoy.month], "etapa": etapa,
           "fuente": data.get("fuente"), "nota_calendario": data.get("nota_calendario")}
    if not info:
        res["disponible"] = False
        return res
    periodos = PERIODOS_POR_MES.get(hoy.month, [])
    receso = not periodos
    if receso:  # enero/febrero: receso; se muestra lo que viene en marzo
        periodos = ["marzo"]
    actuales = _fichas_de(info, periodos)
    orden = data.get("periodos", [])
    proximo = None
    if periodos and periodos[-1] in orden:
        i = orden.index(periodos[-1])
        for p in orden[i + 1:]:
            fichas = _fichas_de(info, [p])
            if fichas:
                proximo = {"periodo": p, "label": PERIODO_LABEL.get(p, p), "fichas": fichas}
                break
    lit = liturgico_activo(hoy)
    if lit:
        lit["fichas"] = next((t["fichas"] for t in info.get("tiempos_liturgicos", [])
                              if t["tiempo_liturgico"] == lit["clave"]), [])
    res.update({
        "disponible": True,
        "nombre": info["nombre"], "edades": info["edades"],
        "nivel_escolar_mexico": info.get("nivel_escolar_mexico", []),
        "resumen": info["resumen"], "temas_centrales": info.get("temas_centrales", ""),
        "necesidades": info.get("necesidades", []),
        "receso": receso,
        "periodos": [{"periodo": p, "label": PERIODO_LABEL.get(p, p)} for p in periodos],
        "fichas": actuales, "proximo": proximo, "liturgico": lit,
    })
    return res


def contexto_programa(etapa: Optional[int], hoy: Optional[date] = None, detallado: bool = False) -> str:
    """Bloque de texto con el programa de la etapa para el prompt de la IA."""
    s = sugerencias(etapa, hoy)
    if not s.get("disponible"):
        return ("No hay etapa definida para este equipo: no se puede ubicar la consulta en el programa. "
                "Si es relevante, preguntá la etapa.")
    r = s["resumen"]
    fuente = (s.get("fuente") or {}).get("titulo", "Formando apóstoles en el ECyD")
    lines = [
        f"Programa de la {s['nombre']} ({s['edades']}) — fuente: {fuente}, Tomo III.",
        f"- Temas centrales: {_short(s.get('temas_centrales'), 420)}",
        f"- Alianza: {_short(r.get('alianza'), 260)}",
        f"- Amor: {r.get('amor')} · Virtud: {r.get('virtud')}",
        f"- Símbolo: {_short(r.get('simbolo'), 160)}",
    ]
    if detallado and s.get("necesidades"):
        lines.append("- Necesidades: " + "; ".join(s["necesidades"][:6]))
    per = ", ".join(p["label"] for p in s["periodos"])
    if s.get("receso"):
        lines.append(f"- Hoy es {s['mes']}: receso en el ciclo argentino; el programa retoma en marzo.")
    fichas = "; ".join(f"«{f['titulo']}»" for f in s["fichas"]) or "(no hay fichas asignadas a este período)"
    lines.append(f"- Fichas previstas para {per} (mes actual: {s['mes']}): {fichas}")
    if s.get("proximo"):
        lines.append(f"- Próximo período ({s['proximo']['label']}): "
                     + "; ".join(f"«{f['titulo']}»" for f in s["proximo"]["fichas"]))
    lit = s.get("liturgico")
    if lit:
        estado = "en curso" if lit["en_curso"] else "se acerca"
        fl = "; ".join(f"«{f['titulo']}»" for f in lit.get("fichas", [])) or "sin ficha específica"
        lines.append(f"- Tiempo litúrgico ({estado}): {lit['nombre']} — ficha de la etapa: {fl}")
    lines.append("(Los temas por mes salen de la organización de las fichas por mes en los materiales.)")
    return "\n".join(lines)


def _short(text: Optional[str], n: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


def ficha_en_programa(etapa: Optional[int], doc_id: str) -> Optional[dict]:
    """Dónde aparece una ficha en el programa de la etapa (período o tiempo litúrgico)."""
    info = etapa_info(etapa)
    if not info:
        return None
    for p in info.get("calendario", []):
        if any(f["doc_id"] == doc_id for f in p["fichas"]):
            return {"periodo": p["periodo"], "label": PERIODO_LABEL.get(p["periodo"], p["periodo"])}
    for t in info.get("tiempos_liturgicos", []):
        if any(f["doc_id"] == doc_id for f in t["fichas"]):
            return {"tiempo_liturgico": t["tiempo_liturgico"],
                    "label": LITURGICO_LABEL.get(t["tiempo_liturgico"], t["tiempo_liturgico"])}
    return None
