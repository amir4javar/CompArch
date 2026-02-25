"""
Hybrid Search RAG Pipeline with Conversation History.

This module re-exports the public API so that existing imports
(e.g. from api_service.py) continue to work unchanged.
"""

import logging
import uuid

import weaviate

logger = logging.getLogger(__name__)
from langchain_core.messages import HumanMessage

from config import WEAVIATE_COLLECTION
from embeddings import embeddings
from vectorstore import get_vectorstore
from graph.nodes import generate_stream
from graph.builder import rag_app

# Re-export as `app` for backward compatibility with api_service.py
app = rag_app


# --- Main Execution ---
if __name__ == "__main__":
    # Check/create index
    try:
        temp_client = weaviate.connect_to_local()
        if not temp_client.collections.exists(WEAVIATE_COLLECTION):
            temp_client.close()
            get_vectorstore()
        else:
            temp_client.close()
    except Exception as e:
        logger.warning("Index check failed (%s) — creating new index...", e)
        get_vectorstore()

    # Session ID for conversation memory
    session_id = input("🔑 Enter session ID (or press Enter for new session): ").strip()
    if not session_id:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
    print(f"📌 Using session: {session_id}")
    
    config = {"configurable": {"thread_id": session_id}}
    
    while True:
        query = input("\n❓ Enter your question (or 'quit' to exit): ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        # Add user message to input
        inputs = {
            "messages": [HumanMessage(content=query)],
            "question": query
        }
        
        # Invoke the graph with memory
        result = app.invoke(inputs, config=config)
        
        print("\n" + "=" * 40)
        print("🤖 ANSWER:")
        print("=" * 40)
        print(result["answer"])
        print("\n" + "-" * 40)
        print("📄 Sources used:")
        for ctx in result["context"][:5]:
            print(f"  • {ctx}...")
