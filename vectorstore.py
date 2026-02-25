import logging
import uuid

import weaviate

logger = logging.getLogger(__name__)
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate.vectorstores import WeaviateVectorStore

from config import PDF_PATH, WEAVIATE_LOCAL_PORT, WEAVIATE_GRPC_PORT, WEAVIATE_COLLECTION
from embeddings import embeddings


def get_vectorstore():
    client = weaviate.connect_to_local(port=WEAVIATE_LOCAL_PORT, grpc_port=WEAVIATE_GRPC_PORT)

    logger.info("Loading PDF: %s", PDF_PATH)
    loader = PyPDFLoader(PDF_PATH)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", "."]
    )
    docs = loader.load_and_split(text_splitter)
    logger.info("Split into %d chunks.", len(docs))

    # ADD chunk_id to each document
    for idx, doc in enumerate(docs):
        clean_metadata = {
            "chunk_id": f"chunk_{idx}_{uuid.uuid4().hex[:8]}",  # ← NEW: unique chunk ID
        }
        for key, value in doc.metadata.items():
            if key in ["source", "page"]:
                clean_metadata[key] = value
        doc.metadata = clean_metadata

    logger.info("Embedding and indexing chunks (this may take a moment)...")
    vectorstore = WeaviateVectorStore.from_documents(
        docs,
        embeddings,
        client=client,
        index_name=WEAVIATE_COLLECTION
    )
    client.close()
    return vectorstore
