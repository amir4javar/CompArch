import logging
import threading
from typing import Callable, List, Generator, Optional

import weaviate
import weaviate.classes.query as wq
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from config import LLM_MODEL, LLM_API_BASE, LLM_API_KEY, WEAVIATE_COLLECTION
from embeddings import openai_client, embeddings
from graph.state import GraphState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level LLM singleton
# ---------------------------------------------------------------------------
_llm = ChatOpenAI(
    model=LLM_MODEL,
    base_url=LLM_API_BASE,
    api_key=LLM_API_KEY,
)

# ---------------------------------------------------------------------------
# Weaviate lazy singleton with reconnection
# ---------------------------------------------------------------------------
_weaviate_client: Optional[weaviate.WeaviateClient] = None
_weaviate_lock = threading.Lock()


def _get_weaviate_client() -> weaviate.WeaviateClient:
    global _weaviate_client
    with _weaviate_lock:
        if _weaviate_client is None or not _weaviate_client.is_connected():
            _weaviate_client = weaviate.connect_to_local()
    return _weaviate_client


# ---------------------------------------------------------------------------
# Streaming callback registry
# Maps session_id → callable(token: str | None)
# None is the sentinel that signals end-of-stream.
# ---------------------------------------------------------------------------
_callbacks: dict[str, Callable[[Optional[str]], None]] = {}
_callbacks_lock = threading.Lock()


def register_stream_callback(session_id: str, callback: Callable[[Optional[str]], None]) -> None:
    with _callbacks_lock:
        _callbacks[session_id] = callback


def unregister_stream_callback(session_id: str) -> None:
    with _callbacks_lock:
        _callbacks.pop(session_id, None)


# ---------------------------------------------------------------------------
# Node 1: Contextualize
# ---------------------------------------------------------------------------

def contextualize_node(state: GraphState):
    """Analyzes conversation history and creates context summary."""
    messages = state.get("messages", [])

    # Get the current question from the last message
    if messages:
        question = messages[-1].content
    else:
        question = state.get("question", "")

    # If no history or only one message, return as-is
    if len(messages) <= 1:
        logger.debug("No conversation history — using question as-is")
        return {
            "question": question,
            "reformulated_question": question,
            "context_summary": "No previous context.",
        }

    # Get last 8 messages (excluding current) for context
    history_messages = messages[-9:-1] if len(messages) > 8 else messages
    history = "\n".join([
        f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
        for m in history_messages
    ])

    prompt = f"""You are a conversation context analyzer. Your job is to analyze the conversation history and the current user question.

                You MUST output EXACTLY two lines in the following format. No extra text, no explanations, no markdown, no bullet points, no numbering. Just these two lines:

                USER_CURRENT_QUESTION: <the user's exact current question copied verbatim>
                CONTEXT_SUMMARY: <a concise summary of relevant context from history, OR the exact phrase "No context needed." if the question is standalone>

                STRICT RULES:
                - Your output must start with "USER_CURRENT_QUESTION:" on the first line.
                - Your output must have "CONTEXT_SUMMARY:" on the second line.
                - Do NOT add any other lines, headers, labels, or explanations.
                - Do NOT wrap output in quotes, markdown, or code blocks.
                - Do NOT say things like "Here is the output:" or "Sure!" before the two lines.
                - For USER_CURRENT_QUESTION, copy the user's current question EXACTLY word-for-word. Do not rephrase it.
                - For CONTEXT_SUMMARY, summarize ONLY the parts of history that are directly needed to understand the current question. If the current question is fully standalone, write exactly: No context needed.

                EXAMPLES:

                Example 1 (question needs context):
                Conversation History:
                User: What is pipelining?
                Assistant: Pipelining is a technique where multiple instructions are overlapped in execution...
                Current User Question: What are its hazards?

                Correct output:
                USER_CURRENT_QUESTION: What are its hazards?
                CONTEXT_SUMMARY: The user previously asked about pipelining. "Its" refers to pipelining.

                Example 2 (standalone question):
                Conversation History:
                User: What is pipelining?
                Assistant: Pipelining is a technique where multiple instructions are overlapped in execution...
                Current User Question: What is cache memory?

                Correct output:
                USER_CURRENT_QUESTION: What is cache memory?
                CONTEXT_SUMMARY: No context needed.

                Example 3 (multi-turn context):
                Conversation History:
                User: Explain RISC architecture
                Assistant: RISC (Reduced Instruction Set Computer) uses simple instructions that execute in one clock cycle...
                User: How does it compare to CISC?
                Assistant: CISC uses complex instructions that may take multiple cycles, while RISC uses simpler ones...
                Current User Question: Which one is better for mobile devices?

                Correct output:
                USER_CURRENT_QUESTION: Which one is better for mobile devices?
                CONTEXT_SUMMARY: The user has been comparing RISC and CISC architectures. "Which one" refers to RISC vs CISC.

                NOW PROCESS THIS:

                Conversation History:
                {history}

                Current User Question: {question}"""

    response = _llm.invoke(prompt)
    output = response.content.strip()

    # Parse the structured output
    user_question = question  # Default to original
    context_summary = "No context needed."

    if "USER_CURRENT_QUESTION:" in output and "CONTEXT_SUMMARY:" in output:
        try:
            parts = output.split("USER_CURRENT_QUESTION:", 1)[1]
            if "CONTEXT_SUMMARY:" in parts:
                q_part, ctx_part = parts.split("CONTEXT_SUMMARY:", 1)
                user_question = q_part.strip()
                context_summary = ctx_part.strip()
        except Exception:
            context_summary = output
    else:
        context_summary = output

    # Combine for retrieval
    reformulated = (
        f"{user_question}\nContext: {context_summary}"
        if context_summary != "No context needed."
        else user_question
    )

    logger.info("Original question: %s", question)
    logger.debug("Context summary: %s", context_summary)

    return {
        "question": user_question,
        "reformulated_question": reformulated,
        "context_summary": context_summary,
    }


