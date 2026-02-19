import asyncio
import uuid
from typing import Any, Dict

import weaviate
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage

from graph.builder import rag_app
from api.lifespan import executor

router = APIRouter()


def run_rag_pipeline(inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the RAG pipeline synchronously (for use in thread pool).
    This is the same approach used in your working __main__ block.
    """
    # This is EXACTLY how your working script does it
    result = rag_app.invoke(inputs, config=config)
    return result


# --- Health Check ---
@router.get("/health")
async def health_check():
    """Check API and Weaviate health."""
    try:
        client = weaviate.connect_to_local()
        weaviate_ok = client.is_ready()
        client.close()
    except:
        weaviate_ok = False
    
    return {
        "status": "healthy" if weaviate_ok else "degraded",
        "weaviate": "connected" if weaviate_ok else "disconnected"
    }


# --- Session Management ---
@router.get("/session")
async def create_session():
    """Create a new session ID."""
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    return {"session_id": session_id}


# --- WebSocket Chat Endpoint ---
@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming chat with conversation history.
    """
    await websocket.accept()
    print(f"🔗 WebSocket connected: {session_id}")
    
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "message": "Connected to RAG chat service"
    })
    
    try:
        while True:
            # Receive question from client
            data = await websocket.receive_json()
            question = data.get("question", "").strip()
            
            if not question:
                await websocket.send_json({
                    "type": "error",
                    "message": "Empty question received"
                })
                continue
            
            print(f"\n{'='*50}")
            print(f"❓ Question from {session_id}: {question}")
            
            await websocket.send_json({"type": "processing"})
            
            # CRITICAL: Config with thread_id for conversation memory
            # This is EXACTLY how your working script does it
            config = {"configurable": {"thread_id": session_id}}
            
            # Input state - EXACTLY how your working script does it
            inputs = {
                "messages": [HumanMessage(content=question)],
                "question": question
            }
            
            try:
                # Run the pipeline in a thread pool (non-blocking for async)
                # Uses invoke() just like your working __main__ block
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    executor,
                    run_rag_pipeline,
                    inputs,
                    config
                )
                
                # Extract results
                answer = result.get("answer", "")
                context = result.get("context", [])
                search_queries = result.get("search_queries", [])
                
                print(f"✅ Generated answer ({len(answer)} chars)")
                
                # Send search queries info
                await websocket.send_json({
                    "type": "stream_start",
                    "search_queries": search_queries
                })
                
                # Stream the answer character by character for nice UX
                for char in answer:
                    await websocket.send_json({
                        "type": "token",
                        "content": char
                    })
                    await asyncio.sleep(0.003)  # Small delay for streaming effect
                
                # Send completion with sources
                sources = [ctx[:300] for ctx in context[:5]]
                
                await websocket.send_json({
                    "type": "complete",
                    "answer": answer,
                    "sources": sources,
                    "search_queries": search_queries
                })
                
            except Exception as e:
                print(f"❌ Error processing question: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": f"Processing error: {str(e)}"
                })
    
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"❌ WebSocket error for {session_id}: {e}")


# --- REST Endpoint (Alternative to WebSocket) ---
@router.post("/chat/{session_id}")
async def chat_rest(session_id: str, request: dict):
    """
    REST endpoint for chat (non-streaming alternative).
    """
    question = request.get("question", "").strip()
    
    if not question:
        return {"error": "Empty question"}
    
    config = {"configurable": {"thread_id": session_id}}
    inputs = {
        "messages": [HumanMessage(content=question)],
        "question": question
    }
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_rag_pipeline, inputs, config)
    
    return {
        "answer": result.get("answer", ""),
        "sources": result.get("context", [])[:5],
        "search_queries": result.get("search_queries", [])
    }


# --- Debug Endpoint ---
@router.get("/debug/history/{session_id}")
async def debug_history(session_id: str):
    """Debug endpoint to check conversation history for a session."""
    try:
        config = {"configurable": {"thread_id": session_id}}
        
        # Get the current state from checkpointer
        state = rag_app.get_state(config)
        
        if state and state.values:
            messages = state.values.get("messages", [])
            return {
                "session_id": session_id,
                "message_count": len(messages),
                "messages": [
                    {
                        "type": type(m).__name__,
                        "content": m.content[:100] + "..." if len(m.content) > 100 else m.content
                    }
                    for m in messages
                ]
            }
        else:
            return {
                "session_id": session_id,
                "message_count": 0,
                "messages": [],
                "note": "No history found for this session"
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
        "debug": "GET /debug/history/{session_id}"
    }
