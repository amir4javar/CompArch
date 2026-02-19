from typing import List, TypedDict, Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # Conversation history
    question: str                    # Original user question
    reformulated_question: str       # Question + context for retrieval
    context_summary: str             # Summary of conversation context
    search_queries: List[str]        # Extracted key terms (1-3)
    context: List[str]               # Retrieved chunks
    answer: str                      # Final generated answer
