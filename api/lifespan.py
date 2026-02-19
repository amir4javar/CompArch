from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

import weaviate
from fastapi import FastAPI

from config import WEAVIATE_COLLECTION
from vectorstore import get_vectorstore

executor = ThreadPoolExecutor(max_workers=4)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("🚀 Starting up API service...")
    
    # Check if Weaviate index exists
    try:
        client = weaviate.connect_to_local()
        if not client.collections.exists(WEAVIATE_COLLECTION):
            print("📚 Creating Weaviate index...")
            client.close()
            get_vectorstore()
        else:
            print("✅ Weaviate index already exists.")
            client.close()
    except Exception as e:
        print(f"⚠️ Weaviate check failed: {e}")
        print("📚 Attempting to create index...")
        try:
            get_vectorstore()
        except Exception as e2:
            print(f"❌ Could not create index: {e2}")
    
    print("✅ API service ready!")
    yield
    
    # Shutdown
    print("👋 Shutting down API service...")
    executor.shutdown(wait=False)
