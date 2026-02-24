# RAG Chat Assistant

A Retrieval-Augmented Generation (RAG) chat application that lets you have multi-turn conversations with a PDF document. It uses hybrid vector + keyword search backed by Weaviate, a LangGraph pipeline for structured reasoning, and a streaming WebSocket interface.

---

## Quick Start

```bash
# 1. Start Weaviate
docker run -d -p 8080:8080 -p 50051:50051 \
  cr.weaviate.io/semitechnologies/weaviate:1.28.0

# 2. Set your API key and install dependencies
cp config.py.example config.py   # then fill in LLM_API_KEY and LLM_API_BASE
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Start the backend (indexes PDF on first run)
uvicorn api_service:app --reload --host 0.0.0.0 --port 8000

# 4. Start the frontend
streamlit run streamlit_app.py
# Open http://localhost:8501
```

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
LangGraph RAG Pipeline  (hybrid_search_graph_history.py)
    ├── 1. Contextualize   — analyze conversation history, reformulate question
    ├── 2. Extract Terms   — extract 1–3 key search terms via LLM
    ├── 3. Retrieve        — hybrid search (vector + BM25) on Weaviate
    └── 4. Generate        — stream answer from LLM using retrieved context
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
| Vector Database | Weaviate (local) |
| LLM & Embeddings | GPT API (OpenAI-compatible) |
| Conversation Memory | SQLite via LangGraph `SqliteSaver` |
| Document Loader | PyPDF |

---

## Project Structure

```
.
├── config.py                        # All configuration constants
├── embeddings.py                    # GPTEmbeddings class
├── vectorstore.py                   # PDF loading, chunking, and Weaviate indexing
│
├── graph/
│   ├── state.py                     # GraphState TypedDict
│   ├── nodes.py                     # Pipeline nodes + generate_stream
│   └── builder.py                   # Graph wiring and compilation
│
├── api/
│   ├── lifespan.py                  # FastAPI startup/shutdown + thread pool
│   └── routes.py                    # All HTTP and WebSocket endpoints
│
├── ui/
│   ├── styles.py                    # Custom CSS
│   ├── websocket_client.py          # WebSocket communication helpers
│   ├── sidebar.py                   # Settings sidebar
│   └── chat.py                      # Chat history, input handling, footer
│
├── hybrid_search_graph_history.py   # Entry point — pipeline (run directly or import)
├── api_service.py                   # Entry point — FastAPI server
├── streamlit_app.py                 # Entry point — Streamlit UI
│
├── reset_weaviate.py                # Utility: delete Weaviate collection
│
└── requirements.txt
```

---

## Prerequisites

- Python 3.10+
- Docker (for running Weaviate)
- A `computer_architecture.pdf` file placed in the project root (used as the knowledge base)
- Access to an **OpenAI-compatible API** (OpenAI, Azure OpenAI, local model server, etc.)

### Running Weaviate locally

```bash
docker run -d \
  -p 8080:8080 \
  -p 50051:50051 \
  cr.weaviate.io/semitechnologies/weaviate:1.28.0
```

> Pinning to a specific version is recommended over `latest` for reproducibility.

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Configuration

All settings live in `config.py`. At minimum, set your API credentials before running:

```python
LLM_API_KEY  = "sk-..."                        # your OpenAI (or compatible) API key
LLM_API_BASE = "https://api.openai.com/v1"     # base URL for the LLM API
```

> **Keep your API key out of version control.** You can also export it as an environment variable and read it in `config.py` with `os.environ.get("OPENAI_API_KEY", "")`.

Full settings reference:

```python
PDF_PATH         = "computer_architecture.pdf"
WEAVIATE_URL     = "http://localhost:8080"
EMBEDDING_MODEL  = "text-embedding-3-large"
LLM_MODEL        = "gpt-4o-mini"
LLM_API_BASE     = ""
LLM_API_KEY      = ""
EMBED_BATCH_SIZE = 128

API_HOST = "localhost"
API_PORT = 8000
```

