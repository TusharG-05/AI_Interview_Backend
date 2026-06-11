from typing import Dict, List, Any, Set, Optional
from fastapi import WebSocket
from ..core.logger import get_logger
import json
from datetime import datetime, timezone

logger = get_logger(__name__)

class WebSocketManager:
    """
    Centralized manager for all WebSocket connections.
    Handles:
    1. Candidate WebSocket connections per interview
    2. Global Admin Dashboard connections (real-time metrics)
    """
    
    def __init__(self):
        # {interview_id: [WebSocket]} - Candidate connections
        self.candidate_connections: Dict[int, List[WebSocket]] = {}
        
        # Global admin dashboard connections (all admins receive all events, filtered by role)
        # {WebSocket: {"id": admin_id, "role": role}}
        self.admin_connections: Dict[WebSocket, Dict[str, Any]] = {}

    # ========== CANDIDATE WEBSOCKET ==========
    async def connect_candidate(self, websocket: WebSocket, interview_id: int):
        """Register a candidate WebSocket connection for an interview"""
        await websocket.accept()
        if interview_id not in self.candidate_connections:
            self.candidate_connections[interview_id] = []
        self.candidate_connections[interview_id].append(websocket)
        logger.info(f"WS: Candidate connected to Interview {interview_id}")

    async def disconnect_candidate(self, websocket: WebSocket, interview_id: int):
        """Unregister a candidate WebSocket connection"""
        if interview_id in self.candidate_connections:
            if websocket in self.candidate_connections[interview_id]:
                self.candidate_connections[interview_id].remove(websocket)
            if not self.candidate_connections[interview_id]:
                del self.candidate_connections[interview_id]
        logger.info(f"WS: Candidate disconnected from Interview {interview_id}")

    # ========== GLOBAL ADMIN DASHBOARD ==========
    async def connect_admin(self, websocket: WebSocket, admin_id: int, role: str):
        """Register a global admin dashboard connection"""
        # Already accepted in the endpoint before calling this
        self.admin_connections[websocket] = {"id": admin_id, "role": role}
        logger.info(f"WS: Admin Dashboard connected (Global) [{role} {admin_id}] - Total: {len(self.admin_connections)}")

    def disconnect_admin(self, websocket: WebSocket):
        """Unregister a global admin dashboard connection"""
        if websocket in self.admin_connections:
            del self.admin_connections[websocket]
        logger.info(f"WS: Admin Dashboard disconnected (Global) - Total: {len(self.admin_connections)}")

    async def broadcast_to_admins(self, message: dict):
        """Broadcast a message to connected global admin dashboards, filtered by role"""
        # Extract the admin_id who owns this interview session from the payload
        session_admin_id = message.get("data", {}).get("session_admin_id")
        
        for connection, admin_info in list(self.admin_connections.items()):
            # SUPER_ADMIN sees everything. Regular ADMIN only sees events for their own interviews.
            if admin_info["role"] != "SUPER_ADMIN" and session_admin_id is not None:
                if admin_info["id"] != session_admin_id:
                    continue # Skip sending to this admin
            
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WS Error sending to admin: {e}")
                self.disconnect_admin(connection)

    # ========== UTILITY METHODS ==========
    def has_candidate_connection(self, interview_id: int) -> bool:
        """Check if there are any candidate connections for an interview"""
        return interview_id in self.candidate_connections and len(self.candidate_connections[interview_id]) > 0

    def get_admin_connection_count(self) -> int:
        """Get count of connected global admin dashboards"""
        return len(self.admin_connections)

# Global Singleton
manager = WebSocketManager()
