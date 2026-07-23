# Graph Report - .  (2026-07-23)

## Corpus Check
- Corpus is ~19,550 words - fits in a single context window. You may not need a graph.

## Summary
- 241 nodes · 355 edges · 19 communities (16 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.7)
- Token cost: 82,859 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_LangGraph Pipeline Core|LangGraph Pipeline Core]]
- [[_COMMUNITY_API Routes & Streaming|API Routes & Streaming]]
- [[_COMMUNITY_Streamlit UI|Streamlit UI]]
- [[_COMMUNITY_API Integration Tests|API Integration Tests]]
- [[_COMMUNITY_GPT Embeddings|GPT Embeddings]]
- [[_COMMUNITY_Graphify Skill Docs|Graphify Skill Docs]]
- [[_COMMUNITY_Retrieve Node & Tests|Retrieve Node & Tests]]
- [[_COMMUNITY_API Service & Vectorstore Setup|API Service & Vectorstore Setup]]
- [[_COMMUNITY_Project Docs & Dependencies|Project Docs & Dependencies]]
- [[_COMMUNITY_Test Fixtures|Test Fixtures]]
- [[_COMMUNITY_Generate Stream Tests|Generate Stream Tests]]
- [[_COMMUNITY_Graphify Query Docs|Graphify Query Docs]]
- [[_COMMUNITY_Export Benchmark Doc|Export Benchmark Doc]]
- [[_COMMUNITY_MCP Export Doc|MCP Export Doc]]
- [[_COMMUNITY_Confidence Rubric Doc|Confidence Rubric Doc]]

## God Nodes (most connected - your core abstractions)
1. `GPTEmbeddings` - 13 edges
2. `contextualize_node()` - 13 edges
3. `retrieve_node()` - 13 edges
4. `/graphify Skill (SKILL.md)` - 13 edges
5. `extract_key_terms_node()` - 11 edges
6. `generate_node()` - 11 edges
7. `register_stream_callback()` - 10 edges
8. `GraphState` - 9 edges
9. `unregister_stream_callback()` - 8 edges
10. `generate_stream()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Project graphify Rules (root CLAUDE.md)` --conceptually_related_to--> `RAG Chat Assistant`  [INFERRED]
  CLAUDE.md → README.md
- `TestGPTEmbeddings` --uses--> `GPTEmbeddings`  [INFERRED]
  tests/test_embeddings.py → embeddings.py
- `RAG Chat Assistant` --references--> `requirements.txt (core dependencies)`  [EXTRACTED]
  README.md → requirements.txt
- `requirements-test.txt (test dependencies)` --conceptually_related_to--> `requirements.txt (core dependencies)`  [INFERRED]
  requirements-test.txt → requirements.txt
- `lifespan()` --calls--> `get_vectorstore()`  [EXTRACTED]
  api/lifespan.py → vectorstore.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build/Query/Update Reference Set** — claude_skills_graphify_skill_graphify, claude_skills_graphify_references_extraction_spec_subagent_prompt, claude_skills_graphify_references_query_query_expansion, claude_skills_graphify_references_update_update [INFERRED 0.75]
- **LangGraph RAG Pipeline Stages** — readme_langgraph_contextualize, readme_langgraph_extract_terms, readme_langgraph_retrieve, readme_langgraph_generate [EXTRACTED 1.00]

## Communities (19 total, 3 thin omitted)

### Community 0 - "LangGraph Pipeline Core"
Cohesion: 0.08
Nodes (28): build_graph(), Construct and compile the RAG pipeline graph., contextualize_node(), extract_key_terms_node(), generate_node(), generate_stream(), _get_weaviate_client(), Extracts 1-3 key search terms/queries from the reformulated question. (+20 more)

### Community 1 - "API Routes & Streaming"
Cohesion: 0.09
Nodes (18): Any, chat_rest(), Run the RAG graph synchronously (called inside a thread-pool worker).      Inter, Run the RAG graph synchronously without streaming (for REST endpoint)., _run_pipeline(), _run_pipeline_streaming(), websocket_chat(), register_stream_callback() (+10 more)

### Community 2 - "Streamlit UI"
Cohesion: 0.10
Nodes (21): Streamlit Chat UI for Hybrid Search RAG API Run with: streamlit run streamlit_ap, handle_chat_input(), init_session_state(), Initialize all session state variables., Render a minimal footer below the chat., Render a centered welcome screen when the chat is empty., Display the existing chat history., Process new user input and stream the response. (+13 more)

