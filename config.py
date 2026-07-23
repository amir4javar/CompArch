import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
PDF_PATH = "computer_architecture.pdf"
EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "deepseek-v4-pro"  # "gemini-2.5-flash"
LLM_API_BASE = "https://api.gapgpt.app/v1"
LLM_API_KEY = os.getenv("LLM_API_KEY")
EMBED_BATCH_SIZE = 128  # Keep embedding requests well under the provider's 300k token limit

WEAVIATE_COLLECTION = "BookChunk_hist"
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_LOCAL_PORT = int(os.getenv("WEAVIATE_LOCAL_PORT", "8080"))
WEAVIATE_GRPC_PORT = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
WEAVIATE_URL = os.getenv("WEAVIATE_URL", f"http://{WEAVIATE_HOST}:{WEAVIATE_LOCAL_PORT}")

API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))
WS_ENDPOINT = f"ws://{API_HOST}:{API_PORT}/ws/chat"
