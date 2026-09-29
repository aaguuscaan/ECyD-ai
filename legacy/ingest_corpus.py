import os
import re
import json
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF
from pypdf import PdfReader


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(r"E:\ECyD")
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "corpus.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\x00", " ")

    # Normalizar Unicode
    text = unicodedata.normalize("NFC", text)

    # Espacios repetidos
    text = re.sub(r"[ \t]+", " ", text)

    # Demasiados saltos de línea
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_for_matching(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )

    return text.lower()


# ============================================================
# METADATOS
# ============================================================

MESES = {
    "enero": "enero",
    "febrero": "febrero",
    "marzo": "marzo",
    "abril": "abril",
    "mayo": "mayo",
    "junio": "junio",
    "julio": "julio",
    "agosto": "agosto",
    "septiembre": "septiembre",
    "setiembre": "septiembre",
    "octubre": "octubre",
    "noviembre": "noviembre",
    "diciembre": "diciembre",
}


def detectar_etapa(path: Path):
    nombre = normalize_for_matching(str(path))

    patrones = [
        (r"1ra etapa", 1),
        (r"1era etapa", 1),
        (r"primera etapa", 1),

        (r"2da etapa", 2),
        (r"2da-etapa", 2),
        (r"segunda etapa", 2),

        (r"3ra etapa", 3),
        (r"3ra-etapa", 3),
        (r"tercera etapa", 3),

        (r"4ta etapa", 4),
        (r"4ta-etapa", 4),
        (r"cuarta etapa", 4),
    ]

    for patron, etapa in patrones:
        if re.search(patron, nombre):
            return etapa

    return None


def detectar_mes(path: Path):
    nombre = normalize_for_matching(str(path))

    # Prioridad litúrgica
    if "cristo-rey" in nombre or "cristo rey" in nombre:
        return "cristo_rey", "cristo_rey"

    if "cuaresma" in nombre:
        return "cuaresma", "cuaresma"

    if "navidad" in nombre:
        return "navidad", "navidad"

    # Meses
    for clave, mes in MESES.items():
        if re.search(rf"\b{clave}\b", nombre):
            return mes, None

    return None, None


def detectar_mes_argentino(mes_original, prioridad):
    """
    Las fichas fueron creadas siguiendo el ciclo escolar mexicano.

    Para Argentina:
        septiembre -> marzo
        octubre    -> abril
        noviembre  -> mayo
        diciembre  -> junio
        enero      -> julio/agosto
        febrero    -> agosto/septiembre
        marzo      -> septiembre
        abril      -> octubre
        mayo       -> noviembre
        junio      -> diciembre

    Pero las festividades litúrgicas tienen prioridad.
    """

    if prioridad:
        return None

    equivalencia = {
        "septiembre": "marzo",
        "octubre": "abril",
        "noviembre": "mayo",
        "diciembre": "junio",

        "enero": "julio_agosto",
        "febrero": "agosto_septiembre",

        "marzo": "septiembre",
        "abril": "octubre",
        "mayo": "noviembre",
        "junio": "diciembre",
    }

    return equivalencia.get(mes_original)


def detectar_tipo(path: Path):
    nombre = normalize_for_matching(str(path))

    if "documentos oficiales" in nombre:
        return "documento_oficial"

    if "ensayos rc" in nombre:
        return "ensayo"

    if "retiros espirituales" in nombre:
        return "retiro"

    if "programa territorial" in nombre:
        return "programa_territorial"

    if "fichas" in nombre or "etapa" in nombre:
        return "ficha"

    return "otro"


# ============================================================
# TÍTULO
# ============================================================

def limpiar_titulo(nombre):
    nombre = Path(nombre).stem

    # Quitar nombres técnicos de compresión
    nombre = re.sub(
        r"\.compressed$",
        "",
        nombre,
        flags=re.IGNORECASE
    )

    # Quitar prefijos del tipo:
    # marzo
    # abril
    # FINAL2ETAPA
    # etc.
    nombre = re.sub(
        r"^(final)?\d*etapa[a-z]*",
        "",
        nombre,
        flags=re.IGNORECASE
    )

    nombre = re.sub(
        r"^(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
        "",
        nombre,
        flags=re.IGNORECASE
    )

    nombre = nombre.replace("_", " ")

    nombre = re.sub(r"\s+", " ", nombre)

    return nombre.strip(" -_")


# ============================================================
# EXTRACCIÓN NORMAL
# ============================================================

def extraer_texto_pypdf(path: Path):
    try:
        reader = PdfReader(str(path))

        paginas = []

        for page in reader.pages:
            try:
                text = page.extract_text()

                if text:
                    paginas.append(text)
            except Exception:
                continue

        texto = "\n\n".join(paginas)

        return normalize_text(texto)

    except Exception as e:
        print(f"   ⚠️ Error pypdf: {e}")
        return ""


# ============================================================
# OCR
# ============================================================

def buscar_tesseract():
    posibles = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for ruta in posibles:
        if os.path.exists(ruta):
            return ruta

    return None


