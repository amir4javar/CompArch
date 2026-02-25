"""
Shared pytest configuration and fixtures.

This module MUST set fake environment variables before any project modules
are imported, because config.py reads them at module level.
"""
import os

# Provide a dummy key so OpenAI client construction doesn't raise at import time.
os.environ.setdefault("LLM_API_KEY", "test-fake-key-for-testing")

import pytest
from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage, AIMessage


# ---------------------------------------------------------------------------
# State fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_state():
    """Minimal GraphState: single message, no history."""
    return {
        "messages": [HumanMessage(content="What is pipelining?")],
        "session_id": "test_session_001",
        "question": "What is pipelining?",
        "reformulated_question": "",
        "context_summary": "",
        "search_queries": [],
        "context": [],
        "answer": "",
    }


@pytest.fixture
def state_with_history():
    """GraphState with multi-turn conversation history."""
    return {
        "messages": [
            HumanMessage(content="What is pipelining?"),
            AIMessage(content="Pipelining overlaps instruction execution across multiple stages."),
            HumanMessage(content="What are its hazards?"),
        ],
        "session_id": "test_session_002",
        "question": "What are its hazards?",
        "reformulated_question": "",
        "context_summary": "",
        "search_queries": [],
        "context": [],
        "answer": "",
    }


@pytest.fixture
def state_ready_to_generate():
    """GraphState fully populated and ready for the generate node."""
    return {
        "messages": [HumanMessage(content="What is cache memory?")],
        "session_id": "test_session_003",
        "question": "What is cache memory?",
        "reformulated_question": "What is cache memory?",
        "context_summary": "No context needed.",
        "search_queries": ["cache memory"],
        "context": [
            "[Page 42] (score: 0.9500): Cache memory is a small, fast memory layer...",
            "[Page 43] (score: 0.8800): Direct-mapped cache uses one cache line per set...",
        ],
        "answer": "",
    }


# ---------------------------------------------------------------------------
# Weaviate mock helpers
# ---------------------------------------------------------------------------

def make_weaviate_object(chunk_id: str, text: str, page: int, score: float) -> MagicMock:
    """Build a fake Weaviate query result object."""
    obj = MagicMock()
    obj.properties = {"chunk_id": chunk_id, "text": text, "page": page}
    obj.metadata.score = score
    return obj
