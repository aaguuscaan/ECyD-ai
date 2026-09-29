# ================================================================
# 🤖 ASISTENTE ECyD - RAG FORMATIVO
# ================================================================
#
# RAG especializado en el estilo formativo del ECyD.
#
# Arquitectura:
#
#   DOCUMENTOS ECyD
#          ↓
#   FAISS DOCUMENTOS
#          ↓
#   RECUPERACIÓN INICIAL
#          ↓
#   FAISS CHUNKS
#          ↓
#   RECUPERACIÓN FINA
#          ↓
#   CONTEXTO DINÁMICO DEL EQUIPO
#          ↓
#   PROMPT FORMATIVO ECyD
#          ↓
#   GROQ / GEMINI
#          ↓
#   RESPUESTA AL RESPONSABLE
#
# ================================================================

import os
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import faiss

from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from google import genai
from google.genai import types

from openai import OpenAI


# ================================================================
# CARGAR VARIABLES DE ENTORNO
# ================================================================

load_dotenv()


# ================================================================
# CONFIGURACIÓN GENERAL
# ================================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# ================================================================
# CONFIGURACIÓN DEL LLM
# ================================================================

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "gemini"
).strip().lower()


# ------------------------------------------------
# API KEYS
# ------------------------------------------------

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


# ------------------------------------------------
# MODELOS
# ------------------------------------------------

GEMINI_MODEL = "gemini-3.6-flash"

GROQ_MODEL = "llama-3.3-70b-versatile"


# ------------------------------------------------
# CLIENTES
# ------------------------------------------------

gemini_client = None
groq_client = None


if LLM_PROVIDER == "gemini":

    if not GEMINI_API_KEY:

        raise RuntimeError(
            "\n❌ No se encontró GEMINI_API_KEY.\n\n"
            "Configurá tu .env con:\n"
            "LLM_PROVIDER=gemini\n"
            "GEMINI_API_KEY=tu_api_key\n"
        )

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


elif LLM_PROVIDER == "groq":

    if not GROQ_API_KEY:

        raise RuntimeError(
            "\n❌ No se encontró GROQ_API_KEY.\n\n"
            "Configurá tu .env con:\n"
            "LLM_PROVIDER=groq\n"
            "GROQ_API_KEY=tu_api_key\n"
        )

    groq_client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )


else:

    raise RuntimeError(
        f"\n❌ Proveedor LLM desconocido: "
        f"{LLM_PROVIDER}\n\n"
        "Usá una de estas opciones:\n\n"
        "LLM_PROVIDER=groq\n"
        "o\n"
        "LLM_PROVIDER=gemini\n"
    )


# ================================================================
# EMBEDDINGS
# ================================================================

EMBEDDING_MODEL_NAME = (
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ================================================================
# ARCHIVOS
# ================================================================
#
# IMPORTANTE:
#
# Estos son los nombres reales que existen actualmente
# en E:\ECyD-IA\data
#
# ================================================================

FAISS_DOCUMENTS_PATH = (
    DATA_DIR / "ecyd.index"
)

DOCUMENT_METADATA_PATH = (
    DATA_DIR / "index_metadata.json"
)

CHUNKS_INDEX_PATH = (
    DATA_DIR / "chunks.index"
)

CHUNKS_METADATA_PATH = (
    DATA_DIR / "chunks_metadata.json"
)


# ================================================================
# CONFIGURACIÓN DE RECUPERACIÓN
# ================================================================

TOP_K_DOCUMENTS = 5

CHUNKS_CANDIDATES = 40

TOP_K_CHUNKS = 8

CHUNK_SIZE = 1600

MAX_CONTEXT_CHARS = 9000


# ================================================================
# CONFIGURACIÓN DE GENERACIÓN
# ================================================================

MAX_OUTPUT_TOKENS = 3000

TEMPERATURE = 0.35


# ================================================================
# HISTORIAL
# ================================================================

MAX_HISTORY_MESSAGES = 6


# ================================================================
# CONTEXTO DEL EQUIPO
# ================================================================

team_context = {

    "etapa": "",

    "edades": "",

    "cantidad_chicos": "",

    "tema_mensual": "",

    "tema_reunion": "",

    "objetivo": "",

    "situacion_equipo": "",

    "duracion": "",

    "tipo_encuentro": "",

}


# ================================================================
# INICIO
# ================================================================

print("=" * 70)

print(
    "🤖 ASISTENTE ECyD - RAG FORMATIVO"
)

print("=" * 70)


# ================================================================
# CARGAR MODELO DE EMBEDDINGS
# ================================================================

print(
    "\n🧠 Cargando modelo de embeddings..."
)


embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)


print(
    "✅ Modelo cargado"
)


# ================================================================
# CARGAR ÍNDICE DOCUMENTAL
# ================================================================

print(
    "\n📚 Cargando índice FAISS..."
)


if not FAISS_DOCUMENTS_PATH.exists():

    raise FileNotFoundError(
        "\n❌ No existe el índice FAISS:\n"
        f"{FAISS_DOCUMENTS_PATH}\n\n"
        "Los archivos esperados son:\n"
        "data/ecyd.index\n"
        "data/index_metadata.json"
    )


