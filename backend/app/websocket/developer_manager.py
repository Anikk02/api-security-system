# app/websocket/developer_manager.py
import logging
from typing import List, Dict, Any
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class DeveloperConnectionManager:
    """Manage WebSocket connections for Developer Panel real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_counter = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_counter += 1
        logger.info(f"Developer WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Developer WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected developer clients."""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Failed to send developer WebSocket message: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_system_health(self, health_data: Dict[str, Any]):
        """Broadcast system health updates (DB, Redis, error rates)."""
        await self.broadcast({
            "type": "system_health_update",
            "payload": health_data
        })

    async def broadcast_new_log(self, log_entry: Dict[str, Any]):
        """Broadcast a new request log entry in real-time."""
        await self.broadcast({
            "type": "new_log",
            "payload": log_entry
        })

    async def broadcast_abuse_alert(self, alert: Dict[str, Any]):
        """Broadcast an abuse detection alert."""
        await self.broadcast({
            "type": "abuse_alert",
            "payload": alert
        })

    async def broadcast_metrics_update(self, metrics: Dict[str, Any]):
        """Broadcast real-time metrics updates (overview, traffic, etc.)."""
        await self.broadcast({
            "type": "metrics_update",
            "payload": metrics
        })

    async def broadcast_client_update(self, client_data: Dict[str, Any]):
        """Broadcast when a client's status or API key changes."""
        await self.broadcast({
            "type": "client_update",
            "payload": client_data
        })


# Global instance
developer_websocket_manager = DeveloperConnectionManager()