"""
Exporta un encuentro a PDF con la identidad del ECyD.

Convierte el markdown de la propuesta (el mismo que muestra la web) en
párrafos, títulos, listas y tablas de ReportLab. Usa Helvetica (incluida en
todo lector de PDF, sin descargar fuentes) y el rojo institucional
Pantone 187 (#AC0D2E) del Manual de imagen ECyD.
"""

from __future__ import annotations

import io
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (Flowable, KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROJO = colors.HexColor("#AC0D2E")      # Pantone 187
ROJO_TINTE = colors.HexColor("#F7E9EC")
TINTA = colors.HexColor("#231F20")
GRIS = colors.HexColor("#6B6164")
BORDE = colors.HexColor("#E4D7D9")
AVISO_BG = colors.HexColor("#FFF4E0")
AVISO_TX = colors.HexColor("#7A4E00")
CRUZ = Path(__file__).parent / "assets" / "cruz-ecyd.png"

ESTADOS = {"borrador": "Borrador", "planificado": "Planificado", "realizado": "Realizado"}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre"]

# ------------------------------------------------------------------ estilos
_base = dict(fontName="Helvetica", textColor=TINTA, alignment=TA_LEFT)
ST = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=21, leading=25, textColor=ROJO, spaceAfter=4),
    "meta": ParagraphStyle("meta", **{**_base, "fontSize": 9, "leading": 12, "textColor": GRIS}),
    "body": ParagraphStyle("body", **{**_base, "fontSize": 10.5, "leading": 15, "spaceAfter": 5}),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=ROJO, spaceBefore=10, spaceAfter=4),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=ROJO, spaceBefore=10, spaceAfter=3),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=TINTA, spaceBefore=8, spaceAfter=2),
    "quote": ParagraphStyle("quote", **{**_base, "fontName": "Helvetica-Oblique", "fontSize": 10.5, "leading": 15,
                                        "textColor": colors.HexColor("#4A4345"), "leftIndent": 10}),
    "li": ParagraphStyle("li", **{**_base, "fontSize": 10.5, "leading": 14.5}),
    "cell": ParagraphStyle("cell", **{**_base, "fontSize": 9, "leading": 12}),
    "cellh": ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=ROJO),
    "small": ParagraphStyle("small", **{**_base, "fontSize": 8.5, "leading": 11.5, "textColor": GRIS}),
    "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=GRIS,
                              spaceBefore=14, spaceAfter=5),
    "aviso": ParagraphStyle("aviso", **{**_base, "fontSize": 9.5, "leading": 13, "textColor": AVISO_TX}),
}

# ------------------------------------------------------------------ texto
_REEMPLAZOS = {"→": "->", "←": "<-", "✓": "", "✔": "", "⚠": "Atención:", "️": "", "≈": "~", "≥": ">=", "≤": "<=",
               " ": " ", "​": "", " ": " ", " ": " "}


def limpiar(text: str) -> str:
    """Helvetica (WinAnsi) cubre español y tipografía usual; el resto se reemplaza o se omite."""
    out = []
    for ch in unicodedata.normalize("NFC", str(text or "")):
        if ch in _REEMPLAZOS:
            out.append(_REEMPLAZOS[ch])
            continue
        try:
            ch.encode("cp1252")
            out.append(ch)
        except UnicodeEncodeError:
            base = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode()
            out.append(base)
    return "".join(out)


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s: str) -> str:
    """Markdown en línea → mini-HTML de ReportLab."""
    s = _esc(limpiar(s))
    s = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', s)
    s = re.sub(r"\*\*F(\d{1,2})\*\*|\[F(\d{1,2})\]|\(F(\d{1,2})\)",
               lambda m: f'<font size="7" color="#AC0D2E"><super>F{m.group(1) or m.group(2) or m.group(3)}</super></font>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"__([^_]+)__", r"<b>\1</b>", s)
    s = re.sub(r"(^|[^*\w])\*([^*\n]+)\*(?!\w)", r"\1<i>\2</i>", s)
    s = re.sub(r"(^|\W)_([^_\n]+)_(?=\W|$)", r"\1<i>\2</i>", s)
    return s


# ------------------------------------------------------------------ bloques
_LIST = re.compile(r"^(\s*)([-*•]|\d+[.)])\s+(.*)$")
_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


class Linea(Flowable):
    def __init__(self, width=None, color=BORDE, thickness=0.8, space=6):
        super().__init__()
        self.w, self.color, self.t, self.space = width, color, thickness, space

    def wrap(self, aw, ah):
        self.width = self.w or aw
        return self.width, self.space * 2

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.t)
        self.canv.line(0, self.space, self.width, self.space)


