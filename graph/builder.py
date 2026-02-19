import sqlite3

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

from graph.state import GraphState
from graph.nodes import (
    contextualize_node,
    extract_key_terms_node,
    retrieve_node,
    generate_node,
)


def build_graph():
    """Construct and compile the RAG pipeline graph."""
    workflow = StateGraph(GraphState)

    # Add all nodes
    workflow.add_node("contextualize", contextualize_node)
    workflow.add_node("extract_terms", extract_key_terms_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)

    # Set entry point and edges
    workflow.set_entry_point("contextualize")
    workflow.add_edge("contextualize", "extract_terms")
    workflow.add_edge("extract_terms", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    # Setup SQLite checkpointer for conversation history
    conn = sqlite3.connect("conversations.db", check_same_thread=False)
    memory = SqliteSaver(conn)
    return workflow.compile(checkpointer=memory)


rag_app = build_graph()
