from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from typing import List, Any, Dict, Optional

from src.utils.database import DatabaseConnection
from src.agents.location_resolver import LocationResolverAgent
from src.agents.pm_data_agent import PMDataAgent
from src.graphs.pm_query_workflow import PMQueryWorkflow

app = FastAPI(title="Air Quality Q&A Agent")

# Add CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            query = json.loads(data)
            # Process through your agent system (uses app.state.workflow set at startup)
            query_text = query.get('text')
            if not query_text:
                await manager.send_personal_message(json.dumps({"error": "no text provided"}), websocket)
                continue

            state = await app.state.process_with_agents(query_text)

            response = {
                "response": state.get('response'),
                "metadata": {
                    "confidence": 1.0,
                    "data_source": "db",
                    "execution_time": None,
                    "agent_path": []
                }
            }

            await manager.send_personal_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


class QueryRequest(BaseModel):
    query: str


class SelectionRequest(BaseModel):
    # The workflow state previously returned by /query (serializable dict)
    state: Dict[str, Any]
    # The index selected by the user from the 'locations' list
    selected_index: int


@app.on_event("startup")
async def startup_event():
    """Initialize DB connection and workflow once on app startup."""
    db = DatabaseConnection()
    await db.connect()
    location_agent = LocationResolverAgent(db)
    pm_agent = PMDataAgent(db)
    workflow = PMQueryWorkflow(location_agent, pm_agent)

    # Attach to app state for reuse
    app.state.db = db
    app.state.location_agent = location_agent
    app.state.pm_agent = pm_agent
    app.state.workflow = workflow

    async def _process_with_agents(query_text: str):
        # Use workflow to process and return the state/dict
        state = await workflow.process_query(query_text)
        return state

    app.state.process_with_agents = _process_with_agents


@app.on_event("shutdown")
async def shutdown_event():
    if getattr(app.state, 'db', None):
        await app.state.db.disconnect()


@app.post('/query')
async def post_query(req: Request):
    """Accept a JSON body {"query": "..."} and return the workflow response."""
    body = await req.json()
    query_text = body.get('query') or body.get('text') or ''
    if not query_text:
        return {"error": "No query provided"}

    state = await app.state.process_with_agents(query_text)
    # Debug log for workflow state
    try:
        print(f"[PMQuery] process_query returned waiting_for_user={state.get('waiting_for_user')} locations={len(state.get('locations') or [])}")
    except Exception:
        pass
    # Compose response similar to what the Streamlit frontend expects
    resp = {
        "data": {
            "formatted_response": state.get('response'),
            "raw_data": state.get('pm_data')
        },
        "state": state,
        "query_metadata": {
            "confidence": 1.0,
            "source": "db"
        }
    }

    return resp


@app.post('/query/select')
async def post_query_selection(req: Request):
    """Accept a JSON body {"state": {...}, "selected_index": 0} and continue the workflow.

    This lets the frontend (Streamlit) send the saved workflow state and the user's selection
    so the server can fetch PM data and return the final response.
    """
    body = await req.json()
    state = body.get('state')
    selected_index = body.get('selected_index') if 'selected_index' in body else body.get('selectedIndex')

    if state is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'state' is required and must be a dict")

    if selected_index is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'selected_index' is required")

    # Validate state shape
    if not isinstance(state, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'state' must be a JSON object")

    locations = state.get('locations')
    if not isinstance(locations, list) or len(locations) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No selectable locations found in state")

    # Ensure selected_index is an integer and within bounds
    try:
        idx = int(selected_index)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'selected_index' must be an integer")

    if idx < 0 or idx >= len(locations):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'selected_index' out of range [0, {len(locations)-1}]")

    # If the workflow was not explicitly marked as waiting_for_user, log a warning
    if not state.get('waiting_for_user'):
        print("[PMQuery] Warning: continue_with_selection called but workflow state is not waiting_for_user; proceeding anyway.")

    # Continue the workflow with the user's selection
    try:
        new_state = await app.state.workflow.continue_with_selection(state, idx)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to continue workflow: {e}")

    resp = {
        "data": {
            "formatted_response": new_state.get('response'),
            "raw_data": new_state.get('pm_data')
        },
        "query_metadata": {
            "confidence": 1.0,
            "source": "db"
        }
    }

    return resp