if not DOCUMENT_METADATA_PATH.exists():

    raise FileNotFoundError(
        "\n❌ No existe la metadata documental:\n"
        f"{DOCUMENT_METADATA_PATH}\n\n"
        "Los archivos esperados son:\n"
        "data/ecyd.index\n"
        "data/index_metadata.json"
    )


document_index = faiss.read_index(
    str(FAISS_DOCUMENTS_PATH)
)


with open(
    DOCUMENT_METADATA_PATH,
    "r",
    encoding="utf-8"
) as f:

    document_metadata = json.load(f)


print(
    "✅ Índice cargado"
)


print(
    f"   Vectores: {document_index.ntotal}"
)


print(
    f"   Dimensión: {document_index.d}"
)


print(
    f"   Metadatos: "
    f"{len(document_metadata)} documentos"
)


# ================================================================
# NORMALIZACIÓN
# ================================================================

def normalize_text(
    text: str
) -> str:

    if not text:

        return ""

    text = str(text)

    text = text.replace(
        "\x00",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ================================================================
# OBTENER NOMBRE DEL DOCUMENTO
# ================================================================

def get_document_name(
    metadata: Dict[str, Any]
) -> str:

    for key in [

        "filename",

        "file_name",

        "document",

        "document_name",

        "source",

        "title",

        "name",

    ]:

        value = metadata.get(key)

        if value:

            return str(value)


    return "Documento ECyD"


# ================================================================
# OBTENER TEXTO DEL DOCUMENTO
# ================================================================

def get_document_text(
    metadata: Dict[str, Any]
) -> str:

    for key in [

        "text",

        "content",

        "document_text",

        "page_content",

    ]:

        value = metadata.get(key)

        if value:

            return str(value)


    return ""


# ================================================================
# DIVIDIR DOCUMENTO EN CHUNKS
# ================================================================

def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE
) -> List[str]:

    text = normalize_text(
        text
    )

    if not text:

        return []


    chunks = []

    start = 0


    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]


        if chunk.strip():

            chunks.append(
                chunk.strip()
            )


        start = end


    return chunks


# ================================================================
# PREPARAR ÍNDICE DE CHUNKS
# ================================================================

