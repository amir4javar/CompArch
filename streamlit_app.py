"""
Streamlit Chat UI for Hybrid Search RAG API
Run with: streamlit run streamlit_app.py
"""

import streamlit as st

from ui.styles import inject_styles
from ui.sidebar import render_sidebar
from ui.chat import init_session_state, render_chat_history, handle_chat_input, render_footer


st.set_page_config(
    page_title="RAG Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()
init_session_state()
render_sidebar()

if not st.session_state.session_id:
    st.markdown(
        """
        <div class="welcome-container">
            <span class="welcome-icon">🤖</span>
            <h2>RAG Chat Assistant</h2>
            <p>Create or load a session from the sidebar to start chatting
               with your documents.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

render_chat_history()
handle_chat_input()
render_footer()
