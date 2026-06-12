from typing import Dict, List, Any
import json
import asyncio
import redis.asyncio as redis
from fastapi import WebSocket
from ..core.logger import get_logger
from ..core.config import REDIS_URL

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
        
        # Redis PubSub
        self.redis_pubsub_client = None
        self.pubsub_task = None
        self.channel_name = "admin_broadcasts"

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

    async def start_pubsub(self):
        """Start the Redis Pub/Sub listener."""
        try:
            conn_kwargs = {"decode_responses": True}
            if REDIS_URL.startswith("rediss://"):
                conn_kwargs["ssl_cert_reqs"] = "none"
            self.redis_pubsub_client = redis.from_url(REDIS_URL, **conn_kwargs)
            self.pubsub_task = asyncio.create_task(self.listen_to_pubsub())
            logger.info("WS: Redis Pub/Sub started")
        except Exception as e:
            logger.error(f"WS: Failed to start Redis Pub/Sub: {e}")

    async def stop_pubsub(self):
        """Stop the Redis Pub/Sub listener."""
        if self.pubsub_task:
            self.pubsub_task.cancel()
        if self.redis_pubsub_client:
            await self.redis_pubsub_client.close()
            logger.info("WS: Redis Pub/Sub stopped")

    async def listen_to_pubsub(self):
        """Listen to Redis channel and route to local admin websockets."""
        if not self.redis_pubsub_client:
            return
            
        try:
            pubsub = self.redis_pubsub_client.pubsub()
            await pubsub.subscribe(self.channel_name)
            logger.info(f"WS: Subscribed to Redis channel '{self.channel_name}'")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self._send_to_local_admins(data)
                    except json.JSONDecodeError:
                        pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WS: Redis Pub/Sub listen error: {e}")
            # Try to restart in 5 seconds
            await asyncio.sleep(5)
            self.pubsub_task = asyncio.create_task(self.listen_to_pubsub())

    async def broadcast_to_admins(self, message: dict) -> None:
        """
        Publish a message to Redis so all workers receive it.
        """
        if self.redis_pubsub_client:
            try:
                await self.redis_pubsub_client.publish(self.channel_name, json.dumps(message))
            except Exception as e:
                logger.error(f"WS: Redis publish failed: {e}")
                # Fallback to local
                await self._send_to_local_admins(message)
        else:
            # Fallback if no redis
            await self._send_to_local_admins(message)

    async def _send_to_local_admins(self, message: dict) -> None:
        """
        Send a message to locally connected admin dashboards.
        """
        session_admin_id = message.get("data", {}).get("session_admin_id")

        dead: list[WebSocket] = []
        # list() creates a shallow copy so we don't crash if dictionary mutates
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
