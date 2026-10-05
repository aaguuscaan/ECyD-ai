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
  memory.py      SQLite/Supabase: cuentas, equipos, memoria, conversaciones, notas, encuentros
  auth.py        cuentas individuales (scrypt + cookie firmada) y código de registro
  programas.py   programa por etapa, temas por mes y tiempos litúrgicos
  assistant.py   orquestación de cada consulta, preparación de encuentros y memoria
  main.py        API web (FastAPI) y servidor de la interfaz
web/             interfaz (HTML/CSS/JS, sin dependencias externas)
scripts/
  ingest_corpus.py  PDFs → data/corpus.json (con OCR)
  build_index.py    corpus → chunks + índices FAISS (+ --check)
  build_programas.py  programa por etapa + calendario de fichas → data/programas.json
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
python scripts\build_index.py --backend onnx   REM recomendado: rechunkea y recalcula embeddings (2-5 min)
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

## Cuentas, etapas y encuentros

**Cuentas.** Cada responsable entra con su email y contraseña. Sus equipos, encuentros y
conversaciones son solo suyos (el servidor verifica el dueño en cada pedido). Para crear
una cuenta hace falta el **código de acceso**: `REGISTRATION_CODE`, o si no está definido,
el `APP_PASSWORD` de siempre. La **primera cuenta** que se crea adopta los datos que ya
existían (equipos, conversaciones) de la época de la contraseña compartida.

**Material por etapa.** Cada documento tiene `categoria` (`programa`, `ficha`, `documento`,
`recurso`) y sus `etapas`. La vista *Documentos* lo organiza por Etapa 1–4: programa
(Alianza, amor, virtud, símbolo, temas centrales), fichas por mes, documentos y recursos.

**Programa y temas por mes.** `scripts/build_programas.py` extrae de *Formando apóstoles en
el ECyD* (Tomo III) la sección de cada etapa y arma el calendario a partir de las carpetas
de fichas por mes (ciclo mexicano → ciclo argentino: septiembre→marzo … junio→diciembre;
enero/febrero = receso) más los tiempos litúrgicos (Cuaresma, Pascua, Cristo Rey, Navidad),
calculados por fecha. No se inventan temas: si una etapa no tiene fichas en un período, se dice.

**Progresión de etapas.** La búsqueda prioriza la etapa del grupo, admite la siguiente solo
como complemento (máx. 2 fragmentos, rotulados), nunca etapas posteriores salvo que la
consulta las nombre explícitamente. Orden de autoridad: programa > fichas > documentos >
recursos > historial del grupo > información del responsable.

**Preparar encuentro.** Grupo → etapa → programa del momento del año → ficha sugerida (o
tema propio) → la IA lee las fichas, el programa y los encuentros anteriores del grupo
(avisa si un tema o ficha se repite) → propone el encuentro siguiendo la metodología de la
ficha → el responsable lo edita y lo guarda en *Mis encuentros* (borrador / planificado /
realizado, con observaciones).

Después de cambiar PDFs o el índice: `python scripts/build_programas.py`.

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
  (tablas `users`, `teams`, `memories`, `conversations`, `messages`, `encuentros`). Las tablas tienen RLS: solo
  aceptan pedidos del servidor que traen el secreto `ECYD_DB_SECRET`; la clave pública de
  Supabase sola no da acceso a nada.
- **Búsqueda**: el mismo modelo de embeddings en versión ONNX cuantizada (~120 MB, con
  `onnxruntime`). En cada arranque en frío se descarga en `/tmp` (la primera consulta
  tarda unos segundos más). `/api/health` informa `embeddings.similitud_promedio`: si es > 0.9, el modelo en
  ejecución coincide con el que armó el índice.

Variables de entorno en Vercel:

| Variable | Qué es |
|---|---|
| `REGISTRATION_CODE` | código para crear cuentas (si falta, se usa `APP_PASSWORD`) |
| `GROQ_API_KEY` | clave de Groq |
| `SUPABASE_URL` | `https://<proyecto>.supabase.co` |
| `SUPABASE_KEY` | clave publicable de Supabase (`sb_publishable_…`) |
| `ECYD_DB_SECRET` | secreto del servidor (su hash está en `private.app_secret`) |
| `APP_PASSWORD` | código de registro heredado (antes era la contraseña compartida) |
| `SECRET_KEY` | cadena aleatoria para firmar la sesión |

Sin las variables de Supabase la app usa SQLite local (`data/memoria.db`), así que en tu
PC funciona igual que antes.

Para recalcular el índice con exactamente el mismo motor que usa Vercel:
`python scripts\build_index.py --backend onnx`.

### Alternativa: Docker (Render, Railway, VPS)

```bash
docker compose up -d --build     # http://servidor:8000
```
Montá un volumen en `/data` si no usás Supabase.

**Importante:** la memoria guarda información sobre adolescentes. Mantené el repositorio
**privado**, definí siempre un código de registro (`REGISTRATION_CODE` o `APP_PASSWORD`),
`SECRET_KEY`, y usá HTTPS.

## Límites de Groq (plan gratuito)

El plan gratis de Groq permite **8.000 tokens por minuto por organización** (consulta +
respuesta), sin importar cuántas claves crees. La app se adapta sola: usa la versión
condensada del prompt formativo (mismos principios), calcula cuánto espacio queda para la
respuesta y, si Groq igual rechaza el pedido por tamaño, reintenta recortando historial y
fuentes. Si Groq pide esperar por límite de velocidad, espera lo indicado y reintenta.

Con el plan pago (Dev tier) podés poner `GROQ_TPM_LIMIT` más alto y `PROMPT_VERSION=completo`.

## Pruebas

```bash
pip install pytest && python -m pytest tests -q
python scripts/build_index.py --check
```
