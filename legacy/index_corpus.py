import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURACIÓN
# ============================================================

CORPUS_PATH = Path("data/corpus.json")
INDEX_PATH = Path("data/ecyd.index")
METADATA_PATH = Path("data/index_metadata.json")

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


# ============================================================
# CARGAR CORPUS
# ============================================================

print("=" * 70)
print("🔎 INDEXACIÓN SEMÁNTICA DEL CORPUS ECyD")
print("=" * 70)

print("\n📂 Cargando corpus...")

with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    corpus = json.load(f)

documentos = corpus["documentos"]

print(f"   📚 Documentos encontrados: {len(documentos)}")


# ============================================================
# PREPARAR TEXTOS
# ============================================================

texts = []

for doc in documentos:
    texto = doc.get("texto", "").strip()

    if not texto:
        texto = doc.get("titulo", "")

    # Incluimos el título para darle más peso semántico
    texto_para_embedding = (
        f"TÍTULO: {doc['titulo']}\n"
        f"ETAPA: {doc.get('etapa', '')}\n"
        f"MES: {doc.get('mes_argentino', '')}\n"
        f"CONTENIDO:\n{texto}"
    )

    texts.append(texto_para_embedding)


# ============================================================
# CARGAR MODELO
# ============================================================

print("\n🧠 Cargando modelo:")
print(f"   {MODEL_NAME}")

model = SentenceTransformer(MODEL_NAME)

print("   ✅ Modelo cargado")


# ============================================================
# GENERAR EMBEDDINGS
# ============================================================

print("\n⚙️ Generando embeddings...")

embeddings = model.encode(
    texts,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)

print(f"\n   ✅ Embeddings generados")
print(f"   📐 Dimensión: {embeddings.shape}")


# ============================================================
# CREAR ÍNDICE FAISS
# ============================================================

dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

print("\n🗂️ Índice FAISS creado")
print(f"   Vectores almacenados: {index.ntotal}")
print(f"   Dimensión: {dimension}")


# ============================================================
# GUARDAR ÍNDICE
# ============================================================

faiss.write_index(index, str(INDEX_PATH))

print(f"\n💾 Índice guardado en:")
print(f"   {INDEX_PATH}")


# ============================================================
# GUARDAR METADATOS
# ============================================================

metadata = []

metadata = []

for doc in documentos:
    metadata.append({
        "id": doc["id"],
        "titulo": doc["titulo"],
        "archivo": doc["archivo"],
        "ruta": doc["ruta"],
        "tipo": doc["tipo"],
        "etapa": doc.get("etapa"),
        "mes_original": doc.get("mes_original"),
        "mes_argentino": doc.get("mes_argentino"),
        "prioridad": doc.get("prioridad"),
        "idioma": doc.get("idioma"),
        "metodo_extraccion": doc.get("metodo_extraccion"),
        "contenido": doc.get("texto", "")
    })

with open(METADATA_PATH, "w", encoding="utf-8") as f:
    json.dump(
        metadata,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"📄 Metadatos guardados en:")
print(f"   {METADATA_PATH}")


# ============================================================
# RESUMEN
# ============================================================

print("\n" + "=" * 70)
print("✅ INDEXACIÓN TERMINADA")
print("=" * 70)

print(f"""
📚 Documentos:       {len(documentos)}
🧠 Modelo:           {MODEL_NAME}
📐 Dimensión:        {dimension}
🔢 Vectores:         {index.ntotal}

💾 Archivos creados:
   • {INDEX_PATH}
   • {METADATA_PATH}
""")