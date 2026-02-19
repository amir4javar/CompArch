import uuid

import streamlit as st

from config import API_HOST, API_PORT


def render_sidebar():
    """Render the settings sidebar."""
    with st.sidebar:
        st.title("⚙️ Settings")
        
        st.divider()
        
        # Session Management
        st.subheader("📌 Session")
        
        # Session ID input
        session_input = st.text_input(
            "Session ID",
            value=st.session_state.session_id or "",
            placeholder="Enter existing or leave empty for new",
            help="Same session ID = conversation history preserved"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 New Session", use_container_width=True):
                st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
                st.session_state.chat_history = []
                st.rerun()
        
        with col2:
            if st.button("✅ Use Session", use_container_width=True):
                if session_input.strip():
                    st.session_state.session_id = session_input.strip()
                else:
                    st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
                st.rerun()
        
        # Display current session
        if st.session_state.session_id:
            st.success(f"Active: `{st.session_state.session_id}`")
        else:
            st.warning("No session active")
        
        st.divider()
        
        # Display Options
        st.subheader("🎨 Display")
        st.session_state.show_sources = st.toggle("Show Sources", value=True)
        
        st.divider()
        
        # Clear Chat
        if st.button("🗑️ Clear Chat History", use_container_width=True, type="secondary"):
            st.session_state.chat_history = []
            st.rerun()
        
        st.divider()
        
        # API Info
        st.subheader("ℹ️ API Info")
        st.code(f"Host: {API_HOST}:{API_PORT}")
        
        # Connection test
        if st.button("🔗 Test Connection", use_container_width=True):
            import requests
            try:
                response = requests.get(f"http://{API_HOST}:{API_PORT}/health", timeout=5)
                if response.status_code == 200:
                    health = response.json()
                    if health.get("status") == "healthy":
                        st.success("✅ API is healthy")
                    else:
                        st.warning(f"⚠️ API status: {health.get('status')}")
                else:
                    st.error("❌ API returned error")
            except Exception as e:
                st.error(f"❌ Cannot connect: {e}")
