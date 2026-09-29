# Asistente ECyD – RAG formativo (versión web)

Asistente de IA para responsables y formadores del ECyD. Responde a partir de los
documentos del ECyD, distingue **lo que dice el material**, la **interpretación
formativa** y la **propuesta práctica**, recuerda a cada equipo y guarda el
historial de conversaciones.

```
Documentos ECyD ─► corpus.json (v2) ─► FAISS documentos ─► recuperación inicial
                                   └► FAISS chunks ─────► recuperación fina + re-ranking
                                                          (etapa del equipo, autoridad)
Perfil del equipo + memoria + notas de la conversación + historial
                                   └──────────────► prompt formativo ECyD ─► Groq ─► respuesta con [F#]
```

## Estructura

```
app/
  config.py      configuración (.env)
  corpus.py      esquema v2 de documentos, metadata, temas y chunking
  retrieval.py   RAG en dos etapas (FAISS) + re-ranking + contexto [F1]…
  prompts.py     prompt formativo ECyD (sistema) + armado del mensaje
  llm.py         cliente Groq (streaming, reintentos, modelo de respaldo); Gemini opcional
  memory.py      SQLite: equipos, memoria, conversaciones, mensajes, notas
  assistant.py   orquestación de cada consulta + actualización de memoria
  main.py        API web (FastAPI) y servidor de la interfaz
web/             interfaz (HTML/CSS/JS, sin dependencias externas)
scripts/
  ingest_corpus.py  PDFs → data/corpus.json (con OCR)
  build_index.py    corpus → chunks + índices FAISS (+ --check)
  migrate_v1.py     migra los datos del formato anterior (ya ejecutado)
  search.py         buscador de consola para revisar la recuperación
data/
  corpus.json, documents.json, chunks.json, *.index, index_manifest.json
  overrides.json    correcciones manuales de metadata (títulos, etapas, temas…)
  memoria.db        memoria e historial (se crea sola)
  legacy/           archivos del formato anterior (respaldo)
legacy/          scripts originales (rag.py, etc.) como referencia
cli.py           versión de consola con memoria persistente
tests/           pruebas sin red
```

## Puesta en marcha (Windows, local)

```bat
cd E:\ECyD-IA
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      REM solo si no tenés .env: pegá tu GROQ_API_KEY
python scripts\build_index.py --backend fastembed   REM recomendado: rechunkea y recalcula embeddings (2-5 min)
iniciar.bat                     REM abre http://localhost:8000
```

`build_index.py` es recomendable una vez: los datos migrados funcionan, pero conservan los
chunks viejos de 1600 caracteres y el modelo de embeddings solo "lee" ~128 tokens
(≈550 caracteres) de cada uno. Los chunks nuevos (~650 caracteres, por párrafo, con
solapamiento) hacen buscable todo el texto.

Consola: `python cli.py` (comandos `/ayuda`, `/equipo`, `/configurar`, `/memoria`,
`/recordar`, `/historial`, `/nueva`, …).

## Diseño e identidad

La interfaz sigue el **Manual de imagen ECYD (2017)**: rojo institucional Pantone 187
(`#AC0D2E`), rojo de la Cruz Pantone 186 y negro en los trazos; tipografía del nombre
Eurostile Bold (en web se usa *Saira*, de la misma familia; si la computadora tiene
Eurostile instalada, se usa esa). La Cruz del ECyD y el logotipo están en `web/img/`
como SVG extraídos del manual, sin deformar ni recolorear (en modo oscuro la Cruz va
sobre fondo blanco, como en la bandera). Los colores están como variables al comienzo
de `web/styles.css`.

Foto de portada opcional: guardá una imagen como `web/img/portada.jpg` y aparece en el
inicio.

## Memoria

| Nivel | Dónde | Qué guarda | Cómo se borra |
|---|---|---|---|
| Equipo | `teams` | perfil: etapa, edades, tema mensual, objetivo… | Configurar equipo → Eliminar |
| Memoria del equipo | `memories` | hechos duraderos (manuales o aprendidos de las conversaciones) | Panel "Memoria del equipo": editar / borrar / borrar todo |
| Historial | `conversations`, `messages` | cada conversación con sus fuentes | Ícono ✕ en el historial |
| Temporal | `conversations.notas` | resumen vivo de una conversación | Botón "Notas" o al borrar la conversación |

Después de cada respuesta, un modelo rápido de Groq propone hasta 3 recuerdos nuevos del
equipo (evitando detalles sensibles) y actualiza las notas de la conversación. Se puede
desactivar por equipo o globalmente con `AUTO_MEMORY=false`.

## Datos del corpus (schema v2)

Cada documento tiene: `id`, `ids_legacy`, `titulo`, `tipo`, `autoridad` (1 = Estatutos …
5 = fichas), `etapas`, `idioma`, `temas`, `nivel_escolar`, `calendario` (mes original
MX, equivalente argentino, tiempo litúrgico), `fuente` (archivo, ruta, carpeta, duplicados),
`extraccion` (método, calidad, sha1) y `texto`. Los vocabularios están en `corpus.json`.

Para corregir un título, etapa o tema, editá `data/overrides.json` y ejecutá
`python scripts/build_index.py`. Para agregar material nuevo: copiarlo en la carpeta
del ECyD, `python scripts/ingest_corpus.py` y luego `build_index.py`.

## Despliegue en la web (Vercel + Supabase)

- **Vercel** corre la app (FastAPI, `app/main.py`, configurada en `vercel.json`).
- **Supabase** guarda la memoria: equipos, recuerdos, conversaciones y notas
  (tablas `teams`, `memories`, `conversations`, `messages`). Las tablas tienen RLS: solo
  aceptan pedidos del servidor que traen el secreto `ECYD_DB_SECRET`; la clave pública de
  Supabase sola no da acceso a nada.
- **Búsqueda**: el mismo modelo de embeddings en versión ONNX (`fastembed`), liviano. En
  cada arranque en frío se descarga en `/tmp` (la primera consulta tarda unos segundos
  más). `/api/health` informa `embeddings.similitud_promedio`: si es > 0.9, el modelo en
  ejecución coincide con el que armó el índice.

Variables de entorno en Vercel:

| Variable | Qué es |
|---|---|
| `GROQ_API_KEY` | clave de Groq |
| `SUPABASE_URL` | `https://<proyecto>.supabase.co` |
| `SUPABASE_KEY` | clave publicable de Supabase (`sb_publishable_…`) |
| `ECYD_DB_SECRET` | secreto del servidor (su hash está en `private.app_secret`) |
| `APP_PASSWORD` | contraseña para entrar a la web (recomendado) |
| `SECRET_KEY` | cadena aleatoria para firmar la sesión |

Sin las variables de Supabase la app usa SQLite local (`data/memoria.db`), así que en tu
PC funciona igual que antes.

Para recalcular el índice con exactamente el mismo motor que usa Vercel:
`python scripts\build_index.py --backend fastembed`.

### Alternativa: Docker (Render, Railway, VPS)

```bash
docker compose up -d --build     # http://servidor:8000
```
Montá un volumen en `/data` si no usás Supabase.

**Importante:** la memoria guarda información sobre adolescentes. Mantené el repositorio
**privado**, definí siempre `APP_PASSWORD` y usá HTTPS.

## Pruebas

```bash
pip install pytest && python -m pytest tests -q
python scripts/build_index.py --check
```
