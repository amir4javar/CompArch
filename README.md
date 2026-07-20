# RAG Chat Assistant

A multi-turn conversational RAG (Retrieval-Augmented Generation) application for querying PDF documents. It combines hybrid vector + keyword search via Weaviate, a structured 4-node LangGraph reasoning pipeline, and a real-time streaming interface over WebSockets.

[![Live Demo](https://img.shields.io/badge/🤗%20Live%20Demo-Hugging%20Face%20Spaces-blue)](https://huggingface.co/spaces/amir4javar/comp_arch)

---

## Features

- **Multi-turn conversations** — full conversation history with context-aware reformulation
- **Hybrid search** — combines dense vector similarity and BM25 keyword search (50/50 alpha) for best-of-both-worlds retrieval
- **Streaming responses** — tokens stream in real time to the browser via WebSocket
- **Persistent sessions** — conversation state is stored in SQLite; restarting the server preserves history
- **REST fallback** — non-streaming HTTP endpoint available alongside WebSocket

---

## Architecture

```
User (Streamlit UI)
    │
    │  WebSocket  ws://localhost:8000/ws/chat/{session_id}
    ▼
FastAPI Backend  (api_service.py)
    │
    ▼
LangGraph RAG Pipeline
    ├── 1. Contextualize   — analyze history, extract current intent
    ├── 2. Extract Terms   — distill 1–3 precise search queries via LLM
    ├── 3. Retrieve        — hybrid search (vector + BM25) against Weaviate
    └── 4. Generate        — stream grounded answer from LLM
    │
    ▼
Conversation Memory  (SQLite  conversations.db)
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + WebSocket |
| RAG Pipeline | LangGraph |
| Vector Database | Weaviate (local Docker) |
| LLM & Embeddings | OpenAI-compatible API (`deepseek-v4-pro` / `text-embedding-3-large`) |
| Conversation Memory | SQLite via LangGraph `SqliteSaver` |
| Document Loader | PyPDF |

---

## Project Structure

```
.
├── config.py                        # All configuration constants (reads from .env)
├── embeddings.py                    # Embedding client wrapper
├── vectorstore.py                   # PDF loading, chunking, and Weaviate indexing
│
├── graph/
│   ├── state.py                     # GraphState TypedDict
│   ├── nodes.py                     # Pipeline nodes + generate_stream
│   └── builder.py                   # Graph wiring and compilation
│
├── api/
│   ├── lifespan.py                  # FastAPI startup/shutdown + thread pool
│   └── routes.py                    # HTTP and WebSocket endpoints
│
├── ui/
│   ├── styles.py                    # Custom CSS
│   ├── websocket_client.py          # WebSocket communication helpers
│   ├── sidebar.py                   # Settings sidebar
│   └── chat.py                      # Chat history and input handling
│
├── hybrid_search_graph_history.py   # Entry point — run pipeline from terminal
├── api_service.py                   # Entry point — FastAPI server
├── streamlit_app.py                 # Entry point — Streamlit UI
│
├── reset_weaviate.py                # Utility: wipe and re-index Weaviate collection
├── .env.example                     # Environment variable template
├── requirements.txt                 # Core dependencies
└── requirements_auth.txt            # Extended deps (Firebase, Firestore, websocket-client)
```

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Docker (for Weaviate)
- An OpenAI-compatible API key

### 2. Start Weaviate

```bash
docker run -d \
  -p 8080:8080 \
  -p 50051:50051 \
  cr.weaviate.io/semitechnologies/weaviate:latest
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
# then edit .env:
# LLM_API_KEY=sk-...
```

All other settings (model names, ports, PDF path) are in `config.py`.

### 5. Add your PDF

Place your PDF in the project root. By default the app looks for `computer_architecture.pdf`. To use a different file, update `PDF_PATH` in `config.py`.

### 6. Start the backend

```bash
uvicorn api_service:app --reload --host 0.0.0.0 --port 8000
```

On first startup the backend automatically loads the PDF, chunks it, embeds it, and indexes it in Weaviate. Subsequent starts skip this step if the collection already exists.

### 7. Start the frontend

```bash
streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Acknowledgments

Claude (Anthropic) was used as an assistant for designing the Streamlit UI components in this project.

---

---

## Configuration

All settings are in `config.py` and can be overridden via environment variables or by editing the file directly:

| Variable | Default | Description |
|---|---|---|
| `PDF_PATH` | `computer_architecture.pdf` | Path to the source PDF |
| `LLM_MODEL` | `deepseek-v4-pro` | Chat model |
| `EMBEDDING_MODEL` | `text-embedding-3-large` | Embedding model |
| `LLM_API_BASE` | `https://api.openai.com/v1` | API base URL (swap for any OpenAI-compatible endpoint) |
| `LLM_API_KEY` | *(from `.env`)* | API key |
| `WEAVIATE_URL` | `http://localhost:8080` | Weaviate HTTP endpoint |
| `EMBED_BATCH_SIZE` | `128` | Chunks per embedding request |
| `API_HOST` / `API_PORT` | `localhost` / `8000` | FastAPI server binding |

---

## How It Works

### RAG Pipeline (LangGraph)

The pipeline is a directed graph with four nodes executed in sequence:

1. **Contextualize** — The LLM reads the last 8 messages and the current question, then produces a `CONTEXT_SUMMARY` describing what prior context is needed. For standalone questions it passes through unchanged.

2. **Extract Terms** — The LLM distills the reformulated question into 1–3 precise search terms optimized for retrieval.

3. **Retrieve** — For each search term, a hybrid search runs against Weaviate combining:
   - Dense vector similarity (`text-embedding-3-large`)
   - BM25 keyword search
   - Equal 50/50 alpha weighting

   Results are deduplicated by `chunk_id` and the top 10 chunks by score are kept.

4. **Generate** — The LLM streams an answer using the retrieved chunks and the context summary as grounding.

### Conversation Memory

Each session has a `session_id` (e.g. `session_a3f2c1b0`). State is persisted in `conversations.db` (SQLite) via LangGraph's `SqliteSaver`. Reusing the same session ID after a server restart restores the full conversation history.

### Document Indexing

On first run, the PDF is:
1. Loaded page-by-page with `PyPDFLoader`
2. Split into ~800-token chunks with 100-token overlap
3. Each chunk is assigned a unique `chunk_id`
4. Embedded in batches and stored in the Weaviate collection `BookChunk_hist`

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | API info and available endpoints |
| `GET` | `/health` | Weaviate connectivity check |
| `GET` | `/session` | Generate a new session ID |
| `WS` | `/ws/chat/{session_id}` | Streaming chat (WebSocket) |
| `POST` | `/chat/{session_id}` | Non-streaming chat (REST) |
| `GET` | `/debug/history/{session_id}` | Inspect conversation history for a session |
| `GET` | `/docs` | Interactive Swagger UI |

### WebSocket protocol

**Client → Server**
```json
{ "question": "What is pipelining?" }
```

**Server → Client** (in order)
```json
{ "type": "connected",    "session_id": "...", "message": "Connected to RAG chat service" }
{ "type": "processing" }
{ "type": "stream_start", "search_queries": ["pipelining", "instruction hazards"] }
{ "type": "token",        "content": "P" }
{ "type": "token",        "content": "ipelining" }
{ "type": "complete",     "answer": "...", "sources": [...], "search_queries": [...] }
```

### REST endpoint

```bash
curl -X POST http://localhost:8000/chat/my-session \
  -H "Content-Type: application/json" \
  -d '{"question": "What is cache coherence?"}'
```

---

## Utilities

**Force re-indexing** (deletes the Weaviate collection so the next startup rebuilds it):
```bash
python reset_weaviate.py
```

**Run the pipeline from the terminal** (no UI):
```bash
python hybrid_search_graph_history.py
```

---

## Troubleshooting

**Weaviate connection refused**
Confirm Docker is running and the container is up:
```bash
docker ps
curl http://localhost:8080/v1/.well-known/ready
```

**`LLM_API_KEY` not found**
Make sure `.env` exists in the project root with `LLM_API_KEY=...` set, or export the variable in your shell.

**PDF not found on startup**
Check that your PDF file name matches `PDF_PATH` in `config.py` and that it is placed in the project root.

**Want to use a different LLM provider**
Set `LLM_API_BASE` to any OpenAI-compatible endpoint (e.g. Azure OpenAI, local Ollama with `openai` compatibility) and update `LLM_MODEL` accordingly.