def extraer_texto_ocr(path: Path):
    try:
        import pytesseract
        from PIL import Image

    except ImportError:
        print("   ❌ Falta pytesseract/Pillow.")
        return ""

    tesseract_path = buscar_tesseract()

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    try:
        documento = fitz.open(str(path))

        paginas = []

        total_paginas = len(documento)

        for numero, pagina in enumerate(documento, start=1):

            print(
                f"      🔍 OCR página {numero}/{total_paginas}...",
                end="\r"
            )

            # Renderizamos a una resolución suficiente
            pix = pagina.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                alpha=False
            )

            imagen = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            texto = pytesseract.image_to_string(
                imagen,
                lang="spa+eng"
            )

            if texto:
                paginas.append(texto)

        print(" " * 60, end="\r")

        documento.close()

        texto_final = "\n\n".join(paginas)

        return normalize_text(texto_final)

    except Exception as e:
        print(f"   ❌ Error OCR: {e}")
        return ""


# ============================================================
# PROCESAMIENTO DE DOCUMENTO
# ============================================================

def procesar_documento(path: Path):

    print(f"📄 Procesando: {path}")

    # --------------------------------------------------------
    # 1. Intentar extracción normal
    # --------------------------------------------------------

    texto = extraer_texto_pypdf(path)

    metodo_extraccion = "pypdf"

    # --------------------------------------------------------
    # 2. Si no hay texto -> OCR
    # --------------------------------------------------------

    if len(texto.strip()) < 100:

        print("   ⚠️ Poco o ningún texto. Intentando OCR...")

        texto = extraer_texto_ocr(path)

        if texto:
            metodo_extraccion = "ocr"

    # --------------------------------------------------------
    # 3. Metadatos
    # --------------------------------------------------------

    tipo = detectar_tipo(path)

    etapa = detectar_etapa(path)

    mes_original, prioridad = detectar_mes(path)

    mes_argentino = detectar_mes_argentino(
        mes_original,
        prioridad
    )

    titulo = limpiar_titulo(path.name)

    # --------------------------------------------------------
    # 4. Resultado
    # --------------------------------------------------------

    if texto:

        print(
            f"   ✅ {tipo} | "
            f"etapa={etapa} | "
            f"mes={mes_original} | "
            f"mes_AR={mes_argentino} | "
            f"prioridad={prioridad} | "
            f"extracción={metodo_extraccion}"
        )

    else:

        print(
            f"   ❌ NO SE PUDO EXTRAER TEXTO"
        )

    return {
        "id": None,
        "titulo": titulo,
        "archivo": path.name,
        "ruta": str(path),

        "tipo": tipo,

        "etapa": etapa,

        "mes_original": mes_original,
        "mes_argentino": mes_argentino,

        "prioridad": prioridad,

        "idioma": (
            "ingles"
            if "english" in normalize_for_matching(path.name)
            or "pledge" in normalize_for_matching(path.name)
            or "statutes" in normalize_for_matching(path.name)
            else "espanol"
        ),

        "metodo_extraccion": metodo_extraccion,

        "texto": texto,

        "texto_disponible": bool(texto),
    }


# ============================================================
# BUSCAR ARCHIVOS
# ============================================================

def buscar_archivos():

    extensiones = {
        ".pdf",
        ".docx",
    }

    archivos = []

    for path in BASE_DIR.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in extensiones:
            continue

        archivos.append(path)

    return sorted(archivos)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("🚀 INGESTA DEL CORPUS ECyD")
    print("=" * 70)

    print()
    print("📂 Carpeta origen:")
    print(f"   {BASE_DIR}")

    archivos = buscar_archivos()

    print()
    print(f"🔎 Archivos encontrados: {len(archivos)}")
    print()

    documentos = []

    for path in archivos:

        documento = procesar_documento(path)

        if documento["texto_disponible"]:

            documento["id"] = f"doc_{len(documentos) + 1:04d}"

            documentos.append(documento)

        else:

            # También guardamos los documentos fallidos.
            documento["id"] = f"doc_{len(documentos) + 1:04d}"

            documentos.append(documento)

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    total = len(documentos)

    ok = sum(
        1
        for d in documentos
        if d["texto_disponible"]
    )

    empty = total - ok

    tipos = {}

    for documento in documentos:

        tipo = documento["tipo"]

        tipos[tipo] = tipos.get(tipo, 0) + 1

    # ========================================================
    # GUARDAR
    # ========================================================

    corpus = {
        "metadata": {
            "nombre": "Corpus ECyD",
            "version": "1.0",
            "total_documentos": total,
            "documentos_con_texto": ok,
            "documentos_sin_texto": empty,
        },

        "documentos": documentos,
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            corpus,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ========================================================
    # RESUMEN
    # ========================================================

    print()
    print("=" * 70)
    print("✅ INGESTA TERMINADA")
    print("=" * 70)

    print()
    print(f"📚 Documentos procesados: {total}")

    print()
    print("📊 Estadísticas:")

    print(f"   total: {total}")
    print(f"   ok: {ok}")
    print(f"   empty: {empty}")

    for tipo, cantidad in sorted(tipos.items()):
        print(f"   {tipo}: {cantidad}")

    print()
    print("💾 Corpus guardado en:")
    print(f"   {OUTPUT_FILE}")

    print()

    if empty > 0:

        print("⚠️ ATENCIÓN")
        print(
            f"   Todavía quedaron {empty} documentos "
            "sin texto."
        )

        print()
        print(
            "   Esto puede deberse a que necesitan OCR, "
            "a que Tesseract no está instalado o a que "
            "el PDF está dañado."
        )

    else:

        print(
            "🎉 ¡Todos los documentos tienen texto!"
        )


if __name__ == "__main__":
    main()