import streamlit as st

CUSTOM_CSS = """
<style>
    /* Chat message containers */
    .user-message {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 15px 15px 5px 15px;
        margin: 10px 0;
        margin-left: 20%;
        border-left: 4px solid #1976d2;
    }
    
    .assistant-message {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 15px 15px 15px 5px;
        margin: 10px 0;
        margin-right: 20%;
        border-left: 4px solid #43a047;
    }
    
    .source-box {
        background-color: #fff3e0;
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        font-size: 0.85em;
        border-left: 3px solid #ff9800;
    }
    
    .search-query-tag {
        background-color: #e8f5e9;
        padding: 3px 10px;
        border-radius: 15px;
        margin: 2px;
        display: inline-block;
        font-size: 0.85em;
        color: #2e7d32;
    }
    
    .status-indicator {
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9em;
        display: inline-block;
    }
    
    .status-connected {
        background-color: #c8e6c9;
        color: #2e7d32;
    }
    
    .status-disconnected {
        background-color: #ffcdd2;
        color: #c62828;
    }
    
    .streaming-cursor {
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
</style>
"""


def inject_styles():
    """Inject the custom CSS into the Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
