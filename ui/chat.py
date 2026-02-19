from datetime import datetime

import streamlit as st

from config import API_HOST, API_PORT
from ui.websocket_client import stream_response


def init_session_state():
    """Initialize all session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    
    if "current_response" not in st.session_state:
        st.session_state.current_response = ""
    
    if "show_sources" not in st.session_state:
        st.session_state.show_sources = True


def render_chat_history():
    """Display the existing chat history."""
    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg["content"])
                    
                    # Show sources if available and enabled
                    if st.session_state.show_sources and msg.get("sources"):
                        with st.expander(f"📚 Sources ({len(msg['sources'])} chunks)", expanded=False):
                            for i, source in enumerate(msg["sources"][:5], 1):
                                st.markdown(f"**{i}.** {source[:300]}...")
                    
                    # Show search queries if available
                    if msg.get("search_queries"):
                        st.caption(f"🔍 Search terms: {', '.join(msg['search_queries'])}")


def handle_chat_input():
    """Process new user input and stream the response."""
    if prompt := st.chat_input("Ask a question...", disabled=st.session_state.is_processing):
        if not prompt.strip():
            st.warning("Please enter a question")
            st.stop()
        
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Process and stream response
        with st.chat_message("assistant", avatar="🤖"):
            response_placeholder = st.empty()
            status_placeholder = st.empty()
            
            # Use mutable container instead of nonlocal
            result = {
                "full_response": "",
                "sources": [],
                "search_queries": [],
                "error": None,
                "complete": False
            }
            
            try:
                st.session_state.is_processing = True
                
                # Stream response using generator
                for event in stream_response(st.session_state.session_id, prompt):
                    event_type = event.get("type", "")
                    
                    if event_type == "status":
                        status_placeholder.info(f"⏳ {event.get('message', '')}")
                    
                    elif event_type == "processing":
                        status_placeholder.info("⏳ Processing...")
                    
                    elif event_type == "stream_start":
                        queries = event.get("search_queries", [])
                        result["search_queries"] = queries
                        if queries:
                            status_placeholder.info(f"🔍 Searching: {', '.join(queries)}")
                    
                    elif event_type == "token":
                        token = event.get("content", "")
                        result["full_response"] += token
                        response_placeholder.markdown(result["full_response"] + "▌")
                        status_placeholder.empty()
                    
                    elif event_type == "complete":
                        result["full_response"] = event.get("answer", result["full_response"])
                        result["sources"] = event.get("sources", [])
                        result["search_queries"] = event.get("search_queries", result["search_queries"])
                        result["complete"] = True
                        response_placeholder.markdown(result["full_response"])
                    
                    elif event_type == "error":
                        result["error"] = event.get("message", "Unknown error")
                        status_placeholder.error(f"❌ {result['error']}")
                        break
            
            finally:
                st.session_state.is_processing = False
            
            # Show sources after streaming completes
            if not result["error"] and result["full_response"]:
                if st.session_state.show_sources and result["sources"]:
                    with st.expander(f"📚 Sources ({len(result['sources'])} chunks)", expanded=False):
                        for i, source in enumerate(result["sources"][:5], 1):
                            st.markdown(f"**{i}.** {source[:300]}...")
                
                if result["search_queries"]:
                    st.caption(f"🔍 Search terms: {', '.join(result['search_queries'])}")
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result["full_response"],
                    "sources": result["sources"],
                    "search_queries": result["search_queries"],
                    "timestamp": datetime.now().isoformat()
                })


def render_footer():
    """Render the page footer."""
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"Session: `{st.session_state.session_id}`")
    with col2:
        st.caption(f"Messages: {len(st.session_state.chat_history)}")
    with col3:
        st.caption(f"API: `{API_HOST}:{API_PORT}`")