# ---------------------------------------------------------------------------
# Node 2: Extract Key Terms
# ---------------------------------------------------------------------------

def extract_key_terms_node(state: GraphState):
    """Extracts 1-3 key search terms/queries from the reformulated question."""
    reformulated_question = state.get("reformulated_question", state.get("question", ""))

    prompt = f"""You are a search query optimizer. Extract the most important search terms or short phrases from the user's question for retrieval from a knowledge base.

Rules:
- Extract between 1 and 3 key search terms/phrases
- Remove stop words, filler words, and noise
- Focus on domain-specific terms, technical concepts, and key nouns
- Each term should be specific enough to retrieve relevant documents
- Output ONLY the terms, one per line, nothing else

User's Question:
{reformulated_question}

Key Search Terms (1-3 terms, one per line):"""

    response = _llm.invoke(prompt)
    output = response.content.strip()

    # Parse the output into a list of search queries
    search_queries = [
        term.strip().strip('-').strip('•').strip('*').strip()
        for term in output.split('\n')
        if term.strip() and len(term.strip()) > 1
    ]

    # Limit to max 3 queries
    search_queries = search_queries[:3]

    # Fallback: if no terms extracted, use the original question
    if not search_queries:
        search_queries = [state.get("question", reformulated_question)]

    logger.info("Extracted search terms: %s", search_queries)

    return {"search_queries": search_queries}


# ---------------------------------------------------------------------------
# Node 3: Retrieve
# ---------------------------------------------------------------------------

def retrieve_node(state: GraphState):
    """Performs hybrid search for each extracted term and deduplicates results."""
    search_queries = state.get("search_queries", [state.get("question", "")])

    logger.info("Searching with queries: %s", search_queries)

    client = _get_weaviate_client()
    if not client.collections.exists(WEAVIATE_COLLECTION):
        raise RuntimeError(
            f"Weaviate collection '{WEAVIATE_COLLECTION}' does not exist — "
            "check that the PDF was indexed successfully at startup"
        )
    collection = client.collections.get(WEAVIATE_COLLECTION)

    # Collect all results with deduplication by chunk_id
    seen_chunk_ids: set = set()
    context_data = []

    for query in search_queries:
        query_vector = embeddings.embed_query(query)

        response = collection.query.hybrid(
            query=query,
            vector=query_vector,
            alpha=0.5,
            limit=5,
            return_metadata=wq.MetadataQuery(score=True),
        )

        for obj in response.objects:
            properties = obj.properties
            chunk_id = properties.get("chunk_id", "")

            if chunk_id in seen_chunk_ids:
                continue

            seen_chunk_ids.add(chunk_id)
            context_data.append({
                "chunk_id": chunk_id,
                "text": properties.get("text", ""),
                "page": properties.get("page", "Unknown"),
                "score": obj.metadata.score if obj.metadata.score else 0.0,
                "matched_query": query,
            })

    # Sort by score and take top results
    context_data.sort(key=lambda x: x["score"], reverse=True)
    context_data = context_data[:10]

    formatted_context = [
        f"[Page {item['page']}] (score: {item['score']:.4f}): {item['text']}"
        for item in context_data
    ]

    logger.info("Found %d unique chunks via hybrid search", len(formatted_context))

    return {"context": formatted_context}


# ---------------------------------------------------------------------------
# Node 4: Generate
# ---------------------------------------------------------------------------

def generate_node(state: GraphState):
    question = state.get("question", "")
    context = state.get("context", [])
    context_summary = state.get("context_summary", "")
    session_id = state.get("session_id", "")

    with _callbacks_lock:
        callback = _callbacks.get(session_id)

    full_answer = ""
    try:
        for token in generate_stream(question, context, context_summary):
            full_answer += token
            if callback:
                callback(token)
    finally:
        # Always send the sentinel so the WebSocket consumer can exit cleanly,
        # even if generate_stream raises mid-way.
        if callback:
            callback(None)

    logger.info("Generated answer (%d chars)", len(full_answer))
    return {
        "answer": full_answer,
        "messages": [AIMessage(content=full_answer)],
    }


def generate_stream(question: str, context: List[str], context_summary: str = "") -> Generator[str, None, None]:
    """Stream the LLM response token by token."""
    logger.debug("Generating answer (streaming)...")

    context_str = "\n\n".join(context)
    prompt = f"""
    You are a helpful assistant. Answer the user's question based strictly on the provided context.

    Conversation Context Summary: {context_summary}

    Context:
    {context_str}

    Question: {question}

    Answer:
    """

    stream = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
