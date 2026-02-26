#!/usr/bin/env bash
set -e

echo "=== Starting Weaviate ==="
PERSISTENCE_DATA_PATH=/tmp/weaviate \
AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
QUERY_DEFAULTS_LIMIT=25 \
DEFAULT_VECTORIZER_MODULE=none \
CLUSTER_HOSTNAME=node1 \
weaviate --host 0.0.0.0 --port 8080 --scheme http &

# Wait for Weaviate to be ready
echo "Waiting for Weaviate..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
        echo "Weaviate is ready."
        break
    fi
    sleep 1
done

echo "=== Starting FastAPI ==="
uvicorn api_service:app --host 127.0.0.1 --port 8000 &

# Give FastAPI a moment to start and index the PDF
sleep 3

echo "=== Starting Streamlit ==="
# Streamlit runs as PID 1's child — if it dies, the container stops
exec streamlit run streamlit_app.py \
    --server.port 7860 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
