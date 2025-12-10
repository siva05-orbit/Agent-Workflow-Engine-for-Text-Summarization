# Agent-Workflow-Engine-for-Text-Summarization
Minimal LangGraph-like backend workflow engine built with FastAPI. Supports nodes, shared state, linear edges, conditional branching, and loops. Implements Option B: rule-based text summarization + refinement workflow.

#How to Run

installation:
pip install fastapi uvicorn pydantic networkx matplotlib websockets
Start Server:
bash
uvicorn main:app --reload
Open http://127.0.0.1:8000/docs for interactive API docs.

Test Workflow using FastAPI docs (http://127.0.0.1:8000/docs)
Create Graph (POST /graph/create):
<img width="1103" height="865" alt="Screenshot 2025-12-11 001330" src="https://github.com/user-attachments/assets/5341d740-472e-4178-803e-f7d4a6b48172" />


Copy the returned graph_id.

Run Graph (POST /graph/run):
<img width="1022" height="865" alt="Screenshot 2025-12-11 001400" src="https://github.com/user-attachments/assets/9e59f7b6-90fb-43bc-bcb9-2d04b43b90e9" />


Check State (GET /graph/state/{run_id}).
<img width="947" height="865" alt="Screenshot 2025-12-11 001430" src="https://github.com/user-attachments/assets/cbb419cc-63de-4aa4-baf6-579e8d26bf7a" />

Websocket:
Use a WebSocket client (for example, “Simple WebSocket Client” browser extension):

Connect to ws://127.0.0.1:8000/ws/graph/run.

Send the JSON payload with your graph_id and initial_state.
<img width="1920" height="1020" alt="Screenshot 2025-12-11 013622" src="https://github.com/user-attachments/assets/82ba9fb4-3299-4a92-8b67-e482b06cb5ac" />

Observe streamed events for each node execution and the final state.

What the Workflow Engine Supports
Nodes: Python functions that read/modify shared state dict

State: Mutable dictionary passed between nodes

Edges: Linear flow via next_node field

Branching: Conditional routing via condition_key, on_true, on_false

Looping: Repeat nodes until condition met (e.g., summary_ok == true)

Tool Registry: Dynamic lookup of functions by name

Async Execution: Non-blocking node execution

In-memory Storage: Graphs and runs persist across requests

Execution Logging: Full step-by-step state history

WebSocket Streaming: Real-time log streaming (ws://localhost:8000/ws/graph/run)

FastAPI Docs: Interactive Swagger UI at /docs

Example Workflow: Rule-based summarization pipeline (split → summarize → merge → refine → loop until summary_ok).

#What I Would Improve with More Time
Persistent Storage: SQLite/Postgres for graphs and runs instead of in-memory dicts

Dynamic Tool Registration: POST /tools/register API endpoint

Graph Validation: Schema checking for cycles, unreachable nodes, missing tools

Parallel Execution: Run independent nodes concurrently with asyncio.gather

Error Recovery: Retry failed nodes, dead-letter queue for permanent failures

Metrics/Observability: Prometheus endpoints, structured logging with OpenTelemetry

Frontend Dashboard: React/Vue UI for graph building and monitoring

Pydantic v2: Migrate to latest validation features

Docker: Containerized deployment with docker-compose

Tests: pytest suite with 90%+ coverage including property-based testing for graph execution
