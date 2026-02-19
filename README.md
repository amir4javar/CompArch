# RAG Chat Assistant

A Retrieval-Augmented Generation (RAG) chat application that lets you have multi-turn conversations with a PDF document. It uses hybrid vector + keyword search backed by Weaviate, a LangGraph pipeline for structured reasoning, and a streaming WebSocket interface.

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
| LLM & Embeddings | GapGPT API (OpenAI-compatible) |
| Conversation Memory | SQLite via LangGraph `SqliteSaver` |
| Document Loader | PyPDF |

---

## Project Structure

```
.
├── config.py                        # All configuration constants
├── embeddings.py                    # GapGPTEmbeddings class
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
├── gap_gpt_test_models.py           # Utility: list available GapGPT models
│
├── requirements.txt
└── requirements_auth.txt            # Extended deps (Firebase, Firestore, websocket-client)
```

---

## Prerequisites

- Python 3.10+
- A running **Weaviate** instance on `localhost:8080` (gRPC on `50051`)
- A `computer_architecture.pdf` file placed in the project root (used as the knowledge base)
- Access to the **GapGPT API** at `https://api.gapgpt.app/v1`

### Running Weaviate locally

The easiest way is with Docker:

```bash
docker run -d \
  -p 8080:8080 \
  -p 50051:50051 \
  cr.weaviate.io/semitechnologies/weaviate:latest
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Configuration

All settings live in `config.py`:

```python
PDF_PATH        = "computer_architecture.pdf"
WEAVIATE_URL    = "http://localhost:8080"
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

**List available GapGPT models**:
```bash
python gap_gpt_test_models.py
```
