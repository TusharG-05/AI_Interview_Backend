from typing import Dict, List, Any, Set, Optional
from fastapi import WebSocket
from ..core.logger import get_logger
import json

logger = get_logger(__name__)

class WebSocketManager:
    """
    Centralized manager for all WebSocket connections.
    Handles:
    1. Candidate WebSocket connections per interview
    2. Admin Dashboard connections per interview
    """
    
    def __init__(self):
        # {interview_id: [WebSocket]} - Candidate connections
        self.candidate_connections: Dict[int, List[WebSocket]] = {}
        
        # {interview_id: [WebSocket]} - Admin dashboard connections
        self.admin_dashboard_connections: Dict[int, List[WebSocket]] = {}

    # ========== CANDIDATE WEBSOCKET ==========
    async def connect_candidate(self, websocket: WebSocket, interview_id: int):
        """Register a candidate WebSocket connection for an interview"""
        await websocket.accept()
        if interview_id not in self.candidate_connections:
            self.candidate_connections[interview_id] = []
        self.candidate_connections[interview_id].append(websocket)
        logger.info(f"WS: Candidate connected to Interview {interview_id}")

    def disconnect_candidate(self, websocket: WebSocket, interview_id: int):
        """Unregister a candidate WebSocket connection"""
        if interview_id in self.candidate_connections:
            if websocket in self.candidate_connections[interview_id]:
                self.candidate_connections[interview_id].remove(websocket)
            if not self.candidate_connections[interview_id]:
                del self.candidate_connections[interview_id]
        logger.info(f"WS: Candidate disconnected from Interview {interview_id}")

    # ========== ADMIN DASHBOARD WEBSOCKET ==========
    async def connect_admin_dashboard(self, websocket: WebSocket, interview_id: int):
        """Register an admin dashboard WebSocket connection for an interview"""
        await websocket.accept()
        if interview_id not in self.admin_dashboard_connections:
            self.admin_dashboard_connections[interview_id] = []
        self.admin_dashboard_connections[interview_id].append(websocket)
        logger.info(f"WS: Admin Dashboard connected to Interview {interview_id}")

    def disconnect_admin_dashboard(self, websocket: WebSocket, interview_id: int):
        """Unregister an admin dashboard WebSocket connection"""
        if interview_id in self.admin_dashboard_connections:
            if websocket in self.admin_dashboard_connections[interview_id]:
                self.admin_dashboard_connections[interview_id].remove(websocket)
            if not self.admin_dashboard_connections[interview_id]:
                del self.admin_dashboard_connections[interview_id]
        logger.info(f"WS: Admin Dashboard disconnected from Interview {interview_id}")

    # ========== BROADCASTING ==========
    async def broadcast_to_admin_dashboard(self, interview_id: int, event: dict):
        """Broadcast an event to all connected admin dashboards for an interview"""
        if interview_id not in self.admin_dashboard_connections:
            logger.debug(f"No admin dashboard connections for interview {interview_id}")
            return
        
        # Copy list to avoid runtime modification errors
        for connection in self.admin_dashboard_connections[interview_id][:]:
            try:
                await connection.send_json(event)
                logger.debug(f"Event broadcast to admin dashboard for interview {interview_id}: {event.get('event_type')}")
            except Exception as e:
                logger.error(f"WS Error sending to admin dashboard {interview_id}: {e}")
                self.disconnect_admin_dashboard(connection, interview_id)

    async def broadcast_to_candidate(self, interview_id: int, event: dict):
        """Broadcast an event to all connected candidates for an interview"""
        if interview_id not in self.candidate_connections:
            logger.debug(f"No candidate connections for interview {interview_id}")
            return
        
        # Copy list to avoid runtime modification errors
        for connection in self.candidate_connections[interview_id][:]:
            try:
                await connection.send_json(event)
                logger.debug(f"Event broadcast to candidate for interview {interview_id}: {event.get('event_type')}")
            except Exception as e:
                logger.error(f"WS Error sending to candidate {interview_id}: {e}")
                self.disconnect_candidate(connection, interview_id)

    # ========== UTILITY METHODS ==========
    def has_admin_connections(self, interview_id: int) -> bool:
        """Check if there are any admin dashboard connections for an interview"""
        return interview_id in self.admin_dashboard_connections and len(self.admin_dashboard_connections[interview_id]) > 0

    def get_admin_connection_count(self, interview_id: int) -> int:
        """Get count of connected admin dashboards for an interview"""
        if interview_id in self.admin_dashboard_connections:
            return len(self.admin_dashboard_connections[interview_id])
        return 0

# Global Singleton
manager = WebSocketManager()
