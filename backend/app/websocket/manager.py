import logging
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    # Manage WebSocket connections for real_time updates

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_counter = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_counter += 1
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total Connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, data: Dict[str, Any]):
        # Broadcast data to all connected clients
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                disconnected.append(connection)

        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    
    async def broadcast_alert(self, alert: Dict[str, Any]):
        # Broadcast a new alert to all clients
        await self.broadcast({
            "type": "new_alert",
            "payload": alert
        })

    async def broadcast_stats_update(self, stats: Dict[str, Any]):
        # Broadcast stats update to all clients

        await self.broadcast({
            'type': "stats_update",
            'payload': stats
        })

#Global instance
websocket_manager = ConnectionManager()