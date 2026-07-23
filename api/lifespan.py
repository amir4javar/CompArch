import logging
import time
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

import weaviate
from fastapi import FastAPI

from config import WEAVIATE_COLLECTION, WEAVIATE_HOST, WEAVIATE_LOCAL_PORT, WEAVIATE_GRPC_PORT
from vectorstore import get_vectorstore

logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=4)

WEAVIATE_CHECK_RETRIES = 5
WEAVIATE_CHECK_RETRY_DELAY_SECONDS = 2


def connect_weaviate() -> weaviate.WeaviateClient:
    """Connect to Weaviate using the configured host/ports (env-driven, see config.py)."""
    return weaviate.connect_to_local(
        host=WEAVIATE_HOST, port=WEAVIATE_LOCAL_PORT, grpc_port=WEAVIATE_GRPC_PORT
    )


def _collection_exists(collection_name: str) -> bool:
    """Connect to Weaviate and check collection existence, retrying on transient
    connection errors (e.g. Weaviate container still warming up at startup)."""
    last_error = None
    for attempt in range(1, WEAVIATE_CHECK_RETRIES + 1):
        try:
            client = connect_weaviate()
            try:
                return client.collections.exists(collection_name)
            finally:
                client.close()
        except Exception as e:
            last_error = e
            logger.warning(
                "Weaviate check attempt %d/%d failed: %s",
                attempt, WEAVIATE_CHECK_RETRIES, e,
            )
            if attempt < WEAVIATE_CHECK_RETRIES:
                time.sleep(WEAVIATE_CHECK_RETRY_DELAY_SECONDS)
    raise RuntimeError(f"Could not reach Weaviate after {WEAVIATE_CHECK_RETRIES} attempts") from last_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting up API service...")

    # Check if Weaviate index exists, create it if not. We never index blindly:
    # if Weaviate is unreachable after retries, fail loudly instead of guessing,
    # since a false "missing" reading would duplicate the collection's data.
    try:
        if _collection_exists(WEAVIATE_COLLECTION):
            logger.info("Weaviate index already exists.")
        else:
            logger.info("Weaviate collection not found — creating index...")
            get_vectorstore()
    except Exception as e:
        logger.error("Weaviate startup check failed, not indexing: %s", e)

    logger.info("API service ready.")
    yield

    logger.info("Shutting down API service...")
    executor.shutdown(wait=False)
