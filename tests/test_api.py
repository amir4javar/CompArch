"""
Unit tests for api/routes.py

Uses FastAPI's TestClient with all external dependencies mocked.
No running Weaviate, LLM, or database connection is required.
"""
import pytest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


# ---------------------------------------------------------------------------
# App fixture — minimal FastAPI app without the startup lifespan
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_healthy_when_weaviate_is_ready(self, client):
        mock_wv = MagicMock()
        mock_wv.is_ready.return_value = True

        with patch("api.routes.weaviate.connect_to_local", return_value=mock_wv):
            response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["weaviate"] == "connected"

    def test_degraded_when_weaviate_not_ready(self, client):
        mock_wv = MagicMock()
        mock_wv.is_ready.return_value = False

        with patch("api.routes.weaviate.connect_to_local", return_value=mock_wv):
            response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "degraded"
        assert body["weaviate"] == "disconnected"

    def test_degraded_when_weaviate_connection_fails(self, client):
        with patch("api.routes.weaviate.connect_to_local", side_effect=Exception("refused")):
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "degraded"


# ---------------------------------------------------------------------------
# GET /session
# ---------------------------------------------------------------------------

class TestSessionEndpoint:

    def test_returns_session_id(self, client):
        response = client.get("/session")
        assert response.status_code == 200
        body = response.json()
        assert "session_id" in body
        assert body["session_id"].startswith("session_")

    def test_each_call_returns_a_unique_id(self, client):
        ids = {client.get("/session").json()["session_id"] for _ in range(5)}
        assert len(ids) == 5, "Session IDs must be unique across calls"


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestRootEndpoint:

    def test_returns_api_links(self, client):
        response = client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert "websocket" in body
        assert "rest" in body
        assert "docs" in body


# ---------------------------------------------------------------------------
# POST /chat/{session_id}  (REST / non-streaming)
# ---------------------------------------------------------------------------

class TestRestChatEndpoint:

    def test_empty_question_returns_error(self, client):
        response = client.post("/chat/test_session", json={"question": ""})
        assert response.status_code == 200
        assert "error" in response.json()

    def test_missing_question_key_returns_error(self, client):
        response = client.post("/chat/test_session", json={})
        assert response.status_code == 200
        assert "error" in response.json()

    def test_valid_question_returns_answer(self, client):
        mock_result = {
            "answer": "Pipelining overlaps instruction execution.",
            "context": ["[Page 10]: Pipelining context."],
            "search_queries": ["pipelining"],
        }
        with patch("api.routes._run_pipeline", return_value=mock_result):
            response = client.post(
                "/chat/test_session",
                json={"question": "What is pipelining?"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "Pipelining overlaps instruction execution."
        assert isinstance(body["sources"], list)
        assert isinstance(body["search_queries"], list)


# ---------------------------------------------------------------------------
# GET /debug/history/{session_id}
# ---------------------------------------------------------------------------

class TestDebugHistoryEndpoint:

    def test_returns_empty_history_for_new_session(self, client):
        mock_state = MagicMock()
        mock_state.values = {"messages": []}

        with patch("api.routes.rag_app") as mock_app:
            mock_app.get_state.return_value = mock_state
            response = client.get("/debug/history/new_session")

        assert response.status_code == 200
        body = response.json()
        assert body["message_count"] == 0
        assert body["messages"] == []

    def test_returns_message_count_for_existing_session(self, client):
        from langchain_core.messages import HumanMessage, AIMessage

        mock_state = MagicMock()
        mock_state.values = {
            "messages": [
                HumanMessage(content="What is pipelining?"),
                AIMessage(content="Pipelining overlaps execution."),
            ]
        }
        with patch("api.routes.rag_app") as mock_app:
            mock_app.get_state.return_value = mock_state
            response = client.get("/debug/history/existing_session")

        assert response.status_code == 200
        assert response.json()["message_count"] == 2

    def test_handles_get_state_exception_gracefully(self, client):
        with patch("api.routes.rag_app") as mock_app:
            mock_app.get_state.side_effect = Exception("DB connection error")
            response = client.get("/debug/history/bad_session")

        assert response.status_code == 200
        assert "error" in response.json()


# ---------------------------------------------------------------------------
# WebSocket /ws/chat/{session_id}
# ---------------------------------------------------------------------------

class TestWebSocketEndpoint:

    def test_connection_sends_connected_message(self, client):
        """On connect, the server must immediately send a 'connected' message."""
        # Patch _run_pipeline_streaming so it sends the sentinel immediately
        # and the handler can exit cleanly.
        def instant_pipeline(inputs, config, event_callback):
            from graph import nodes as _nodes
            cb = _nodes._callbacks.get(inputs.get("session_id", ""))
            if cb:
                cb(None)  # sentinel — no tokens, just end the stream
            return {"answer": "", "context": [], "search_queries": []}

        with patch("api.routes._run_pipeline_streaming", side_effect=instant_pipeline):
            with client.websocket_connect("/ws/chat/test_ws_connect") as ws:
                msg = ws.receive_json()
                assert msg["type"] == "connected"
                assert msg["session_id"] == "test_ws_connect"

    def test_empty_question_returns_error_message(self, client):
        """Sending an empty question over WebSocket must return a type='error' message."""
        def instant_pipeline(inputs, config, event_callback):
            from graph import nodes as _nodes
            cb = _nodes._callbacks.get(inputs.get("session_id", ""))
            if cb:
                cb(None)
            return {}

        with patch("api.routes._run_pipeline_streaming", side_effect=instant_pipeline):
            with client.websocket_connect("/ws/chat/test_ws_empty") as ws:
                ws.receive_json()  # consume 'connected'
                ws.send_json({"question": ""})
                msg = ws.receive_json()
                assert msg["type"] == "error"