def build_chunks():

    print(
        "\n🧩 Preparando índice semántico de chunks..."
    )


    # ------------------------------------------------------------
    # SI YA EXISTE
    # ------------------------------------------------------------

    if (

        CHUNKS_INDEX_PATH.exists()

        and

        CHUNKS_METADATA_PATH.exists()

    ):

        print(
            "   Índice de chunks encontrado."
        )


        chunk_index = faiss.read_index(
            str(CHUNKS_INDEX_PATH)
        )


        with open(
            CHUNKS_METADATA_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            chunk_metadata = json.load(f)


        print(
            f"   Chunks cargados: "
            f"{len(chunk_metadata)}"
        )


        return (
            chunk_index,
            chunk_metadata
        )


    # ------------------------------------------------------------
    # GENERAR
    # ------------------------------------------------------------

    print(
        "   No existe un índice de chunks guardado."
    )


    print(
        f"   Generando chunks desde "
        f"{len(document_metadata)} documentos..."
    )


    chunks = []

    metadata = []


    for doc_index, doc in enumerate(
        document_metadata
    ):

        text = get_document_text(
            doc
        )


        if not text:

            continue


        document_name = get_document_name(
            doc
        )


        document_chunks = split_text(
            text,
            CHUNK_SIZE
        )


        for (
            chunk_number,
            chunk
        ) in enumerate(
            document_chunks
        ):

            chunks.append(
                chunk
            )


            metadata.append(
                {
                    "document_index":
                        doc_index,

                    "document_name":
                        document_name,

                    "chunk_index":
                        chunk_number,

                    "text":
                        chunk,
                }
            )


    print(
        f"   Fragmentos disponibles: "
        f"{len(chunks)}"
    )


    if not chunks:

        raise RuntimeError(
            "❌ No se pudieron generar chunks "
            "a partir de los documentos."
        )


    print(
        f"   Generando embeddings para "
        f"{len(chunks)} chunks..."
    )


    embeddings = embedding_model.encode(

        chunks,

        show_progress_bar=True,

        convert_to_numpy=True,

        normalize_embeddings=True,

    )


    embeddings = embeddings.astype(
        np.float32
    )


    chunk_index = faiss.IndexFlatIP(
        embeddings.shape[1]
    )


    chunk_index.add(
        embeddings
    )


    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    faiss.write_index(
        chunk_index,
        str(CHUNKS_INDEX_PATH)
    )


    with open(
        CHUNKS_METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(

            metadata,

            f,

            ensure_ascii=False,

            indent=2

        )


    print(
        "\n💾 Índice de chunks guardado:"
    )

    print(
        f"   {CHUNKS_INDEX_PATH}"
    )


    print(
        "💾 Metadatos de chunks guardados:"
    )

    print(
        f"   {CHUNKS_METADATA_PATH}"
    )


    return (
        chunk_index,
        metadata
    )


chunk_index, chunk_metadata = build_chunks()


# ================================================================
# CONTEXTO DEL EQUIPO
# ================================================================

def format_team_context() -> str:

    fields = [

        (
            "Etapa",
            "etapa"
        ),

        (
            "Edades",
            "edades"
        ),

        (
            "Cantidad de adolescentes",
            "cantidad_chicos"
        ),

        (
            "Tema mensual",
            "tema_mensual"
        ),

        (
            "Tema de la reunión",
            "tema_reunion"
        ),

        (
            "Objetivo",
            "objetivo"
        ),

        (
            "Situación actual del equipo",
            "situacion_equipo"
        ),

        (
            "Duración disponible",
            "duracion"
        ),

        (
            "Tipo de encuentro",
            "tipo_encuentro"
        ),

    ]


    lines = []


    for label, key in fields:

        value = team_context.get(
            key,
            ""
        )


        if value:

            lines.append(
                f"- {label}: {value}"
            )


    if not lines:

        return (
            "No se proporcionó todavía "
            "contexto específico del equipo."
        )


    return "\n".join(
        lines
    )


# ================================================================
# MOSTRAR CONTEXTO
# ================================================================

def show_team_context():

    print(
        "\n" + "=" * 70
    )

    print(
        "👥 CONTEXTO ACTUAL DEL EQUIPO"
    )

    print(
        "=" * 70
    )

    print(
        format_team_context()
    )


# ================================================================
# CONFIGURAR CONTEXTO
# ================================================================

def configure_team_context():

    print(
        "\n"
    )

    print(
        "=" * 70
    )

    print(
        "👥 CONFIGURACIÓN DEL EQUIPO"
    )

    print(
        "=" * 70
    )


    print(
        "\nDejá vacío cualquier campo que "
        "no quieras especificar."
    )


    questions = [

        (
            "etapa",
            "Etapa del ECyD"
        ),

        (
            "edades",
            "Edades de los adolescentes"
        ),

        (
            "cantidad_chicos",
            "Cantidad de adolescentes"
        ),

        (
            "tema_mensual",
            "Tema mensual"
        ),

        (
            "tema_reunion",
            "Tema específico de la reunión"
        ),

        (
            "objetivo",
            "Objetivo que querés lograr"
        ),

        (
            "situacion_equipo",
            "Situación actual del equipo"
        ),

        (
            "duracion",
            "Duración disponible"
        ),

        (
            "tipo_encuentro",
            "Tipo de encuentro"
        ),

    ]


    for key, question in questions:

        current = team_context.get(
            key,
            ""
        )


        if current:

            prompt = (
                f"{question} "
                f"[actual: {current}]: "
            )

        else:

            prompt = (
                f"{question}: "
            )


        value = input(
            prompt
        ).strip()


        if value:

            team_context[key] = value


    show_team_context()


# ================================================================
# RECUPERACIÓN DOCUMENTAL
# ================================================================

def search_documents(
    query: str
) -> List[Dict[str, Any]]:

    query_embedding = embedding_model.encode(

        [query],

        convert_to_numpy=True,

        normalize_embeddings=True,

    )


    query_embedding = query_embedding.astype(
        np.float32
    )


    scores, indices = document_index.search(

        query_embedding,

        TOP_K_DOCUMENTS

    )


    results = []


    for score, idx in zip(

        scores[0],

        indices[0]

    ):

        if idx < 0:

            continue


        if idx >= len(document_metadata):

            continue


        metadata = document_metadata[idx]


        results.append(

            {

                "score":
                    float(score),

                "metadata":
                    metadata,

                "document_index":
                    int(idx),

            }

        )


    return results


# ================================================================
# RECUPERACIÓN DE CHUNKS
# ================================================================

def search_chunks(

    query: str,

    documents: List[Dict[str, Any]]

) -> List[Dict[str, Any]]:


    query_embedding = embedding_model.encode(

        [query],

        convert_to_numpy=True,

        normalize_embeddings=True,

    )


    query_embedding = query_embedding.astype(
        np.float32
    )


    scores, indices = chunk_index.search(

        query_embedding,

        CHUNKS_CANDIDATES

    )


    candidate_documents = {

        item["document_index"]

        for item in documents

    }


    candidates = []


    for score, idx in zip(

        scores[0],

        indices[0]

    ):

        if idx < 0:

            continue


        if idx >= len(chunk_metadata):

            continue


        meta = chunk_metadata[idx]


        document_index_value = meta.get(
            "document_index"
        )


        if (

            candidate_documents

            and

            document_index_value

            not in candidate_documents

        ):

            continue


        candidates.append(

            {

                "score":
                    float(score),

                "metadata":
                    meta,

                "chunk_index":
                    int(idx),

            }

        )


    # ------------------------------------------------------------
    # FALLBACK GLOBAL
    # ------------------------------------------------------------

    if len(candidates) < TOP_K_CHUNKS:

        candidates = []


        for score, idx in zip(

            scores[0],

            indices[0]

        ):

            if idx < 0:

                continue


            if idx >= len(chunk_metadata):

                continue


            candidates.append(

                {

                    "score":
                        float(score),

                    "metadata":
                        chunk_metadata[idx],

                    "chunk_index":
                        int(idx),

                }

            )


    # ------------------------------------------------------------
    # DIVERSIFICACIÓN
    # ------------------------------------------------------------

    selected = []

    document_counts = {}


    for candidate in candidates:

        document_name = candidate[
            "metadata"
        ].get(

            "document_name",

            "Documento ECyD"

        )


        count = document_counts.get(

            document_name,

            0

        )


        if count >= 4:

            continue


        selected.append(
            candidate
        )


        document_counts[
            document_name
        ] = count + 1


        if len(selected) >= TOP_K_CHUNKS:

            break


    return selected


# ================================================================
# CONSTRUIR CONTEXTO RAG
# ================================================================

def build_context(

    chunks: List[Dict[str, Any]]

) -> str:


    parts = []

    current_length = 0


    for number, chunk in enumerate(

        chunks,

        start=1

    ):

        meta = chunk[
            "metadata"
        ]


        document_name = meta.get(

            "document_name",

            "Documento ECyD"

        )


        chunk_number = meta.get(

            "chunk_index",

            0

        )


        text = normalize_text(

            meta.get(

                "text",

                ""

            )

        )


        block = (

            f"\n--- FUENTE {number} ---\n"

            f"Documento: {document_name}\n"

            f"Fragmento: {chunk_number}\n"

            f"Relevancia: "
            f"{chunk['score']:.4f}\n\n"

            f"{text}\n"

        )


        if (

            current_length

            + len(block)

            > MAX_CONTEXT_CHARS

        ):

            break


        parts.append(
            block
        )


        current_length += len(
            block
        )


    return "".join(
        parts
    )


# ================================================================
# PROMPT FORMATIVO ECYD
# ================================================================

SYSTEM_PROMPT = r"""

SOS EL ASISTENTE FORMATIVO DEL ECYD.

Tu función no es simplemente contestar preguntas sobre el ECyD.

Tu función es ayudar a responsables y formadores a comprender,
vivir y aplicar el estilo formativo propio del ECyD.

Debés responder desde la identidad del ECyD y utilizando como
base principal el material recuperado del corpus.

============================================================
1. IDENTIDAD DEL ECYD
============================================================

El ECyD busca acompañar al adolescente en su proceso de
maduración humana y espiritual, ayudándolo a descubrir quién es
y quién está llamado a ser, desde una visión positiva de la
adolescencia y como inicio de un camino de santificación.

El adolescente no debe ser visto solamente desde sus problemas.

Debe ser mirado como una persona concreta, libre, capaz de
crecer, con deseos, preguntas, capacidades, dificultades,
búsquedas y potencial apostólico.

El responsable no es simplemente un coordinador de actividades.

Es un formador y acompañante.

Por eso, las respuestas deben ayudar al responsable a comprender:

- qué está viviendo el adolescente;
- qué necesita descubrir;
- qué necesita ser formado;
- qué convicción se busca despertar;
- qué respuesta libre se quiere favorecer;
- cómo acompañar el proceso;
- cómo llevarlo a Cristo;
- cómo transformar una experiencia concreta en una oportunidad
  formativa.

============================================================
2. EL ESTILO FORMATIVO DEL ECYD
============================================================

No reduzcas la formación a:

- transmitir información;
- explicar conceptos;
- hacer dinámicas;
- entretener;
- controlar conductas;
- imponer respuestas;
- llenar una reunión de actividades.

La formación debe tocar la vida concreta del adolescente.

Cuando corresponda, utilizá el dinamismo:

DESPERTAR
↓
RESPONDER
↓
ACOMPAÑAR
↓
FORMAR CONVICCIONES

No fuerces esta estructura si las fuentes recuperadas presentan
otra formulación más adecuada.

El objetivo no es solamente que el adolescente "entienda" algo.

La formación busca que pueda descubrir una verdad, encontrarse
con ella en su propia vida, responder libremente y comenzar a
hacerla vida.

============================================================
3. PAPEL DEL RESPONSABLE
============================================================

El responsable debe:

- conocer a sus adolescentes;
- mirar su realidad concreta;
- comprender la etapa que viven;
- escuchar;
- observar;
- descubrir necesidades;
- caminar con ellos;
- generar confianza;
- ser cercano;
- ser auténtico;
- proponer;
- ayudar a descubrir;
- dar motivaciones;
- formar convicciones;
- acompañar procesos;
- tener paciencia;
- confiar en los tiempos de Dios.

El responsable no debe intentar controlar el proceso interior
del adolescente.

Debe sembrar, acompañar, proponer y confiar.

============================================================
4. ACOMPAÑAR
============================================================

Acompañar significa caminar con el adolescente.

No significa resolverle la vida.

No significa darle inmediatamente una respuesta para cada
problema.

No significa controlar cada decisión.

No significa sustituir su libertad.

Cuando sea pertinente, el acompañamiento puede implicar:

1. acercarse;
2. escuchar;
3. comprender;
4. mirar más profundamente;
5. iluminar;
6. proponer;
7. ayudar a descubrir;
8. dejar espacio para una respuesta libre;
9. continuar acompañando.

Los adolescentes pueden querer hablar y no siempre saber
expresar lo que les pasa.

Por eso, el responsable debe aprender a mirar y escuchar para
descubrir qué necesita realmente el adolescente.

============================================================
5. "CONÓCETE, ACÉPTATE, SUPÉRATE"
============================================================

Cuando las fuentes lo permitan, utilizá esta perspectiva como
camino de crecimiento:

CONÓCETE
→ descubrir quién soy, qué vivo, qué me pasa y qué capacidades
tengo.

ACÉPTATE
→ reconocer la propia realidad con verdad, dignidad y confianza
en el proceso.

SUPÉRATE
→ crecer, responder, desarrollar virtudes y avanzar hacia quien
estoy llamado a ser.

No conviertas esta expresión en una fórmula automática.

Utilizala cuando realmente ayude a interpretar el proceso
formativo del adolescente.

============================================================
6. CRISTO ES EL CENTRO
============================================================

El ECyD no es solamente una propuesta de crecimiento humano.

Cristo está en el centro.

Cuando sea pertinente, ayudá al responsable a descubrir cómo
una situación humana concreta puede abrir al adolescente al:

- encuentro con Cristo;
- amistad con Cristo;
- seguimiento de Cristo;
- respuesta a Cristo;
- misión.

No agregues citas bíblicas arbitrariamente.

No inventes referencias.

Si el material recuperado contiene una referencia bíblica,
podés utilizarla.

Si una referencia bíblica complementaria resulta claramente
pertinente, distinguí que es un complemento y no una cita del
material recuperado.

============================================================
7. VIDA DE EQUIPO
============================================================

La vida de equipo es un elemento esencial del ECyD.

El equipo puede ser lugar de:

- encuentro;
- amistad;
- pertenencia;
- crecimiento;
- descubrimiento personal;
- encuentro con Dios;
- encuentro con los demás;
- servicio;
- responsabilidad;
- virtudes;
- misión.

Por eso, cuando una consulta sea grupal, no pienses solamente
en el adolescente individual.

Considerá también:

- clima;
- vínculos;
- pertenencia;
- participación;
- amistad;
- liderazgo;
- servicio;
- responsabilidad;
- misión.

============================================================
8. EL CONTEXTO DEL ADOLESCENTE
============================================================

La adolescencia debe comprenderse desde la realidad concreta
de cada adolescente y de cada etapa.

Considerá:

- edad;
- etapa del ECyD;
- cantidad de adolescentes;
- realidad del equipo;
- contexto social;
- necesidades concretas;
- tema mensual;
- tema de la reunión;
- objetivo;
- duración;
- tipo de encuentro.

No generalices innecesariamente.

No inventes características de una etapa.

Si una información importante no está disponible, trabajá con
lo que existe y señalá la limitación cuando sea relevante.

============================================================
9. TEMA MENSUAL
============================================================

Si existe un tema mensual, no lo trates como un simple título.

Debe integrarse con:

- la etapa;
- la realidad de los adolescentes;
- el objetivo formativo;
- las convicciones;
- la vida de equipo;
- Cristo;
- la misión.

El tema mensual debe ayudar a dar continuidad al proceso
formativo.

No hagas que cada reunión parezca aislada.

Pensá siempre en proceso.

============================================================
10. CONTEXTO DINÁMICO DEL EQUIPO
============================================================

Tenés disponible el siguiente contexto:

{TEAM_CONTEXT}

Este contexto NO es una fuente documental.

Es información proporcionada por el responsable para adaptar
la respuesta.

Usalo para personalizar la respuesta.

============================================================
11. JERARQUÍA DE FUENTES
============================================================

Cuando sea necesario determinar qué idea tiene mayor autoridad,
priorizá:

1. Estatutos del ECyD.

2. Documentos que explican explícitamente el estilo formativo y
   el camino formativo del ECyD.

3. Materiales oficiales de etapas e itinerarios.

4. Guías y materiales prácticos.

5. Fichas y recursos concretos.

Un material práctico puede mostrar cómo aplicar un principio,
pero no debe redefinir la identidad del ECyD.

============================================================
12. FIDELIDAD AL MATERIAL
============================================================

Las fuentes recuperadas son la base principal.

NO atribuyas al ECyD algo que no esté sostenido por las fuentes.

Diferenciá entre:

A. LO QUE DICE EL MATERIAL ECYD

B. UNA INTERPRETACIÓN FORMATIVA

C. UNA PROPUESTA PRÁCTICA DEL ASISTENTE

Si proponés una dinámica, actividad, pregunta, estructura de
reunión, oración o aplicación que no aparece explícitamente en
las fuentes, presentala como:

"Una propuesta práctica basada en estos principios..."

No la presentes como si fuera una metodología oficial del ECyD.

NO inventes:

- citas;
- documentos;
- páginas;
- frases textuales;
- metodologías;
- nombres de etapas;
- conceptos atribuidos a documentos.

============================================================
13. CUANDO LA PREGUNTA SEA CONCEPTUAL
============================================================

Primero explicá qué significa el concepto.

Después fundamentalo en las fuentes.

Luego explicá qué implica para el responsable.

Finalmente, cuando ayude, bajalo a una situación concreta.

La respuesta debe formar al responsable mientras responde.

============================================================
14. CUANDO LA PREGUNTA SEA PRÁCTICA
============================================================

Antes de proponer una actividad preguntate:

¿Qué queremos formar?

¿Qué queremos despertar?

¿Qué convicción buscamos?

¿Qué necesita vivir el adolescente?

¿Cómo conecta con Cristo?

¿Cómo va a responder libremente?

¿Cómo continuará el acompañamiento después?

No propongas actividades simplemente porque sean divertidas.

La actividad debe estar al servicio del proceso formativo.

============================================================
15. CUANDO LA PREGUNTA SEA SOBRE UN ADOLESCENTE
============================================================

No diagnostiques.

No reduzcas al adolescente a una dificultad.

Intentá comprender:

- qué está viviendo;
- qué puede estar buscando;
- qué necesita;
- qué verdad necesita descubrir;
- qué libertad necesita ejercer;
- qué virtud necesita desarrollar;
- qué acompañamiento necesita;
- cómo puede abrirse al encuentro con Cristo.

Si la situación excede el acompañamiento pastoral ordinario,
señalá los límites del rol del responsable.

============================================================
16. SITUACIONES DELICADAS
============================================================

Si la consulta involucra:

- salud mental;
- violencia;
- abuso;
- autolesión;
- suicidio;
- consumo de sustancias;
- riesgo;
- situaciones familiares graves;

no diagnostiques ni minimices.

El responsable no sustituye a profesionales.

La prioridad es la seguridad del adolescente.

Corresponde involucrar a adultos responsables y profesionales
adecuados según la situación.

El acompañamiento pastoral puede continuar, pero dentro de sus
límites.

============================================================
17. NO RESPONDER COMO CHATBOT GENÉRICO
============================================================

EVITÁ:

"Escuchalo, apoyalo y hacé una dinámica."

Eso es insuficiente.

Buscá explicar:

¿Qué significa escuchar desde el estilo formativo del ECyD?

¿Qué querés despertar?

¿Qué necesita descubrir?

¿Qué convicción buscás?

¿Qué respuesta libre querés favorecer?

¿Cómo vas a acompañar esa respuesta?

¿Cómo conecta con Cristo?

============================================================
18. NO SOBREINTERPRETAR
============================================================

Si el material recuperado no alcanza para responder algo con
seguridad, decilo.

Es preferible decir:

"El material recuperado no presenta un protocolo específico,
pero sí ofrece estos criterios..."

antes que inventar una metodología.

============================================================
19. TONO
============================================================

Respondé en español argentino natural.

Hablale al responsable de forma:

- cercana;
- humana;
- respetuosa;
- clara;
- profunda;
- formativa;
- concreta.

No seas excesivamente académico.

No uses emojis salvo que el responsable los pida.

No empieces automáticamente con:

"¡Hola! Qué buena pregunta."

No elogies artificialmente la consulta.

Entrá directamente en materia.

============================================================
20. ESTRUCTURA DE LAS RESPUESTAS
============================================================

No uses siempre la misma estructura.

Elegí según la consulta.

Podés utilizar:

## Idea central

## Qué dice el material ECyD

## Qué significa para el responsable

## Cómo llevarlo a la práctica

## Qué cuidar

## Convicción que buscamos despertar

## Propuesta concreta

## Preguntas para el responsable

No agregues secciones innecesarias.

============================================================
21. FUENTES RECUPERADAS
============================================================

Estos fragmentos provienen del corpus documental ECyD.

Utilizalos como evidencia:

{RAG_CONTEXT}

============================================================
22. CONSULTA
============================================================

{USER_QUERY}

============================================================
23. INSTRUCCIÓN FINAL
============================================================

Respondé la consulta ayudando al responsable a comprender
verdaderamente el estilo formativo del ECyD.

No te limites a decirle qué hacer.

Ayudalo a comprender:

- qué está formando;
- por qué lo está formando;
- cómo mirar al adolescente;
- qué está viviendo;
- qué necesita descubrir;
- qué papel tiene él como responsable;
- qué lugar ocupa Cristo;
- qué proceso quiere acompañar;
- qué convicción puede despertar;
- cómo llevarlo concretamente a la vida;
- y cómo continuar acompañando después.

La respuesta debe poder formar al responsable mientras recibe
la respuesta.

Cuando corresponda, diferenciá claramente:

"El material ECyD plantea..."

"Desde estos principios, podemos interpretar..."

"Como propuesta práctica, podrías..."

============================================================
FIN DEL PROMPT
============================================================
"""


# ================================================================
# CONSTRUIR PROMPT
# ================================================================

def build_prompt(

    query: str,

    rag_context: str

) -> str:

    return SYSTEM_PROMPT.format(

        TEAM_CONTEXT=
            format_team_context(),

        RAG_CONTEXT=
            rag_context,

        USER_QUERY=
            query,

    )


# ================================================================
# GENERACIÓN CON GROQ / GEMINI
# ================================================================

def generate_with_llm(

    prompt: str

) -> str:


    # ============================================================
    # GROQ
    # ============================================================

    if LLM_PROVIDER == "groq":

        last_error = None


        for attempt in range(3):

            try:

                response = (
                    groq_client
                    .chat
                    .completions
                    .create(

                        model=GROQ_MODEL,

                        messages=[

                            {
                                "role":
                                    "system",

                                "content":
                                    prompt,

                            }

                        ],

                        temperature=
                            TEMPERATURE,

                        max_tokens=
                            MAX_OUTPUT_TOKENS,

                    )
                )


                text = (
                    response
                    .choices[0]
                    .message
                    .content
                )


                if text and text.strip():

                    return text.strip()


                raise RuntimeError(
                    "Groq devolvió una "
                    "respuesta vacía."
                )


            except Exception as e:

                last_error = e

                error_text = str(e)


                transient = any(

                    code in error_text

                    for code in [

                        "429",

                        "500",

                        "502",

                        "503",

                        "504",

                        "timeout",

                        "rate limit",

                        "temporarily unavailable",

                    ]

                )


                if not transient:

                    break


                wait_time = 2 ** attempt


                print(

                    f"\n⚠️ Groq no disponible "

                    f"(intento "
                    f"{attempt + 1}/3). "

                    f"Esperando "
                    f"{wait_time}s..."

                )


                time.sleep(
                    wait_time
                )


        raise RuntimeError(

            "No fue posible generar "
            "la respuesta con Groq.\n\n"

            f"Último error:\n"
            f"{last_error}"

        )


    # ============================================================
    # GEMINI
    # ============================================================

    if LLM_PROVIDER == "gemini":

        last_error = None


        for attempt in range(3):

            try:

                response = (
                    gemini_client
                    .models
                    .generate_content(

                        model=
                            GEMINI_MODEL,

                        contents=
                            prompt,

                        config=
                            types
                            .GenerateContentConfig(

                                temperature=
                                    TEMPERATURE,

                                max_output_tokens=
                                    MAX_OUTPUT_TOKENS,

                            ),

                    )
                )


                if not response:

                    raise RuntimeError(
                        "Gemini devolvió una "
                        "respuesta vacía."
                    )


                text = getattr(

                    response,

                    "text",

                    None

                )


                if text and text.strip():

                    return text.strip()


                raise RuntimeError(
                    "Gemini no devolvió texto."
                )


            except Exception as e:

                last_error = e

                error_text = str(e)


                transient = any(

                    code in error_text

                    for code in [

                        "429",

                        "500",

                        "502",

                        "503",

                        "504",

                        "UNAVAILABLE",

                        "RESOURCE_EXHAUSTED",

                        "DEADLINE",

                    ]

                )


                if not transient:

                    break


                wait_time = 2 ** attempt


                print(

                    f"\n⚠️ Gemini no disponible "

                    f"(intento "
                    f"{attempt + 1}/3). "

                    f"Esperando "
                    f"{wait_time}s..."

                )


                time.sleep(
                    wait_time
                )


        raise RuntimeError(

            "No fue posible generar "
            "la respuesta con Gemini.\n\n"

            f"Último error:\n"
            f"{last_error}"

        )


    raise RuntimeError(
        f"Proveedor no soportado: "
        f"{LLM_PROVIDER}"
    )


# ================================================================
# HISTORIAL
# ================================================================

conversation_history = []


# ================================================================
# PROCESAR CONSULTA
# ================================================================

def answer_query(

    query: str

):


    print(
        "\n🔎 Buscando información relevante..."
    )


    # ============================================================
    # DOCUMENTOS
    # ============================================================

    documents = search_documents(
        query
    )


    print(
        "\n📚 DOCUMENTOS RECUPERADOS"
    )

    print(
        "-" * 70
    )


    for i, result in enumerate(

        documents,

        start=1

    ):

        name = get_document_name(

            result["metadata"]

        )


        score = result["score"]


        print(

            f"{i}. {name} "
            f"(score: {score:.4f})"

        )


    # ============================================================
    # CHUNKS
    # ============================================================

    print(
        "\n🧩 Recuperando fragmentos relevantes..."
    )


    chunks = search_chunks(

        query,

        documents

    )


    rag_context = build_context(
        chunks
    )


    print(

        f"\nFragmentos seleccionados: "
        f"{len(chunks)}"

    )


    print(

        f"Caracteres de contexto: "
        f"{len(rag_context)}"

    )


    # ============================================================
    # MOSTRAR FRAGMENTOS
    # ============================================================

    print(
        "\n🧩 FRAGMENTOS UTILIZADOS"
    )

    print(
        "-" * 70
    )


    for i, chunk in enumerate(

        chunks,

        start=1

    ):

        meta = chunk[
            "metadata"
        ]


        name = meta.get(

            "document_name",

            "Documento ECyD"

        )


        number = meta.get(

            "chunk_index",

            0

        )


        score = chunk[
            "score"
        ]


        text = normalize_text(

            meta.get(

                "text",

                ""

            )

        )


        preview = text[:350]


        print(

            f"{i}. {name} "

            f"(chunk {number}, "

            f"score: {score:.4f})"

        )


        print(
            f"   {preview}..."
        )


    # ============================================================
    # PROMPT
    # ============================================================

    prompt = build_prompt(

        query,

        rag_context

    )


    # ============================================================
    # HISTORIAL
    # ============================================================

    if conversation_history:

        history_text = (

            "\n\n"

            "====================================================\n"

            "CONVERSACIÓN RECIENTE\n"

            "====================================================\n"

        )


        for message in conversation_history[

            -MAX_HISTORY_MESSAGES:

        ]:

            role = message[
                "role"
            ]


            content = message[
                "content"
            ]


            history_text += (

                f"\n{role.upper()}:\n"

                f"{content}\n"

            )


        prompt += history_text


    # ============================================================
    # GENERACIÓN
    # ============================================================

    print(
        "\n⚡ Generando respuesta..."
    )


    print(

        f"   Proveedor: "
        f"{LLM_PROVIDER.upper()}"

    )


    if LLM_PROVIDER == "groq":

        print(
            f"   Modelo: {GROQ_MODEL}"
        )

    else:

        print(
            f"   Modelo: {GEMINI_MODEL}"
        )


    try:

        answer = generate_with_llm(
            prompt
        )


    except Exception as e:

        print(
            "\n❌ ERROR AL GENERAR "
            "LA RESPUESTA"
        )


        print(
            f"\nDetalle:\n{e}"
        )


        return


    # ============================================================
    # HISTORIAL
    # ============================================================

    conversation_history.append(

        {

            "role":
                "usuario",

            "content":
                query,

        }

    )


    conversation_history.append(

        {

            "role":
                "asistente",

            "content":
                answer,

        }

    )


    # ============================================================
    # MOSTRAR RESPUESTA
    # ============================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "🤖 RESPUESTA DEL ASISTENTE"
    )

    print(
        "=" * 70
    )


    print(
        answer
    )


    # ============================================================
    # FUENTES
    # ============================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "📚 FUENTES UTILIZADAS"
    )

    print(
        "=" * 70
    )


    used_sources = []


    for chunk in chunks:

        name = chunk[
            "metadata"
        ].get(

            "document_name",

            "Documento ECyD"

        )


        if name not in used_sources:

            used_sources.append(
                name
            )


    for source in used_sources:

        print(
            f"• {source}"
        )


    print(
        "\n" + "=" * 70
    )

    print(
        "✅ RAG COMPLETADO"
    )

    print(
        "=" * 70
    )


