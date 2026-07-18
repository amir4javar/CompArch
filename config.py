import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
PDF_PATH = "computer_architecture.pdf"
WEAVIATE_URL = "http://localhost:8080"
EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "deepseek-v4-pro"  # "gemini-2.5-flash"
LLM_API_BASE = "https://api.gapgpt.app/v1"
LLM_API_KEY = os.getenv("LLM_API_KEY")
EMBED_BATCH_SIZE = 128  # Keep embedding requests well under the provider's 300k token limit

WEAVIATE_COLLECTION = "BookChunk_hist"
WEAVIATE_LOCAL_PORT = 8080
WEAVIATE_GRPC_PORT = 50051

API_HOST = "localhost"
API_PORT = 8000
WS_ENDPOINT = f"ws://{API_HOST}:{API_PORT}/ws/chat"
