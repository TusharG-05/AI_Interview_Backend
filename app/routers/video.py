from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from ..services.camera import CameraService
import time
import asyncio
import json
from ..core.logger import get_logger

from ..utils.response_helpers import StandardizedRoute

router = APIRouter(prefix="/analyze", tags=["Gaze & Face Analysis"], route_class=StandardizedRoute)
camera_service = CameraService()

def frame_generator(session_id: int):
    """Yields MJPEG frames synchronized with the camera service for a specific session."""
    last_id = -1
    while True:
        frame, current_id = camera_service.get_frame(session_id)
        if frame is None:
            # Placeholder for inactive sessions
            placeholder = b'\xff\xd8\xff\xdb\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c\x20\x24\x2e\x27\x20\x22\x2c\x23\x1c\x1c\x28\x37\x29\x2c\x30\x31\x34\x34\x34\x1f\x27\x39\x3d\x38\x32\x3c\x2e\x33\x34\x32\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1a\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x05\x01\x02\x03\x06\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xf5\x7a\x00\xff\xd9'
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
            time.sleep(1.0) # Slow pulse for inactive
            continue
        if current_id == last_id:
            time.sleep(0.01)
            continue
        last_id = current_id
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@router.get("/video/video_feed")
async def video_feed(session_id: int):
    """Streams the isolated annotated video feed for a specific session."""
    if not camera_service.running: camera_service.start()
    return StreamingResponse(frame_generator(session_id), media_type="multipart/x-mixed-replace; boundary=frame")



# --- WebRTC Signaling ---
from aiortc import RTCPeerConnection, RTCSessionDescription
from ..services.webrtc import VideoTransformTrack
from pydantic import BaseModel

class Offer(BaseModel):
    sdp: str
    type: str
    session_id: Optional[int] = None

# Global set to keep references to PCs
pcs = set()
# Global registry for active sessions: {session_id: {"pc": pc, "track": video_track}}
active_sessions = {}

@router.post("/video/offer")
async def offer(params: Offer):
    """
    Candidate Connection (Proctoring Source). 
    Registers identity and initializes session-isolated AI.
    """
    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)
    pc = RTCPeerConnection()
    
    session_id = params.session_id or 0
    active_sessions[session_id] = {"pc": pc, "track": None}

    # Register Candidate Identity (Embedding) from DB
    from ..core.database import engine
    from sqlmodel import Session, select
    from ..models.db_models import InterviewSession, User
    
    with Session(engine) as db_session:
        # Join session and user to get embedding
        stmt = select(User).join(InterviewSession, InterviewSession.candidate_id == User.id).where(InterviewSession.id == session_id)
        user = db_session.exec(stmt).first()
        if user and user.face_embedding:
            camera_service.face_detector.register_session_identity(session_id, user.face_embedding)
            logger.info(f"Identity registered for Session {session_id}")

    logger.info(f"WebRTC: New Candidate Connection {session_id}")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState in ["failed", "closed"]:
            await pc.close()
            if session_id in active_sessions and active_sessions[session_id]["pc"] == pc:
                del active_sessions[session_id]
                logger.info(f"WebRTC: Candidate {session_id} Disconnected")

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            # 1. Wrap with AI
            local_track = VideoTransformTrack(track, session_id=session_id)
            # 2. Add to PC (Echo back to candidate)
            pc.addTrack(local_track)
            # 3. Register for Admin Ghost Mode
            active_sessions[session_id]["track"] = local_track
            logger.info(f"WebRTC: Track registered for Session {session_id}")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

@router.post("/video/watch/{target_session_id}")
async def watch(target_session_id: int, params: Offer):
    """
    Admin Ghost Mode: Watch an active session.
    """
    if target_session_id not in active_sessions or not active_sessions[target_session_id]["track"]:
        # Session not active or no video yet: Admin waits
        return {"status": "WAITING_FOR_CANDIDATE", "message": "Admin Ghost Mode initialized. Waiting for candidate stream..."}

    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)
    pc = RTCPeerConnection()
    
    # We don't store Admin PCs permanently in the session registry, 
    # but we track them to prevent GC (could use a separate set)
    # For now, just a set is fine
    pcs.add(pc)

    logger = get_logger(__name__)
    logger.info(f"WebRTC: Admin watching Session {target_session_id}")
    
    # Add the Candidate's track to Admin's PC
    candidate_track = active_sessions[target_session_id]["track"]
    pc.addTrack(candidate_track)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState in ["failed", "closed"]:
            await pc.close()
            pcs.discard(pc)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

# Shutdown hook to close PCs? 
# In a real app, you'd want to close these on shutdown.
# FastAPI lifespan in server.py could handle this if we exposed `pcs`.
