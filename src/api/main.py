from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

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
            
            # Process through your agent system
            result = await process_with_agents(query['text'])
            
            # Send response with metadata
            response = {
                "response": result['formatted_response'],
                "metadata": {
                    "confidence": result.get('confidence', 1.0),
                    "data_source": result.get('source'),
                    "execution_time": result.get('execution_time_ms'),
                    "agent_path": result.get('execution_path', [])
                }
            }
            
            await manager.send_personal_message(
                json.dumps(response), 
                websocket
            )
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket)