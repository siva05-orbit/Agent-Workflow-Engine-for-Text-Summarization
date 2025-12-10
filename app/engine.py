from typing import Dict, Any, Optional, Callable, List
from pydantic import BaseModel

#models
class NodeConfig(BaseModel):
    id: str
    tool_name: str
    next_node: Optional[str] = None
    condition_key: Optional[str] = None
    condition_value: Optional[Any] = None
    on_true: Optional[str] = None
    on_false: Optional[str] = None

class Graph(BaseModel):
    id: str
    nodes: Dict[str, NodeConfig]
    start_node_id: str

class RunState(BaseModel):
    id: str
    graph_id: str
    current_node_id: Optional[str]
    state: Dict[str, Any]
    log: List[Dict[str, Any]]
    status: str

class GraphCreateRequest(BaseModel):
    start_node_id: str
    nodes: List[NodeConfig]

class RunCreateRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any]

#TOOLS (example rule based functions)

ToolFn = Callable[[Dict[str, Any]], Dict[str, Any]]
TOOLS: Dict[str, ToolFn] = {}

def register_tool(name: str):
    def decorator(fn: ToolFn):
        TOOLS[name] = fn
        return fn
    return decorator

#fake rules for summarization
@register_tool("split_text")  
def split_text(state: Dict[str, Any]) -> Dict[str, Any]:
    text = state.get("text", "")
    chunk_size = state.get("chunk_size", 50)
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    state["chunks"] = chunks
    return state

@register_tool("generate_summaries")
def generate_summaries(state: Dict[str, Any]) -> Dict[str, Any]:
    chunks = state.get("chunks", [])
    summaries = [c[:20] for c in chunks]
    state["summaries"] = summaries
    return state

@register_tool("merge_summaries")
def merge_summaries(state: Dict[str, Any]) -> Dict[str, Any]:
    summaries = state.get("summaries", [])
    state["merged_summary"] = " ".join(summaries)
    return state

@register_tool("refine_summary")
def refine_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    max_len = state.get("max_len", 100)
    summary = state.get("merged_summary", "")
    final = summary[:max_len]
    state["final_summary"] = final
    state["summary_ok"] = len(final) <= max_len
    return state

GRAPHS: Dict[str, Graph] = {}
RUNS: Dict[str, RunState] = {}

#Async Engine

async def execute_node(node: NodeConfig, state: Dict[str, Any]) -> (Dict[str, Any], Optional[str]):
    tool = TOOLS[node.tool_name]
    new_state = tool(state)

    if node.condition_key is not None:
        value = new_state.get(node.condition_key)
        if value == node.condition_value:
            return new_state, node.on_true
        else:
            return new_state, node.on_false

    return new_state, node.next_node

async def run_graph_async(graph: Graph, run: RunState) -> RunState:
    current_node_id = graph.start_node_id if run.current_node_id is None else run.current_node_id
    state = run.state
    max_steps = 100

    for _ in range(max_steps):
        if current_node_id is None:
            run.status = "completed"
            break

        node = graph.nodes[current_node_id]
        state, next_id = await execute_node(node, state)
        run.log.append({"node_id": current_node_id, "state": state.copy()})
        current_node_id = next_id

    run.current_node_id = current_node_id
    run.state = state
    if current_node_id is not None and run.status != "completed":
        run.status = "stopped"

    RUNS[run.id] = run
    return run