def _lista(items: List[tuple], ordered: bool) -> ListFlowable:
    """items: (nivel, texto). Soporta un nivel de anidado."""
    flow, i = [], 0
    while i < len(items):
        lvl, txt = items[i]
        sub = []
        j = i + 1
        while j < len(items) and items[j][0] > lvl:
            sub.append(items[j])
            j += 1
        content = [Paragraph(inline(txt), ST["li"])]
        if sub:
            content.append(_lista([(0, t) for _, t in sub], False))
        flow.append(ListItem(content, leftIndent=14, value=None))
        i = j
    kw = dict(bulletType="1", bulletFormat="%s.", bulletFontSize=10, bulletColor=ROJO) if ordered else \
        dict(bulletType="bullet", start="•", bulletFontSize=9, bulletColor=ROJO)
    return ListFlowable(flow, leftIndent=14, spaceBefore=1, spaceAfter=5, **kw)


def markdown_flowables(src: str, width: float) -> list:
    lines = str(src or "").replace("\r", "").split("\n")
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if not l.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", l)
        if m:
            lvl = len(m.group(1))
            out.append(Paragraph(inline(m.group(2)), ST["h1" if lvl == 1 else "h2" if lvl == 2 else "h3"]))
            i += 1
            continue
        if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", l):
            out.append(Linea())
            i += 1
            continue
        if re.match(r"^\s*>", l):
            buf = []
            while i < len(lines) and re.match(r"^\s*>", lines[i]):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            t = Table([[Paragraph(inline(" ".join(buf)), ST["quote"])]], colWidths=[width])
            t.setStyle(TableStyle([("LINEBEFORE", (0, 0), (0, -1), 2.2, ROJO), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                   ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            out += [t, Spacer(1, 5)]
            continue
        if "|" in l and i + 1 < len(lines) and _SEP.match(lines[i + 1]):
            row = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
            head = row(l)
            body = []
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                body.append(row(lines[i]))
                i += 1
            n = len(head)
            data = [[Paragraph(inline(c), ST["cellh"]) for c in head]] + \
                   [[Paragraph(inline(c), ST["cell"]) for c in (r + [""] * n)[:n]] for r in body]
            t = Table(data, colWidths=[width / n] * n, repeatRows=1)
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ROJO_TINTE), ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
            out += [t, Spacer(1, 6)]
            continue
        if _LIST.match(l):
            ordered = bool(re.match(r"^\s*\d", l))
            items = []
            while i < len(lines):
                mm_ = _LIST.match(lines[i])
                if mm_:
                    items.append((1 if len(mm_.group(1).expandtabs(4)) >= 2 else 0, mm_.group(3)))
                elif lines[i].strip() and re.match(r"^\s{2,}\S", lines[i]) and items:
                    lvl, t = items[-1]
                    items[-1] = (lvl, t + " " + lines[i].strip())
                else:
                    break
                i += 1
            out.append(_lista(items, ordered))
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,6}\s|\s*>|\s*([-*•]|\d+[.)])\s+|\s*(-{3,}|\*{3,})\s*$)", lines[i]):
            buf.append(lines[i])
            i += 1
        if not buf:
            buf.append(lines[i])
            i += 1
        out.append(Paragraph("<br/>".join(inline(b) for b in buf), ST["body"]))
    return out


# ------------------------------------------------------------------ documento
def _fecha_larga(iso: Optional[str]) -> str:
    try:
        d = date.fromisoformat(str(iso)[:10])
        return f"{d.day} de {MESES[d.month - 1]} de {d.year}"
    except (TypeError, ValueError):
        return ""


def nombre_archivo(enc: Dict) -> str:
    base = unicodedata.normalize("NFKD", enc.get("titulo") or "encuentro").encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower()[:60] or "encuentro"
    return f"{(enc.get('fecha') or '')[:10]}-{base}".strip("-") + ".pdf"


