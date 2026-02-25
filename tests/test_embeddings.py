"""
Unit tests for embeddings.py

Tests the GPTEmbeddings wrapper without making real API calls.
"""
import pytest
from unittest.mock import MagicMock

from embeddings import GPTEmbeddings


@pytest.fixture
def mock_client():
    """OpenAI client mock that returns a unique vector per text."""
    client = MagicMock()

    def fake_create(model, input):
        response = MagicMock()
        response.data = [MagicMock(embedding=[float(i)] * 4) for i in range(len(input))]
        return response

    client.embeddings.create.side_effect = fake_create
    return client


class TestGPTEmbeddings:

    def test_embed_query_returns_list_of_floats(self, mock_client):
        """embed_query should return a plain list of float values."""
        embedder = GPTEmbeddings(mock_client, "text-embedding-3-large")
        result = embedder.embed_query("What is pipelining?")

        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_embed_query_calls_api_once(self, mock_client):
        """embed_query must make exactly one API call."""
        embedder = GPTEmbeddings(mock_client, "text-embedding-3-large")
        embedder.embed_query("test query")

        mock_client.embeddings.create.assert_called_once()

    def test_embed_documents_empty_list_returns_empty(self, mock_client):
        """embed_documents([]) should return [] without calling the API."""
        embedder = GPTEmbeddings(mock_client, "text-embedding-3-large")
        result = embedder.embed_documents([])

        assert result == []
        mock_client.embeddings.create.assert_not_called()

    def test_embed_documents_returns_one_vector_per_text(self, mock_client):
        """The number of returned vectors must equal the number of input texts."""
        embedder = GPTEmbeddings(mock_client, "text-embedding-3-large")
        texts = ["text one", "text two", "text three"]
        result = embedder.embed_documents(texts)

        assert len(result) == len(texts)

    def test_embed_documents_batches_large_input(self):
        """With batch_size=2 and 5 texts, the API should be called 3 times (2+2+1)."""
        client = MagicMock()
        batch_sizes_seen = []

        def record_call(model, input):
            batch_sizes_seen.append(len(input))
            response = MagicMock()
            response.data = [MagicMock(embedding=[0.0] * 4) for _ in input]
            return response

        client.embeddings.create.side_effect = record_call
        embedder = GPTEmbeddings(client, "text-embedding-3-large", batch_size=2)
        result = embedder.embed_documents(["a", "b", "c", "d", "e"])

        assert len(result) == 5
        assert batch_sizes_seen == [2, 2, 1]

    def test_batch_size_zero_is_clamped_to_one(self):
        """batch_size=0 should be silently clamped to 1 to avoid division errors."""
        client = MagicMock()
        embedder = GPTEmbeddings(client, "any-model", batch_size=0)
        assert embedder._batch_size == 1
