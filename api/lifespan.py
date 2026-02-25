import logging
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

import weaviate
from fastapi import FastAPI

from config import WEAVIATE_COLLECTION
from vectorstore import get_vectorstore

logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=4)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting up API service...")

    # Check if Weaviate index exists, create it if not
    try:
        client = weaviate.connect_to_local()
        if not client.collections.exists(WEAVIATE_COLLECTION):
            logger.info("Weaviate collection not found — creating index...")
            client.close()
            get_vectorstore()
        else:
            logger.info("Weaviate index already exists.")
            client.close()
    except Exception as e:
        logger.warning("Weaviate check failed: %s — attempting to create index...", e)
        try:
            get_vectorstore()
        except Exception as e2:
            logger.error("Could not create Weaviate index: %s", e2)

    logger.info("API service ready.")
    yield

    logger.info("Shutting down API service...")
    executor.shutdown(wait=False)
