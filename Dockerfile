# --- Stage 1: source of the standalone Weaviate server binary ---
FROM semitechnologies/weaviate:1.28.2 AS weaviate-bin

# --- Stage 2: application image (Weaviate + FastAPI + Streamlit, one container) ---
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl musl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=weaviate-bin /bin/weaviate /usr/local/bin/weaviate

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/weaviate && chmod -R 777 /data /app
ENV PERSISTENCE_DATA_PATH=/data/weaviate

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 7860

ENTRYPOINT ["/entrypoint.sh"]