---

## Running the Application

Both services must be running at the same time.

### 1. Start the FastAPI backend

```bash
uvicorn api_service:app --reload --host 0.0.0.0 --port 8000
```

On first startup the backend will automatically load the PDF, chunk it, embed it, and index it in Weaviate. Subsequent starts skip this step if the collection already exists.

### 2. Start the Streamlit frontend

```bash
streamlit run streamlit_app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

### 3. (Optional) Run the pipeline from the terminal

```bash
python hybrid_search_graph_history.py
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | API info |
| `GET` | `/health` | Weaviate connectivity check |
| `GET` | `/session` | Generate a new session ID |
| `WS` | `/ws/chat/{session_id}` | Streaming chat (WebSocket) |
| `POST` | `/chat/{session_id}` | Non-streaming chat (REST) |
| `GET` | `/debug/history/{session_id}` | Inspect conversation history |
| `GET` | `/docs` | Interactive API docs (Swagger) |

### WebSocket message protocol

**Client → Server**
```json
{ "question": "What is pipelining?" }
```

**Server → Client** (sequence)
```json
{ "type": "connected",    "session_id": "...", "message": "..." }
{ "type": "processing" }
{ "type": "stream_start", "search_queries": ["pipelining", "..."] }
{ "type": "token",        "content": "P" }
{ "type": "token",        "content": "i" }
{ "type": "complete",     "answer": "...", "sources": [...], "search_queries": [...] }
```

---

## How It Works

### RAG Pipeline (LangGraph)

The pipeline is a directed graph with four nodes executed in sequence:

1. **Contextualize** — Given the conversation history, the LLM extracts the user's actual intent and produces a context summary. For standalone questions it passes the question through unchanged.

2. **Extract Terms** — The LLM distills the reformulated question into 1–3 precise search terms optimized for retrieval.

3. **Retrieve** — For each search term, a hybrid search is run against Weaviate combining:
   - Vector similarity (`text-embedding-3-large`, alpha = 0.5)
   - BM25 keyword search (alpha = 0.5)

   Results are deduplicated by `chunk_id` and the top 10 chunks by score are kept.

4. **Generate** — The LLM streams an answer using the retrieved chunks and conversation context summary as grounding.

### Conversation Memory

Each session is identified by a `session_id` (e.g. `session_a3f2c1b0`). Conversation state is persisted in `conversations.db` (SQLite) via LangGraph's `SqliteSaver` checkpointer. Reusing the same session ID across restarts preserves full conversation history.

### Document Indexing

On first run, `computer_architecture.pdf` is:
1. Loaded page-by-page with `PyPDFLoader`
2. Split into ~800-token chunks with 100-token overlap
3. Each chunk is assigned a unique `chunk_id`
4. Embedded in batches of 128 and stored in the Weaviate collection `BookChunk_hist`

---

## Utilities

**Delete the Weaviate collection** (to force re-indexing):
```bash
python reset_weaviate.py
```

---

## Troubleshooting

**Backend fails to start / cannot connect to Weaviate**
- Confirm Weaviate is running: `docker ps` and `curl http://localhost:8080/v1/.well-known/ready`
- Check that ports 8080 and 50051 are not blocked by a firewall or already in use.

**`FileNotFoundError` for the PDF**
- Place `computer_architecture.pdf` in the project root (same directory as `api_service.py`).
- Or update `PDF_PATH` in `config.py` to point to the correct location.

**`AuthenticationError` / 401 from the LLM API**
- Verify `LLM_API_KEY` and `LLM_API_BASE` in `config.py` are correct.
- If using a local model server, confirm it is running and the base URL matches.

**Stale data / want to re-index the PDF**
- Run `python reset_weaviate.py` to drop the collection, then restart the backend.

**Streamlit cannot reach the backend**
- Confirm the FastAPI server is running on port 8000 before starting Streamlit.
- Check `API_HOST` and `API_PORT` in `config.py` match the backend address.
