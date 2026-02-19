"""
Streamlit Chat UI for Hybrid Search RAG API
Run with: streamlit run streamlit_app.py
"""

import streamlit as st

from ui.styles import inject_styles
from ui.sidebar import render_sidebar
from ui.chat import init_session_state, render_chat_history, handle_chat_input, render_footer


# --- Page Configuration ---
st.set_page_config(
    page_title="RAG Chat Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_styles()
init_session_state()
render_sidebar()

# --- Main Chat Area ---
st.title("🤖 RAG Chat Assistant")
st.caption("Ask questions about your documents with conversation memory")

# Check if session is active
if not st.session_state.session_id:
    st.info("👈 Please create or enter a session ID in the sidebar to start chatting.")
    st.stop()

render_chat_history()
handle_chat_input()
render_footer()
