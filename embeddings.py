from typing import List

from openai import OpenAI

from config import LLM_API_BASE, LLM_API_KEY, EMBEDDING_MODEL, EMBED_BATCH_SIZE


openai_client = OpenAI(base_url=LLM_API_BASE, api_key=LLM_API_KEY)


class GapGPTEmbeddings:
    """Embedding helper that mirrors the OpenAI Python client usage."""

    def __init__(self, client: OpenAI, model: str, batch_size: int = 32):
        self._client = client
        self._model = model
        self._batch_size = max(1, batch_size)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        batched_embeddings: List[List[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start:start + self._batch_size]
            response = self._client.embeddings.create(model=self._model, input=batch)
            batched_embeddings.extend(record.embedding for record in response.data)
        return batched_embeddings

    def embed_query(self, text: str) -> List[float]:
        response = self._client.embeddings.create(model=self._model, input=[text])
        return response.data[0].embedding


embeddings = GapGPTEmbeddings(openai_client, EMBEDDING_MODEL, batch_size=EMBED_BATCH_SIZE)
