import uuid

import streamlit as st

from config import API_HOST, API_PORT


def render_sidebar():
    """Render the ChatGPT-style settings sidebar."""
    with st.sidebar:
        # --- App Header ---
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:10px;padding:8px 4px 4px;">
                <div style="width:32px;height:32px;border-radius:8px;background:#10a37f;
                            display:flex;align-items:center;justify-content:center;
                            font-size:1.1rem;flex-shrink:0;">🤖</div>
                <div>
                    <div style="color:#ececec;font-weight:700;font-size:0.95rem;
                                line-height:1.2;">RAG Assistant</div>
                    <div style="color:#8e8ea0;font-size:0.72rem;">Computer Architecture</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # --- New Chat Button ---
        if st.button("＋  New Chat", use_container_width=True, type="primary"):
            st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
            st.session_state.chat_history = []
            st.rerun()

        st.divider()

        # --- Session Management ---
        st.subheader("Session")

        session_input = st.text_input(
            "Session ID",
            value=st.session_state.session_id or "",
            placeholder="Paste existing ID or leave empty",
            help="Reuse a session ID to restore conversation history",
            label_visibility="collapsed",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use ID", use_container_width=True):
                if session_input.strip():
                    st.session_state.session_id = session_input.strip()
                else:
                    st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
                st.session_state.chat_history = []
                st.rerun()
        with col2:
            if st.button("Generate", use_container_width=True):
                st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
                st.session_state.chat_history = []
                st.rerun()

        if st.session_state.session_id:
            st.markdown(
                f"""
                <div style="margin-top:8px;padding:8px 10px;border-radius:8px;
                            background:rgba(16,163,127,0.1);border:1px solid rgba(16,163,127,0.25);
                            display:flex;align-items:center;gap:8px;">
                    <div style="width:7px;height:7px;border-radius:50%;
                                background:#10a37f;flex-shrink:0;"></div>
                    <div style="color:#10a37f;font-size:0.78rem;font-family:monospace;
                                overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                        {st.session_state.session_id}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="margin-top:8px;padding:8px 10px;border-radius:8px;
                            background:rgba(255,255,255,0.04);border:1px solid #3d3d3d;
                            color:#8e8ea0;font-size:0.8rem;">
                    No active session
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()

        # --- Display Options ---
        st.subheader("Options")
        st.session_state.show_sources = st.toggle(
            "Show source citations", value=st.session_state.get("show_sources", True)
        )

        st.divider()

        # --- Clear Chat ---
        if st.button("🗑️  Clear conversation", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

        st.divider()

        # --- API Info (compact) ---
        st.subheader("API")
        st.code(f"{API_HOST}:{API_PORT}", language=None)

        if st.button("Test connection", use_container_width=True):
            import requests

            try:
                resp = requests.get(
                    f"http://{API_HOST}:{API_PORT}/health", timeout=5
                )
                if resp.status_code == 200 and resp.json().get("status") == "healthy":
                    st.success("Connected")
                else:
                    st.warning("Unexpected response")
            except Exception as exc:
                st.error(f"Unreachable — {exc}")
