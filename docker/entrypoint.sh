#!/usr/bin/env bash
set -euo pipefail

: "${WEAVIATE_HOST:=localhost}"
: "${WEAVIATE_LOCAL_PORT:=8080}"
: "${WEAVIATE_GRPC_PORT:=50051}"
: "${API_PORT:=8000}"
: "${STREAMLIT_PORT:=7860}"
: "${PERSISTENCE_DATA_PATH:=/data/weaviate}"

echo "[entrypoint] starting embedded Weaviate on :${WEAVIATE_LOCAL_PORT} (grpc :${WEAVIATE_GRPC_PORT})..."
QUERY_DEFAULTS_LIMIT=25 \
AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
PERSISTENCE_DATA_PATH="${PERSISTENCE_DATA_PATH}" \
DEFAULT_VECTORIZER_MODULE=none \
ENABLE_MODULES="" \
CLUSTER_HOSTNAME=node1 \
GRPC_PORT="${WEAVIATE_GRPC_PORT}" \
/usr/local/bin/weaviate --host 0.0.0.0 --port "${WEAVIATE_LOCAL_PORT}" --scheme http &
WEAVIATE_PID=$!

echo "[entrypoint] waiting for Weaviate readiness..."
ready=0
for i in $(seq 1 30); do
    if curl -fs "http://localhost:${WEAVIATE_LOCAL_PORT}/v1/.well-known/ready" >/dev/null 2>&1; then
        echo "[entrypoint] Weaviate is ready."
        ready=1
        break
    fi
    sleep 2
done
if [ "$ready" -ne 1 ]; then
    echo "[entrypoint] Weaviate failed to become ready after 60s" >&2
    exit 1
fi

echo "[entrypoint] starting FastAPI backend on :${API_PORT}..."
uvicorn api_service:app --host 0.0.0.0 --port "${API_PORT}" &
FASTAPI_PID=$!

trap 'echo "[entrypoint] shutting down..."; kill "$WEAVIATE_PID" "$FASTAPI_PID" 2>/dev/null || true' EXIT INT TERM

echo "[entrypoint] starting Streamlit on :${STREAMLIT_PORT}..."
exec streamlit run streamlit_app.py \
    --server.address 0.0.0.0 \
    --server.port "${STREAMLIT_PORT}" \
    --server.headless true
