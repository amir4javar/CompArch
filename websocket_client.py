import asyncio
import json

import websockets

from config import WS_ENDPOINT


async def send_question_async(session_id: str, question: str, result_container: dict):
    """
    Send question via WebSocket and update result_container with streaming response.
    
    Args:
        session_id: The session identifier
        question: User's question
        result_container: Mutable dict to store results (avoids nonlocal issues)
    """
    uri = f"{WS_ENDPOINT}/{session_id}"
    
    try:
        async with websockets.connect(uri, ping_interval=30, ping_timeout=10) as websocket:
            # Wait for connection confirmation
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(response)
            
            if data.get("type") != "connected":
                result_container["error"] = "Connection failed"
                return
            
            result_container["status"] = "Connected"
            
            # Send the question
            await websocket.send(json.dumps({"question": question}))
            
            # Receive streaming response
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=60)
                    data = json.loads(response)
                    
                    msg_type = data.get("type", "")
                    
                    if msg_type == "processing":
                        result_container["status"] = "Processing..."
                    
                    elif msg_type == "stream_start":
                        result_container["search_queries"] = data.get("search_queries", [])
                        result_container["status"] = "Streaming..."
                    
                    elif msg_type == "token":
                        token = data.get("content", "")
                        result_container["full_response"] += token
                        result_container["streaming"] = True
                    
                    elif msg_type == "complete":
                        result_container["sources"] = data.get("sources", [])
                        result_container["search_queries"] = data.get("search_queries", result_container.get("search_queries", []))
                        result_container["full_response"] = data.get("answer", result_container["full_response"])
                        result_container["complete"] = True
                        break
                    
                    elif msg_type == "error":
                        result_container["error"] = data.get("message", "Unknown error")
                        break
                    
                except asyncio.TimeoutError:
                    result_container["error"] = "Response timeout"
                    break
    
    except websockets.exceptions.ConnectionClosed as e:
        result_container["error"] = f"Connection closed: {e}"
    except ConnectionRefusedError:
        result_container["error"] = "Cannot connect to API server. Is it running?"
    except Exception as e:
        result_container["error"] = f"Error: {str(e)}"


def run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def stream_response(session_id: str, question: str):
    """
    Generator that yields streaming events from WebSocket.
    Uses threading to handle async WebSocket in sync Streamlit context.
    """
    import threading
    import queue
    
    event_queue = queue.Queue()
    
    async def websocket_handler():
        uri = f"{WS_ENDPOINT}/{session_id}"
        
        try:
            async with websockets.connect(uri, ping_interval=30, ping_timeout=10) as websocket:
                # Wait for connection
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get("type") != "connected":
                    event_queue.put({"type": "error", "message": "Connection failed"})
                    return
                
                event_queue.put({"type": "status", "message": "Connected"})
                
                # Send question
                await websocket.send(json.dumps({"question": question}))
                
                # Receive stream
                while True:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=60)
                        data = json.loads(response)
                        event_queue.put(data)
                        
                        if data.get("type") in ["complete", "error"]:
                            break
                            
                    except asyncio.TimeoutError:
                        event_queue.put({"type": "error", "message": "Timeout"})
                        break
                        
        except ConnectionRefusedError:
            event_queue.put({"type": "error", "message": "Cannot connect to API. Is it running?"})
        except Exception as e:
            event_queue.put({"type": "error", "message": str(e)})
        finally:
            event_queue.put(None)  # Signal end
    
    def run_websocket():
        asyncio.run(websocket_handler())
    
    # Start WebSocket in background thread
    thread = threading.Thread(target=run_websocket, daemon=True)
    thread.start()
    
    # Yield events from queue
    while True:
        try:
            event = event_queue.get(timeout=120)
            if event is None:
                break
            yield event
        except queue.Empty:
            yield {"type": "error", "message": "Queue timeout"}
            break
