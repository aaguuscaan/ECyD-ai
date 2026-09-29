FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DB_PATH=/data/memoria.db PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# Descarga el modelo de embeddings (ONNX) dentro de la imagen
ENV EMBEDDING_CACHE_DIR=/opt/modelos
RUN python -c "from app.embeddings import Embedder; Embedder().encode(['hola'])"

COPY web ./web
COPY scripts ./scripts
COPY cli.py ./
COPY data ./data

RUN mkdir -p /data
VOLUME ["/data"]
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