# ================================================================
# AYUDA
# ================================================================

def print_help():

    print(
        """

COMANDOS DISPONIBLES

/ayuda
    Muestra esta ayuda.

/contexto
    Muestra el contexto actual del equipo.

/configurar
    Configura o modifica el contexto del equipo.

/limpiar
    Limpia el historial de conversación.

/salir
    Cierra el asistente.


El resto de los mensajes se interpretan como consultas
formativas para el asistente ECyD.

"""
    )


# ================================================================
# INTERFAZ PRINCIPAL
# ================================================================

print(
    "\n" + "=" * 70
)

print(
    "🤖 ASISTENTE ECyD"
)

print(
    "=" * 70
)


print(
    f"\nProveedor LLM: "
    f"{LLM_PROVIDER.upper()}"
)


if LLM_PROVIDER == "groq":

    print(
        f"Modelo LLM: "
        f"{GROQ_MODEL}"
    )

else:

    print(
        f"Modelo LLM: "
        f"{GEMINI_MODEL}"
    )


print(
    "\nModelo embeddings:"
)

print(
    EMBEDDING_MODEL_NAME
)


print(
    f"\nTop-K documentos: "
    f"{TOP_K_DOCUMENTS}"
)


print(
    f"Chunks candidatos: "
    f"{CHUNKS_CANDIDATES}"
)


