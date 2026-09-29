import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURACIÓN
# ============================================================

INDEX_PATH = Path("data/ecyd.index")
METADATA_PATH = Path("data/index_metadata.json")

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

TOP_K = 5


# ============================================================
# CARGAR MODELO
# ============================================================

print("🧠 Cargando modelo...")

model = SentenceTransformer(MODEL_NAME)

print("✅ Modelo cargado")


# ============================================================
# CARGAR ÍNDICE
# ============================================================

index = faiss.read_index(str(INDEX_PATH))

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    documentos = json.load(f)

print(f"📚 Documentos indexados: {len(documentos)}")
print(f"🔢 Vectores FAISS: {index.ntotal}")


# ============================================================
# FUNCIÓN DE BÚSQUEDA
# ============================================================

def buscar(consulta: str, top_k: int = TOP_K):

    embedding = model.encode(
        [consulta],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores, indices = index.search(embedding, top_k)

    resultados = []

    for score, idx in zip(scores[0], indices[0]):

        if idx < 0:
            continue

        doc = documentos[idx]

        resultados.append({
            "score": float(score),
            "id": doc["id"],
            "titulo": doc["titulo"],
            "tipo": doc["tipo"],
            "etapa": doc["etapa"],
            "mes_argentino": doc["mes_argentino"],
            "prioridad": doc["prioridad"],
            "texto": doc["texto"]
        })

    return resultados


# ============================================================
# INTERFAZ
# ============================================================

print("\n" + "=" * 70)
print("🔎 BUSCADOR SEMÁNTICO ECyD")
print("=" * 70)

print("\nEscribí una consulta.")
print("Escribí 'salir' para terminar.\n")


while True:

    consulta = input("🔎 Consulta: ").strip()

    if consulta.lower() in {"salir", "exit", "q"}:
        print("\n👋 Cerrando buscador...")
        break

    if not consulta:
        continue

    resultados = buscar(consulta)

    print("\n" + "-" * 70)
    print(f"📌 RESULTADOS PARA: {consulta}")
    print("-" * 70)

    for i, resultado in enumerate(resultados, start=1):

        print(f"""
#{i}
📄 {resultado['titulo']}
🆔 {resultado['id']}
📚 Tipo: {resultado['tipo']}
🎓 Etapa: {resultado['etapa']}
📅 Mes Argentina: {resultado['mes_argentino']}
⭐ Score: {resultado['score']:.4f}
""")

    print("-" * 70)