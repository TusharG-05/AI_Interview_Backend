from typing import Dict, List, Any
from fastapi import WebSocket
from ..core.logger import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """
    Centralized manager for all WebSocket connections.

    Tracks:
    1. Candidate WebSocket connections per interview (one per active session).
    2. Global Admin Dashboard connections that receive real-time broadcast events.
    """

    def __init__(self):
        # {interview_id: WebSocket} — one candidate connection per interview
        self.candidate_connections: Dict[int, WebSocket] = {}

        # {WebSocket: {"id": admin_id, "role": role_str}}
        self.admin_connections: Dict[WebSocket, Dict[str, Any]] = {}

    # ──────────────────────────────────────────
    # CANDIDATE WEBSOCKET
    # ──────────────────────────────────────────

    def register_candidate(self, websocket: WebSocket, interview_id: int) -> None:
        """Register an already-accepted candidate WebSocket."""
        self.candidate_connections[interview_id] = websocket
        logger.info(f"WS: Candidate registered for Interview {interview_id}")

    def unregister_candidate(self, interview_id: int) -> None:
        """Remove a candidate WebSocket registration."""
        self.candidate_connections.pop(interview_id, None)
        logger.info(f"WS: Candidate unregistered from Interview {interview_id}")

    def has_candidate(self, interview_id: int) -> bool:
        return interview_id in self.candidate_connections

    # ──────────────────────────────────────────
    # GLOBAL ADMIN DASHBOARD
    # ──────────────────────────────────────────

    async def connect_admin(self, websocket: WebSocket, admin_id: int, role: str) -> None:
        """Register an already-accepted admin dashboard WebSocket."""
        self.admin_connections[websocket] = {"id": admin_id, "role": role}
        logger.info(
            f"WS: Admin Dashboard connected [{role} id={admin_id}] "
            f"— Total admins: {len(self.admin_connections)}"
        )

    def disconnect_admin(self, websocket: WebSocket) -> None:
        """Unregister an admin dashboard WebSocket."""
        self.admin_connections.pop(websocket, None)
        logger.info(f"WS: Admin Dashboard disconnected — Total admins: {len(self.admin_connections)}")

    async def broadcast_to_admins(self, message: dict) -> None:
        """
        Broadcast a message to all connected admin dashboards.

        Security filter:
        - SUPER_ADMIN receives every event.
        - ADMIN only receives events where session_admin_id matches their own id.
        """
        session_admin_id = message.get("data", {}).get("session_admin_id")

        dead: list[WebSocket] = []
        for ws, info in list(self.admin_connections.items()):
            # Role-based filtering
            if info["role"] != "SUPER_ADMIN" and session_admin_id is not None:
                if info["id"] != session_admin_id:
                    continue

            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"WS: Failed to send to admin id={info['id']}: {e}")
                dead.append(ws)

        for ws in dead:
            self.disconnect_admin(ws)

    # ──────────────────────────────────────────
    # UTILITY
    # ──────────────────────────────────────────

    def get_admin_count(self) -> int:
        return len(self.admin_connections)


# Global singleton
manager = WebSocketManager()
