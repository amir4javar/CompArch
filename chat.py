from datetime import datetime

import streamlit as st

from config import API_HOST, API_PORT
from ui.websocket_client import stream_response


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "session_id": None,
        "chat_history": [],
        "is_processing": False,
        "current_response": "",
        "show_sources": True,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_welcome():
    """Render a centered welcome screen when the chat is empty."""
    st.markdown(
        """
        <div class="welcome-container">
            <span class="welcome-icon">🤖</span>
            <h2>RAG Chat Assistant</h2>
            <p>Ask anything about your documents. I use hybrid search and
               have full conversation memory across your session.</p>
            <div class="welcome-chips">
                <div class="welcome-chip">💡 How does branch prediction work?</div>
                <div class="welcome-chip">🔍 Explain cache coherence protocols</div>
                <div class="welcome-chip">📖 What is pipelining in CPU design?</div>
                <div class="welcome-chip">⚡ Compare RISC vs CISC architectures</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history():
    """Display the existing chat history."""
    if not st.session_state.chat_history:
        render_welcome()
        return

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])

                if st.session_state.show_sources and msg.get("sources"):
                    with st.expander(
                        f"📚 {len(msg['sources'])} source chunks", expanded=False
                    ):
                        for i, source in enumerate(msg["sources"][:5], 1):
                            st.markdown(
                                f'<div class="source-box"><strong>{i}.</strong> '
                                f"{source[:350]}…</div>",
                                unsafe_allow_html=True,
                            )

                if msg.get("search_queries"):
                    queries_html = "".join(
                        f'<span class="search-query-tag">🔍 {q}</span>'
                        for q in msg["search_queries"]
                    )
                    st.markdown(
                        f'<div style="margin-top:6px;">{queries_html}</div>',
                        unsafe_allow_html=True,
                    )


def handle_chat_input():
    """Process new user input and stream the response."""
    if prompt := st.chat_input(
        "Message RAG Assistant…", disabled=st.session_state.is_processing
    ):
        if not prompt.strip():
            st.warning("Please enter a question.")
            st.stop()

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().isoformat(),
            }
        )

        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            response_placeholder = st.empty()
            status_placeholder = st.empty()

            result = {
                "full_response": "",
                "sources": [],
                "search_queries": [],
                "error": None,
                "complete": False,
            }

            try:
                st.session_state.is_processing = True

                for event in stream_response(st.session_state.session_id, prompt):
                    etype = event.get("type", "")

                    if etype == "status":
                        status_placeholder.markdown(
                            f'<div style="color:#8e8ea0;font-size:0.82rem;'
                            f'padding:4px 0;">⏳ {event.get("message", "")}</div>',
                            unsafe_allow_html=True,
                        )

                    elif etype == "processing":
                        status_placeholder.markdown(
                            '<div style="color:#8e8ea0;font-size:0.82rem;'
                            'padding:4px 0;">⏳ Processing…</div>',
                            unsafe_allow_html=True,
                        )

                    elif etype == "stream_start":
                        queries = event.get("search_queries", [])
                        result["search_queries"] = queries
                        if queries:
                            tags = "  ".join(f"`{q}`" for q in queries)
                            status_placeholder.markdown(
                                f'<div style="color:#10a37f;font-size:0.82rem;'
                                f'padding:4px 0;">🔍 Searching: {tags}</div>',
                                unsafe_allow_html=True,
                            )

                    elif etype == "token":
                        token = event.get("content", "")
                        result["full_response"] += token
                        response_placeholder.markdown(
                            result["full_response"] + '<span class="streaming-cursor">▌</span>',
                            unsafe_allow_html=True,
                        )
                        status_placeholder.empty()

                    elif etype == "complete":
                        result["full_response"] = event.get(
                            "answer", result["full_response"]
                        )
                        result["sources"] = event.get("sources", [])
                        result["search_queries"] = event.get(
                            "search_queries", result["search_queries"]
                        )
                        result["complete"] = True
                        response_placeholder.markdown(result["full_response"])

                    elif etype == "error":
                        result["error"] = event.get("message", "Unknown error")
                        status_placeholder.error(f"❌ {result['error']}")
                        break

            finally:
                st.session_state.is_processing = False

            if not result["error"] and result["full_response"]:
                if st.session_state.show_sources and result["sources"]:
                    with st.expander(
                        f"📚 {len(result['sources'])} source chunks", expanded=False
                    ):
                        for i, source in enumerate(result["sources"][:5], 1):
                            st.markdown(
                                f'<div class="source-box"><strong>{i}.</strong> '
                                f"{source[:350]}…</div>",
                                unsafe_allow_html=True,
                            )

                if result["search_queries"]:
                    queries_html = "".join(
                        f'<span class="search-query-tag">🔍 {q}</span>'
                        for q in result["search_queries"]
                    )
                    st.markdown(
                        f'<div style="margin-top:6px;">{queries_html}</div>',
                        unsafe_allow_html=True,
                    )

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": result["full_response"],
                        "sources": result["sources"],
                        "search_queries": result["search_queries"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )


def render_footer():
    """Render a minimal footer below the chat."""
    if not st.session_state.session_id:
        return
    msg_count = len(st.session_state.chat_history)
    st.markdown(
        f"""
        <div class="chat-footer">
            <span>Session: {st.session_state.session_id}</span>
            <span>·</span>
            <span>{msg_count} message{"s" if msg_count != 1 else ""}</span>
            <span>·</span>
            <span>{API_HOST}:{API_PORT}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
