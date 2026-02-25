"""
Unit tests for graph/nodes.py

All external dependencies (LLM, Weaviate, embeddings) are mocked so these
tests run without any network or Docker requirements.
"""
import pytest
from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage

from graph.nodes import (
    contextualize_node,
    extract_key_terms_node,
    retrieve_node,
    generate_node,
    generate_stream,
    register_stream_callback,
    unregister_stream_callback,
    _callbacks,
)
from tests.conftest import make_weaviate_object


# ---------------------------------------------------------------------------
# Node 1: Contextualize
# ---------------------------------------------------------------------------

class TestContextualizeNode:

    def test_single_message_skips_llm_and_returns_question(self, base_state):
        """With no history (one message), LLM should not be called."""
        with patch("graph.nodes.ChatOpenAI") as mock_llm_class:
            result = contextualize_node(base_state)

        mock_llm_class.assert_not_called()
        assert result["question"] == "What is pipelining?"
        assert result["reformulated_question"] == "What is pipelining?"
        assert result["context_summary"] == "No previous context."

    def test_with_history_calls_llm_once(self, state_with_history):
        """LLM should be invoked exactly once when conversation history exists."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content=(
                "USER_CURRENT_QUESTION: What are its hazards?\n"
                "CONTEXT_SUMMARY: The user previously asked about pipelining."
            )
        )
        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            contextualize_node(state_with_history)

        mock_llm.invoke.assert_called_once()

    def test_with_history_parses_question_and_context(self, state_with_history):
        """Question and context summary should be correctly parsed from LLM output."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content=(
                "USER_CURRENT_QUESTION: What are its hazards?\n"
                "CONTEXT_SUMMARY: The user previously asked about pipelining."
            )
        )
        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = contextualize_node(state_with_history)

        assert result["question"] == "What are its hazards?"
        assert "pipelining" in result["context_summary"]

    def test_with_history_builds_reformulated_question(self, state_with_history):
        """Reformulated question should concatenate question + context summary."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content=(
                "USER_CURRENT_QUESTION: What are its hazards?\n"
                "CONTEXT_SUMMARY: The user previously asked about pipelining."
            )
        )
        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = contextualize_node(state_with_history)

        assert "What are its hazards?" in result["reformulated_question"]
        assert "pipelining" in result["reformulated_question"]

    def test_standalone_question_is_not_reformulated(self, state_with_history):
        """When LLM says 'No context needed.', reformulated_question equals question."""
        state_with_history["messages"][-1] = HumanMessage(content="What is cache memory?")
        state_with_history["question"] = "What is cache memory?"

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content=(
                "USER_CURRENT_QUESTION: What is cache memory?\n"
                "CONTEXT_SUMMARY: No context needed."
            )
        )
        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = contextualize_node(state_with_history)

        assert result["reformulated_question"] == "What is cache memory?"

    def test_malformed_llm_output_does_not_raise(self, state_with_history):
        """Unexpected LLM output should be handled gracefully without raising."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Some completely unexpected output")

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = contextualize_node(state_with_history)

        assert "question" in result
        assert "reformulated_question" in result
        assert "context_summary" in result

    def test_empty_messages_falls_back_to_state_question(self):
        """Empty messages list should use state['question'] as fallback."""
        state = {
            "messages": [],
            "session_id": "s1",
            "question": "What is RISC?",
            "reformulated_question": "",
            "context_summary": "",
            "search_queries": [],
            "context": [],
            "answer": "",
        }
        result = contextualize_node(state)
        assert result["question"] == "What is RISC?"


# ---------------------------------------------------------------------------
# Node 2: Extract Key Terms
# ---------------------------------------------------------------------------

class TestExtractKeyTermsNode:

    def test_returns_list_of_strings(self, base_state):
        """search_queries must be a list of non-empty strings."""
        base_state["reformulated_question"] = "What is pipelining?"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="pipelining\ninstruction overlap")

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = extract_key_terms_node(base_state)

        assert isinstance(result["search_queries"], list)
        for term in result["search_queries"]:
            assert isinstance(term, str) and len(term) > 0

    def test_strips_bullet_points_and_dashes(self, base_state):
        """Bullet markers (-, •, *) must be stripped from extracted terms."""
        base_state["reformulated_question"] = "Explain cache memory"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="- cache memory\n• direct-mapped\n* set-associative"
        )
        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = extract_key_terms_node(base_state)

        for term in result["search_queries"]:
            assert not term.startswith("-")
            assert not term.startswith("•")
            assert not term.startswith("*")

    def test_caps_output_at_three_terms(self, base_state):
        """More than 3 lines from the LLM should be truncated to exactly 3."""
        base_state["reformulated_question"] = "Explain RISC vs CISC architecture"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="RISC\nCISC\ninstruction set\narchitecture\nexecution cycles"
        )
        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = extract_key_terms_node(base_state)

        assert len(result["search_queries"]) == 3

    def test_falls_back_to_question_on_empty_llm_output(self, base_state):
        """Empty LLM output must fall back to the original question."""
        base_state["question"] = "What is pipelining?"
        base_state["reformulated_question"] = "What is pipelining?"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="")

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = extract_key_terms_node(base_state)

        assert len(result["search_queries"]) >= 1
        assert result["search_queries"][0] == "What is pipelining?"

    def test_correct_terms_are_extracted(self, base_state):
        """Extracted term content should match LLM output after stripping."""
        base_state["reformulated_question"] = "What is cache memory?"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="cache memory\nmemory hierarchy")

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = extract_key_terms_node(base_state)

        assert "cache memory" in result["search_queries"]
        assert "memory hierarchy" in result["search_queries"]