### Community 3 - "API Integration Tests"
Cohesion: 0.08
Nodes (10): client(), Unit tests for api/routes.py  Uses FastAPI's TestClient with all external depend, On connect, the server must immediately send a 'connected' message., Sending an empty question over WebSocket must return a type='error' message., TestDebugHistoryEndpoint, TestHealthEndpoint, TestRestChatEndpoint, TestRootEndpoint (+2 more)

### Community 4 - "GPT Embeddings"
Cohesion: 0.11
Nodes (13): GPTEmbeddings, Embedding helper that mirrors the OpenAI Python client usage., OpenAI, mock_client(), Unit tests for embeddings.py  Tests the GPTEmbeddings wrapper without making rea, OpenAI client mock that returns a unique vector per text., embed_query should return a plain list of float values., embed_query must make exactly one API call. (+5 more)

### Community 5 - "Graphify Skill Docs"
Cohesion: 0.11
Nodes (20): Graphify Usage Rules (.claude/CLAUDE.md), graphify add <url>, --watch (auto-rebuild on change), FalkorDB Export, Neo4j Export, Wiki Export (--wiki), Node ID Format Rule, Extraction Subagent Prompt Spec (+12 more)

### Community 6 - "Retrieve Node & Tests"
Cohesion: 0.19
Nodes (12): Performs hybrid search for each extracted term and deduplicates results., retrieve_node(), make_weaviate_object(), Build a fake Weaviate query result object., Build a mock Weaviate client that returns the given objects., A successful retrieval should return a non-empty context list., The same chunk_id returned by multiple queries should appear only once., Higher-scored chunks should appear before lower-scored ones. (+4 more)

### Community 7 - "API Service & Vectorstore Setup"
Cohesion: 0.25
Nodes (6): lifespan(), Startup and shutdown events., FastAPI WebSocket Service for Hybrid Search RAG Pipeline Simplified version that, FastAPI, Hybrid Search RAG Pipeline with Conversation History.  This module re-exports th, get_vectorstore()

### Community 8 - "Project Docs & Dependencies"
Cohesion: 0.17
Nodes (13): Project graphify Rules (root CLAUDE.md), Native CLAUDE.md Integration (graphify claude install), Conversation Memory (SQLite / SqliteSaver), Contextualize (pipeline node 1), Extract Terms (pipeline node 2), Generate (pipeline node 4, streaming), LangGraph RAG Pipeline (4-node), Retrieve (pipeline node 3, hybrid search) (+5 more)

### Community 9 - "Test Fixtures"
Cohesion: 0.25
Nodes (7): base_state(), Shared pytest configuration and fixtures.  This module MUST set fake environment, Minimal GraphState: single message, no history., GraphState with multi-turn conversation history., GraphState fully populated and ready for the generate node., state_ready_to_generate(), state_with_history()

### Community 10 - "Generate Stream Tests"
Cohesion: 0.32
Nodes (4): Each chunk with non-None content should be yielded as a token., Chunks where delta.content is None should be silently skipped., The LLM call must include both the question and context in the prompt., TestGenerateStream

### Community 11 - "Graphify Query Docs"
Cohesion: 0.67
Nodes (3): BFS/DFS Traversal Modes, /graphify explain, /graphify path

## Ambiguous Edges - Review These
- `Wiki Export (--wiki)` → `Neo4j Export`  [AMBIGUOUS]
  .claude/skills/graphify/references/exports.md · relation: conceptually_related_to

## Knowledge Gaps
- **17 isolated node(s):** `Fast Path: Existing Graph Query`, `graphify add <url>`, `--watch (auto-rebuild on change)`, `FalkorDB Export`, `MCP Server (--mcp)` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Wiki Export (--wiki)` and `Neo4j Export`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `GPTEmbeddings` connect `GPT Embeddings` to `API Service & Vectorstore Setup`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `retrieve_node()` connect `Retrieve Node & Tests` to `LangGraph Pipeline Core`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **What connects `Startup and shutdown events.`, `Run the RAG graph synchronously (called inside a thread-pool worker).      Inter`, `Run the RAG graph synchronously without streaming (for REST endpoint).` to the rest of the system?**
  _88 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `LangGraph Pipeline Core` be split into smaller, more focused modules?**
  _Cohesion score 0.07716701902748414 - nodes in this community are weakly interconnected._
- **Should `API Routes & Streaming` be split into smaller, more focused modules?**
  _Cohesion score 0.09247311827956989 - nodes in this community are weakly interconnected._
- **Should `Streamlit UI` be split into smaller, more focused modules?**
  _Cohesion score 0.10461538461538461 - nodes in this community are weakly interconnected._