def encuentro_pdf(enc: Dict, *, equipo: str = "", incluir_observaciones: bool = True) -> bytes:
    buf = io.BytesIO()
    margin = 18 * mm
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=24 * mm,
                            bottomMargin=20 * mm, title=limpiar(enc.get("titulo") or "Encuentro"),
                            author="Asistente ECyD", subject="Propuesta de encuentro", creator="Asistente ECyD")
    width = A4[0] - 2 * margin
    fecha = _fecha_larga(enc.get("fecha"))
    titulo = limpiar(enc.get("titulo") or "Encuentro")

    def deco(canvas, d):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(ROJO)
        canvas.rect(0, h - 5, w, 5, stroke=0, fill=1)                       # franja superior
        if CRUZ.exists():                                                    # cruz con su proporción original
            ch = 11 * mm
            canvas.drawImage(str(CRUZ), margin, h - 8 * mm - ch, width=ch * 552 / 744, height=ch, mask="auto")
        canvas.setFillColor(TINTA)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(margin + 10 * mm, h - 13.5 * mm, "ECyD")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GRIS)
        canvas.drawString(margin + 10 * mm, h - 17 * mm, "Propuesta de encuentro")
        right = " · ".join(x for x in [limpiar(equipo), fecha] if x)
        canvas.drawRightString(w - margin, h - 13.5 * mm, right[:90])
        canvas.setStrokeColor(BORDE)
        canvas.line(margin, 14 * mm, w - margin, 14 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(margin, 10 * mm, "Generado con el Asistente ECyD a partir de los documentos del ECyD. "
                                            "Es una propuesta: adaptala a tu grupo.")
        canvas.drawRightString(w - margin, 10 * mm, f"Página {d.page}")
        canvas.restoreState()

    story: list = [Paragraph(_esc(titulo), ST["title"])]
    meta = [x for x in [
        limpiar(equipo),
        f"Etapa {enc['etapa']}" if enc.get("etapa") else "",
        fecha,
        limpiar(enc.get("duracion") or ""),
        f"{enc['cantidad']} chicos" if enc.get("cantidad") else "",
        limpiar((enc.get("composicion") or "").capitalize()),
        ESTADOS.get(enc.get("estado") or "", ""),
    ] if x]
    if meta:
        story.append(Paragraph(_esc("  ·  ".join(meta)), ST["meta"]))
    filas = []
    if enc.get("tema"):
        filas.append(["Tema", enc["tema"] + ("  (sugerido por el programa)" if enc.get("origen_tema") == "programa" else "")])
    if enc.get("fichas"):
        filas.append(["Fichas", " · ".join(f.get("titulo", "") for f in enc["fichas"])])
    if filas:
        t = Table([[Paragraph(f"<b>{k}</b>", ST["cell"]), Paragraph(_esc(limpiar(v)), ST["cell"])] for k, v in filas],
                  colWidths=[22 * mm, width - 22 * mm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ROJO_TINTE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                               ("LEFTPADDING", (0, 0), (-1, -1), 7)]))
        story += [Spacer(1, 6), t]
    aviso = (enc.get("meta") or {}).get("aviso")
    if aviso:
        t = Table([[Paragraph(_esc(limpiar(aviso)), ST["aviso"])]], colWidths=[width])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), AVISO_BG), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        story += [Spacer(1, 6), t]
    story.append(Linea(space=7))

    propuesta = enc.get("propuesta") or "_Todavía no hay propuesta._"
    # el título ya está arriba: no repetir la primera línea "# título"
    propuesta = re.sub(r"^\s*#\s+.+\n?", "", propuesta, count=1)
    story += markdown_flowables(propuesta, width)

    obs = (enc.get("observaciones") or "").strip()
    if incluir_observaciones and obs:
        story.append(KeepTogether([Paragraph("OBSERVACIONES", ST["section"]),
                                   Paragraph("<br/>".join(_esc(limpiar(x)) for x in obs.split("\n")), ST["body"])]))

    fuentes = (enc.get("meta") or {}).get("sources") or []
    citadas = [f for f in fuentes if f.get("citada")] or fuentes[:4]
    if citadas:
        story.append(Paragraph("FUENTES DEL ECyD", ST["section"]))
        for f in citadas:
            et = f.get("etapas") or []
            det = " · ".join(x for x in [f"Etapa {' y '.join(map(str, et))}" if et else "General"] if x)
            story.append(Paragraph(f'<font color="#AC0D2E"><b>F{f.get("n")}</b></font>  '
                                   f'{_esc(limpiar(f.get("titulo", "")))} <font color="#6B6164">({det})</font>',
                                   ST["small"]))

    doc.build(story, onFirstPage=deco, onLaterPages=deco)
    return buf.getvalue()