# ---------------------------------------------------------------------------
# Node 3: Retrieve
# ---------------------------------------------------------------------------

class TestRetrieveNode:

    def _mock_weaviate(self, objects: list):
        """Build a mock Weaviate client that returns the given objects."""
        mock_collection = MagicMock()
        mock_collection.query.hybrid.return_value.objects = objects
        mock_client = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        return mock_client

    def test_returns_context_list(self, base_state):
        """A successful retrieval should return a non-empty context list."""
        base_state["search_queries"] = ["pipelining"]
        obj = make_weaviate_object("chunk_1", "Pipelining text.", 10, 0.85)
        mock_client = self._mock_weaviate([obj])

        with patch("graph.nodes.weaviate.connect_to_local", return_value=mock_client), \
             patch("graph.nodes.embeddings.embed_query", return_value=[0.1] * 1536):
            result = retrieve_node(base_state)

        assert isinstance(result["context"], list)
        assert len(result["context"]) == 1
        assert "Pipelining text." in result["context"][0]

    def test_deduplicates_same_chunk_across_queries(self, base_state):
        """The same chunk_id returned by multiple queries should appear only once."""
        base_state["search_queries"] = ["pipelining", "instruction overlap"]
        duplicate = make_weaviate_object("chunk_1", "Pipelining text.", 10, 0.85)
        mock_client = self._mock_weaviate([duplicate])

        with patch("graph.nodes.weaviate.connect_to_local", return_value=mock_client), \
             patch("graph.nodes.embeddings.embed_query", return_value=[0.1] * 1536):
            result = retrieve_node(base_state)

        assert len(result["context"]) == 1

    def test_results_sorted_by_score_descending(self, base_state):
        """Higher-scored chunks should appear before lower-scored ones."""
        base_state["search_queries"] = ["cache memory"]
        low  = make_weaviate_object("chunk_low",  "Low score text.",  5, 0.50)
        high = make_weaviate_object("chunk_high", "High score text.", 8, 0.95)
        mock_client = self._mock_weaviate([low, high])

        with patch("graph.nodes.weaviate.connect_to_local", return_value=mock_client), \
             patch("graph.nodes.embeddings.embed_query", return_value=[0.1] * 1536):
            result = retrieve_node(base_state)

        assert "High score text." in result["context"][0]
        assert "Low score text."  in result["context"][1]

    def test_caps_results_at_ten(self, base_state):
        """At most 10 chunks should be returned regardless of how many are retrieved."""
        base_state["search_queries"] = ["memory"]
        objects = [
            make_weaviate_object(f"chunk_{i}", f"Text {i}", i, 1.0 - i * 0.04)
            for i in range(20)
        ]
        mock_client = self._mock_weaviate(objects)

        with patch("graph.nodes.weaviate.connect_to_local", return_value=mock_client), \
             patch("graph.nodes.embeddings.embed_query", return_value=[0.1] * 1536):
            result = retrieve_node(base_state)

        assert len(result["context"]) <= 10

    def test_weaviate_client_always_closed(self, base_state):
        """Weaviate client.close() must be called after retrieval."""
        base_state["search_queries"] = ["RISC"]
        mock_client = self._mock_weaviate([])

        with patch("graph.nodes.weaviate.connect_to_local", return_value=mock_client), \
             patch("graph.nodes.embeddings.embed_query", return_value=[0.1] * 1536):
            retrieve_node(base_state)

        mock_client.close.assert_called_once()

    def test_context_strings_include_page_and_score(self, base_state):
        """Each context string should contain the page number and relevance score."""
        base_state["search_queries"] = ["cache"]
        obj = make_weaviate_object("c1", "Cache text.", 42, 0.9500)
        mock_client = self._mock_weaviate([obj])

        with patch("graph.nodes.weaviate.connect_to_local", return_value=mock_client), \
             patch("graph.nodes.embeddings.embed_query", return_value=[0.1] * 1536):
            result = retrieve_node(base_state)

        assert "Page 42"  in result["context"][0]
        assert "0.9500"   in result["context"][0]


