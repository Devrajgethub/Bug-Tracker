from fastapi import WebSocket
from typing import List, Dict, Any
import json

class ConnectionManager:
    def __init__(self):
        # Map room_id -> list of WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect_to_room(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect_from_room(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast_to_room(self, room_id: int, message: Any):
        if room_id in self.active_connections:
            # Create a copy of the list to iterate over, in case connections are removed during iteration
            connections = self.active_connections[room_id][:]
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be closed, remove it
                    self.disconnect_from_room(connection, room_id)

manager = ConnectionManager()
