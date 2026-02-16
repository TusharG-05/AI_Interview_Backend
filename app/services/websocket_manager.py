from typing import Dict, List, Any
from fastapi import WebSocket
from ..core.logger import get_logger
import json

logger = get_logger(__name__)

class WebSocketManager:
    """
    Centralized manager for all WebSocket connections.
    Handles:
    1. Interview-specific connections (e.g., Candidate receiving warnings)
    2. Admin Dashboard connections (listening to ALL active interviews)
    """
    
    def __init__(self):
        # {interview_id: [WebSocket]}
        self.interview_connections: Dict[int, List[WebSocket]] = {}
        
        # List of admin dashboards listening to global updates
        self.admin_connections: List[WebSocket] = []

    async def connect_interview(self, websocket: WebSocket, interview_id: int):
        await websocket.accept()
        if interview_id not in self.interview_connections:
            self.interview_connections[interview_id] = []
        self.interview_connections[interview_id].append(websocket)
        logger.info(f"WS: Client connected to Interview {interview_id}")

    def disconnect_interview(self, websocket: WebSocket, interview_id: int):
        if interview_id in self.interview_connections:
            if websocket in self.interview_connections[interview_id]:
                self.interview_connections[interview_id].remove(websocket)
            if not self.interview_connections[interview_id]:
                del self.interview_connections[interview_id]
        logger.info(f"WS: Client disconnected from Interview {interview_id}")

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.admin_connections.append(websocket)
        logger.info("WS: Admin Dashboard connected")

    def disconnect_admin(self, websocket: WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)
        logger.info("WS: Admin Dashboard disconnected")

    async def broadcast_to_interview(self, interview_id: int, message: dict):
        """Send message to specific interview participants (Candidate)"""
        if interview_id in self.interview_connections:
            # Copy list to avoid runtime modification errors
            for connection in self.interview_connections[interview_id][:]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"WS Error sending to interview {interview_id}: {e}")
                    self.disconnect_interview(connection, interview_id)

    async def broadcast_to_admins(self, message: dict):
        """Send message to ALL connected admin dashboards"""
        for connection in self.admin_connections[:]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WS Error sending to admin: {e}")
                self.disconnect_admin(connection)

# Global Singleton
manager = WebSocketManager()
