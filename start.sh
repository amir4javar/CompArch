#!/bin/bash
set -e

# ── Weaviate configuration (all via env vars) ──────────────────────────────────
export PERSISTENCE_DATA_PATH=/app/weaviate_data
export AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
export CLUSTER_HOSTNAME=node1
export DEFAULT_VECTORIZER_MODULE=none
export ENABLE_MODULES=""
export QUERY_DEFAULTS_LIMIT=25
export GRPC_PORT=50051
export LOG_LEVEL=warning

# ── Start Weaviate in the background ──────────────────────────────────────────
echo "[start.sh] Starting Weaviate..."
/usr/local/bin/weaviate --host 0.0.0.0 --port 8080 --scheme http >> /tmp/weaviate.log 2>&1 &

# ── Wait for Weaviate to be ready (max ~60 s) ─────────────────────────────────
echo "[start.sh] Waiting for Weaviate to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
        echo "[start.sh] Weaviate is ready!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "[start.sh] ERROR: Weaviate did not become ready in time. Check /tmp/weaviate.log"
        cat /tmp/weaviate.log
        exit 1
    fi
    sleep 2
done

# ── Start FastAPI on localhost:8000 (internal only, not exposed) ───────────────
# On first boot this will also embed + index the PDF into Weaviate.
echo "[start.sh] Starting FastAPI..."
uvicorn api_service:app --host 127.0.0.1 --port 8000 >> /tmp/fastapi.log 2>&1 &

# ── Start Streamlit on 0.0.0.0:7860 (the only exposed port) ──────────────────
echo "[start.sh] Starting Streamlit on port 7860..."
exec streamlit run streamlit_app.py \
    --server.port 7860 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false