print(
    f"Top-K chunks finales: "
    f"{TOP_K_CHUNKS}"
)


print(
    f"\nTamaño chunk: "
    f"{CHUNK_SIZE} caracteres"
)


print(
    f"Máximo contexto: "
    f"{MAX_CONTEXT_CHARS} caracteres"
)


print(
    f"Máximo output: "
    f"{MAX_OUTPUT_TOKENS} tokens"
)


print(
    "\n💡 Comandos: "
    "/contexto, "
    "/configurar, "
    "/limpiar, "
    "/ayuda, "
    "/salir"
)


print(
    "\nEscribí una consulta."
)


# ================================================================
# LOOP PRINCIPAL
# ================================================================

while True:

    try:

        query = input(
            "\n🔎 Consulta: "
        ).strip()


    except (

        KeyboardInterrupt,

        EOFError

    ):

        print(
            "\n\n👋 Hasta luego."
        )

        break


    if not query:

        continue


    command = query.lower()


    # ------------------------------------------------------------
    # SALIR
    # ------------------------------------------------------------

    if command in [

        "salir",

        "exit",

        "quit",

        "/salir",

    ]:

        print(
            "\n👋 Hasta luego."
        )

        break


    # ------------------------------------------------------------
    # AYUDA
    # ------------------------------------------------------------

    if command == "/ayuda":

        print_help()

        continue


    # ------------------------------------------------------------
    # CONTEXTO
    # ------------------------------------------------------------

    if command == "/contexto":

        show_team_context()

        continue


    # ------------------------------------------------------------
    # CONFIGURAR
    # ------------------------------------------------------------

    if command == "/configurar":

        configure_team_context()

        continue


    # ------------------------------------------------------------
    # LIMPIAR
    # ------------------------------------------------------------

    if command == "/limpiar":

        conversation_history.clear()

        print(
            "\n🧹 Historial de conversación limpiado."
        )

        continue


    # ------------------------------------------------------------
    # CONSULTA
    # ------------------------------------------------------------

    answer_query(
        query
    )