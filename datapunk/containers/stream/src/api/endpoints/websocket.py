from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
from redis import Redis
from datetime import datetime
import json
from ...core.neurocortex import NeuroCortex

router = APIRouter()
redis_client = Redis(host='localhost', port=6379, db=0)
neurocortex = NeuroCortex()  # Initialize with proper config

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "message": message,
                "timestamp": datetime.now().isoformat()
            })

manager = ConnectionManager()

@router.websocket("/ws/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Store message in Redis cache
            message_data = {
                "client_id": client_id,
                "message": data["message"],
                "timestamp": datetime.now().isoformat(),
                "type": "user"
            }
            redis_client.lpush(f"chat:{client_id}", json.dumps(message_data))
            
            # Process through NeuroCortex
            response = await neurocortex.process_request({
                "text": data["message"],
                "task": "chat",
                "client_id": client_id
            })
            
            # Store response in Redis cache
            response_data = {
                "client_id": client_id,
                "message": response["response"],
                "timestamp": datetime.now().isoformat(),
                "type": "ai"
            }
            redis_client.lpush(f"chat:{client_id}", json.dumps(response_data))
            
            # Send response back to client
            await manager.send_message(response["response"], client_id)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
