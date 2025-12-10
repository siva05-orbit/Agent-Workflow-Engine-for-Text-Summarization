# main.py
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import websockets
import json
import uuid
from engine import (
    GraphCreateRequest,
    RunCreateRequest,
    Graph,
    RunState,
    GRAPHS,
    RUNS,
    run_graph_async,
)

app = FastAPI(title="Workflow Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/graph/create")
async def create_graph(req: GraphCreateRequest):
    graph_id = str(uuid.uuid4())
    nodes_dict = {n.id: n for n in req.nodes}
    graph = Graph(id=graph_id, nodes=nodes_dict, start_node_id=req.start_node_id)
    GRAPHS[graph_id] = graph
    return {"graph_id": graph_id}

@app.post("/graph/run")
async def run_graph_endpoint(req: RunCreateRequest):
    graph = GRAPHS.get(req.graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")

    run_id = str(uuid.uuid4())
    run = RunState(
        id=run_id,
        graph_id=req.graph_id,
        current_node_id=None,
        state=req.initial_state,
        log=[],
        status="running",
    )

    run = await run_graph_async(graph, run)
    return {
        "run_id": run.id,
        "final_state": run.state,
        "log": run.log,
        "status": run.status,
    }

@app.get("/graph/state/{run_id}")
async def get_run_state(run_id: str):
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

#WebSocket: stream logs step-by-step

@app.websocket("/ws/graph/run")
async def websocket_run_graph(ws: WebSocket):
    await ws.accept()
    try:
        # Expect a JSON message: {"graph_id": "...", "initial_state": {...}}
        data = await ws.receive_json()
        graph_id = data.get("graph_id")
        initial_state = data.get("initial_state", {})

        graph = GRAPHS.get(graph_id)
        if graph is None:
            await ws.send_json({"error": "Graph not found"})
            await ws.close()
            return

        run_id = str(uuid.uuid4())
        run = RunState(
            id=run_id,
            graph_id=graph_id,
            current_node_id=None,
            state=initial_state,
            log=[],
            status="running",
        )

        # manual step-by-step execution to stream each step
        current_node_id = graph.start_node_id
        state = run.state
        max_steps = 100

        await ws.send_json({"event": "run_started", "run_id": run_id})

        from engine import execute_node  # 

        for _ in range(max_steps):
            if current_node_id is None:
                run.status = "completed"
                await ws.send_json({"event": "run_completed", "final_state": state})
                break

            node = graph.nodes[current_node_id]
            state, next_id = await execute_node(node, state)

            step = {"node_id": current_node_id, "state": state.copy()}
            run.log.append(step)
            await ws.send_json({"event": "step", "data": step})

            current_node_id = next_id

        run.current_node_id = current_node_id
        run.state = state
        if current_node_id is not None and run.status != "completed":
            run.status = "stopped"
            await ws.send_json({"event": "run_stopped", "state": state})

        RUNS[run.id] = run
        await ws.close()

    except WebSocketDisconnect:
        return