# ---------------------------------------------------------------------------
# Node 4: Generate
# ---------------------------------------------------------------------------

class TestGenerateNode:

    def test_tokens_forwarded_to_registered_callback(self, state_ready_to_generate):
        """Each token from generate_stream should reach the registered callback."""
        received = []
        register_stream_callback("test_session_003", lambda t: received.append(t) if t else None)

        with patch("graph.nodes.generate_stream", return_value=iter(["Cache", " memory", " is fast."])):
            generate_node(state_ready_to_generate)

        assert received == ["Cache", " memory", " is fast."]

    def test_none_sentinel_sent_after_all_tokens(self, state_ready_to_generate):
        """The None sentinel must be the last item delivered to the callback."""
        received = []
        register_stream_callback("test_session_003", lambda t: received.append(t))

        with patch("graph.nodes.generate_stream", return_value=iter(["Hello"])):
            generate_node(state_ready_to_generate)

        assert received[-1] is None

    def test_sentinel_sent_even_if_stream_raises(self, state_ready_to_generate):
        """None sentinel must be sent even when generate_stream raises mid-stream."""
        sentinel_received = []
        register_stream_callback(
            "test_session_003",
            lambda t: sentinel_received.append(True) if t is None else None,
        )

        def failing_stream(*args, **kwargs):
            yield "Token1"
            raise RuntimeError("Simulated stream failure")

        with patch("graph.nodes.generate_stream", side_effect=failing_stream):
            try:
                generate_node(state_ready_to_generate)
            except RuntimeError:
                pass

        assert sentinel_received, "Sentinel was not delivered after exception"

    def test_answer_accumulated_correctly(self, state_ready_to_generate):
        """The full answer should be the concatenation of all streamed tokens."""
        register_stream_callback("test_session_003", lambda t: None)

        with patch("graph.nodes.generate_stream", return_value=iter(["Cache", " memory", " is fast."])):
            result = generate_node(state_ready_to_generate)

        assert result["answer"] == "Cache memory is fast."

    def test_works_without_registered_callback(self, state_ready_to_generate):
        """Should not raise when no callback is registered for the session."""
        unregister_stream_callback("test_session_003")

        with patch("graph.nodes.generate_stream", return_value=iter(["Answer"])):
            result = generate_node(state_ready_to_generate)

        assert result["answer"] == "Answer"


# ---------------------------------------------------------------------------
# Stream callback registry
# ---------------------------------------------------------------------------

class TestStreamCallbackRegistry:

    def test_register_adds_callback(self):
        register_stream_callback("reg_test", lambda t: None)
        assert "reg_test" in _callbacks
        unregister_stream_callback("reg_test")

    def test_unregister_removes_callback(self):
        register_stream_callback("unreg_test", lambda t: None)
        unregister_stream_callback("unreg_test")
        assert "unreg_test" not in _callbacks

    def test_unregister_nonexistent_session_is_safe(self):
        """Unregistering a session that was never registered must not raise."""
        unregister_stream_callback("session_that_does_not_exist_xyz")


# ---------------------------------------------------------------------------
# generate_stream (low-level streaming helper)
# ---------------------------------------------------------------------------

class TestGenerateStream:

    def _make_chunk(self, content):
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = content
        return chunk

    def test_yields_tokens_from_openai_stream(self):
        """Each chunk with non-None content should be yielded as a token."""
        mock_stream = [self._make_chunk("Hello"), self._make_chunk(" world"), self._make_chunk("!")]

        with patch("graph.nodes.openai_client") as mock_client:
            mock_client.chat.completions.create.return_value = iter(mock_stream)
            tokens = list(generate_stream("What is cache?", ["[Page 1]: Cache is fast."], "No context."))

        assert tokens == ["Hello", " world", "!"]

    def test_skips_chunks_with_none_content(self):
        """Chunks where delta.content is None should be silently skipped."""
        mock_stream = [self._make_chunk(None), self._make_chunk("Answer"), self._make_chunk(None)]

        with patch("graph.nodes.openai_client") as mock_client:
            mock_client.chat.completions.create.return_value = iter(mock_stream)
            tokens = list(generate_stream("Question", ["Context"], "Summary"))

        assert tokens == ["Answer"]

    def test_question_and_context_included_in_prompt(self):
        """The LLM call must include both the question and context in the prompt."""
        with patch("graph.nodes.openai_client") as mock_client:
            mock_client.chat.completions.create.return_value = iter([])
            list(generate_stream("What is RISC?", ["[Page 5]: RISC overview."], "Some summary"))

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        prompt = call_kwargs["messages"][0]["content"]
        assert "What is RISC?" in prompt
        assert "RISC overview." in prompt
