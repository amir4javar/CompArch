import asyncio
import logging
import traceback
import uuid
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage

from graph.builder import rag_app
from graph.nodes import register_stream_callback, unregister_stream_callback
from api.lifespan import executor, connect_weaviate

router = APIRouter()


def _run_pipeline_streaming(
    inputs: Dict[str, Any],
    config: Dict[str, Any],
    event_callback: Callable[[Dict], None],
) -> Dict[str, Any]:
    """
    Run the RAG graph synchronously (called inside a thread-pool worker).

    Intermediate pipeline events (e.g. search queries from extract_terms) are
    forwarded via `event_callback`.  Token-by-token output is forwarded
    separately via the session's registered stream callback inside generate_node.
    """
    for update in rag_app.stream(inputs, config=config, stream_mode="updates"):
        node_name = next(iter(update))
        node_output = update[node_name]
        if node_name == "extract_terms":
            event_callback({
                "type": "stream_start",
                "search_queries": node_output.get("search_queries", []),
            })

    final_state = rag_app.get_state(config)
    return final_state.values if final_state else {}


def _run_pipeline(inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Run the RAG graph synchronously without streaming (for REST endpoint)."""
    return rag_app.invoke(inputs, config=config)


# --- Health Check ---
@router.get("/health")
async def health_check():
    try:
        client = connect_weaviate()
        weaviate_ok = client.is_ready()
        client.close()
    except Exception:
        weaviate_ok = False

    return {
        "status": "healthy" if weaviate_ok else "degraded",
        "weaviate": "connected" if weaviate_ok else "disconnected",
    }


# --- Session Management ---
@router.get("/session")
async def create_session():
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    return {"session_id": session_id}


# --- WebSocket Chat Endpoint ---
@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info("WebSocket connected: %s", session_id)

    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "message": "Connected to RAG chat service",
    })

    loop = asyncio.get_running_loop()

    try:
        while True:
            data = await websocket.receive_json()
            question = data.get("question", "").strip()

            if not question:
                await websocket.send_json({"type": "error", "message": "Empty question received"})
                continue

            logger.info("Question from %s: %s", session_id, question)
            await websocket.send_json({"type": "processing"})

            config = {"configurable": {"thread_id": session_id}}
            inputs = {
                "messages": [HumanMessage(content=question)],
                "question": question,
                "session_id": session_id,
            }

            # asyncio.Queue bridges the sync thread → async WebSocket.
            # generate_node calls token_callback(token) for each token,
            # then token_callback(None) as a sentinel when done.
            # _run_pipeline_streaming calls event_callback for search queries.
            async_queue: asyncio.Queue = asyncio.Queue()

            def token_callback(token):
                loop.call_soon_threadsafe(async_queue.put_nowait, token)

            def event_callback(event):
                loop.call_soon_threadsafe(async_queue.put_nowait, event)

            register_stream_callback(session_id, token_callback)
            try:
                pipeline_future = loop.run_in_executor(
                    executor,
                    _run_pipeline_streaming,
                    inputs,
                    config,
                    event_callback,
                )

                # Drain the queue until generate_node sends the None sentinel.
                while True:
                    try:
                        item = await asyncio.wait_for(async_queue.get(), timeout=120.0)
                    except asyncio.TimeoutError:
                        break
                    if item is None:
                        break
                    if isinstance(item, str):
                        await websocket.send_json({"type": "token", "content": item})
                    elif isinstance(item, dict):
                        await websocket.send_json(item)

                result = await pipeline_future

                answer = result.get("answer", "")
                context = result.get("context", [])
                search_queries = result.get("search_queries", [])
                sources = [ctx[:300] for ctx in context[:5]]

                logger.info("Generated answer (%d chars) for %s", len(answer), session_id)
                await websocket.send_json({
                    "type": "complete",
                    "answer": answer,
                    "sources": sources,
                    "search_queries": search_queries,
                })

            except Exception as e:
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": f"Processing error: {str(e)}",
                })
            finally:
                unregister_stream_callback(session_id)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session_id)
    except Exception as e:
        logger.error("WebSocket error for %s: %s", session_id, e)


# --- REST Endpoint (non-streaming) ---
@router.post("/chat/{session_id}")
async def chat_rest(session_id: str, request: dict):
    question = request.get("question", "").strip()
    if not question:
        return {"error": "Empty question"}

    config = {"configurable": {"thread_id": session_id}}
    inputs = {
        "messages": [HumanMessage(content=question)],
        "question": question,
        "session_id": session_id,
    }

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, _run_pipeline, inputs, config)

    return {
        "answer": result.get("answer", ""),
        "sources": result.get("context", [])[:5],
        "search_queries": result.get("search_queries", []),
    }


# --- Debug Endpoint ---
@router.get("/debug/history/{session_id}")
async def debug_history(session_id: str):
    try:
        config = {"configurable": {"thread_id": session_id}}
        state = rag_app.get_state(config)
        if state and state.values:
            messages = state.values.get("messages", [])
            return {
                "session_id": session_id,
                "message_count": len(messages),
                "messages": [
                    {
                        "type": type(m).__name__,
                        "content": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                    }
                    for m in messages
                ],
            }
        return {
            "session_id": session_id,
            "message_count": 0,
            "messages": [],
            "note": "No history found for this session",
        }
    except Exception as e:
        return {"error": str(e)}


# --- Root Endpoint ---
@router.get("/")
async def root():
    return {
        "message": "RAG Chat API",
        "docs": "/docs",
        "websocket": "/ws/chat/{session_id}",
        "rest": "POST /chat/{session_id}",
        "debug": "GET /debug/history/{session_id}",
    }
