"""
FastAPI WebSocket Service for Hybrid Search RAG Pipeline
Simplified version that properly handles conversation history.

Run with: uvicorn api_service:app --reload --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
from api.lifespan import lifespan
from api.routes import router

# --- FastAPI App ---
app = FastAPI(
    title="RAG Chat API",
    description="Hybrid Search RAG with Conversation History",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
