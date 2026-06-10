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
    2. Admin Dashboard connections per interview
    3. Global Admin Dashboard connections (real-time metrics)
    """
    
    def __init__(self):
        # {interview_id: [WebSocket]} - Candidate connections
        self.candidate_connections: Dict[int, List[WebSocket]] = {}
        
        # {interview_id: [WebSocket]} - Admin dashboard connections (per-interview)
        self.admin_dashboard_connections: Dict[int, List[WebSocket]] = {}
        
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
        
        # Broadcast to admin dashboard
        await self._broadcast_candidate_status(interview_id, "candidate_connected")

    async def disconnect_candidate(self, websocket: WebSocket, interview_id: int):
        """Unregister a candidate WebSocket connection"""
        if interview_id in self.candidate_connections:
            if websocket in self.candidate_connections[interview_id]:
                self.candidate_connections[interview_id].remove(websocket)
            if not self.candidate_connections[interview_id]:
                del self.candidate_connections[interview_id]
        logger.info(f"WS: Candidate disconnected from Interview {interview_id}")
        
        # Broadcast to admin dashboard
        await self._broadcast_candidate_status(interview_id, "candidate_disconnected")

    async def broadcast_candidate_login(self, interview_id: int, candidate_info: dict):
        """Broadcast candidate login event to all connected admin dashboards"""
        try:
            logger.info(f"DEBUG: Starting candidate_login broadcast for interview {interview_id}")
            # Lazy import to avoid circular dependency
            from .status_manager import get_enriched_admin_data
            
            # Create enriched payload
            enriched_data = get_enriched_admin_data(interview_id)

            payload = {
                "event_type": "candidate_logged_in",
                "data": {
                    **enriched_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }

            # Broadcast to per-interview admin dashboards
            await self.broadcast_to_admin_dashboard(interview_id, payload)
            
            # Broadcast to global admin dashboards
            await self.broadcast_to_admins(payload)
            logger.info(f"DEBUG: Successfully broadcasted candidate_logged_in for interview {interview_id}")
            
        except Exception as e:
            logger.error(f"WS Error broadcasting candidate_logged_in for interview {interview_id}: {e}", exc_info=True)

    async def _broadcast_candidate_status(self, interview_id: int, event_type: str):
        """Helper to broadcast candidate connection status to admins"""
        try:
            logger.info(f"DEBUG: Broadcasting candidate status '{event_type}' for interview {interview_id}")
            # Lazy import to avoid circular dependency
            from .status_manager import get_enriched_admin_data
            
            # Create enriched payload
            enriched_data = get_enriched_admin_data(interview_id)

            payload = {
                "event_type": event_type,
                "data": {
                    **enriched_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }

            # Broadcast to per-interview admin dashboards
            await self.broadcast_to_admin_dashboard(interview_id, payload)
            
            # Broadcast to global admin dashboards
            await self.broadcast_to_admins(payload)
            logger.info(f"DEBUG: Successfully broadcasted {event_type} for interview {interview_id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast {event_type} for interview {interview_id}: {e}")

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
                await self.disconnect_candidate(connection, interview_id)

    # ========== UTILITY METHODS ==========
    def has_admin_connections(self, interview_id: int) -> bool:
        """Check if there are any admin dashboard connections for an interview"""
        return interview_id in self.admin_dashboard_connections and len(self.admin_dashboard_connections[interview_id]) > 0

    def get_admin_connection_count(self, interview_id: int) -> int:
        """Get count of connected admin dashboards for an interview"""
        if interview_id in self.admin_dashboard_connections:
            return len(self.admin_dashboard_connections[interview_id])
        return 0

    # ========== GLOBAL ADMIN DASHBOARD ==========
    # For real-time monitoring across ALL interviews (filtered by admin role)
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

# Global Singleton
manager = WebSocketManager()
