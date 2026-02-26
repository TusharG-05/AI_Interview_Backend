from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from ..services.camera import CameraService
from ..schemas.api_response import ApiResponse
import time
import asyncio
import json
from ..core.logger import get_logger


router = APIRouter(tags=["Gaze & Face Analysis"])
logger = get_logger(__name__)
camera_service = CameraService()

def frame_generator(interview_id: int):
    """Yields MJPEG frames synchronized with the camera service for a specific session."""
    last_id = -1
    while True:
        frame, current_id = camera_service.get_frame(interview_id)
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
async def video_feed(interview_id: int):
    """Streams the isolated annotated video feed for a specific session."""
    if not camera_service.running: camera_service.start()
    return StreamingResponse(frame_generator(interview_id), media_type="multipart/x-mixed-replace; boundary=frame")



# --- WebRTC Signaling ---
from aiortc import RTCPeerConnection, RTCSessionDescription
from ..services.webrtc import VideoTransformTrack
from pydantic import BaseModel

class Offer(BaseModel):
    sdp: str
    type: str
    interview_id: Optional[int] = None

# Global set to keep references to PCs
pcs = set()
# Global registry for active sessions: {interview_id: {"pc": pc, "track": video_track}}
active_sessions = {}

@router.post("/video/offer", response_model=ApiResponse[dict])
async def offer(params: Offer):
    """
    Candidate Connection (Proctoring Source). 
    Registers identity and initializes session-isolated AI.
    """
    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)
    
    # Cloud Optimization: Add Google STUN servers for NAT traversal
    ice_config = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
            {"urls": "stun:stun2.l.google.com:19302"}
        ]
    }
    pc = RTCPeerConnection(configuration=ice_config)
    
    interview_id = params.interview_id or 0
    active_sessions[interview_id] = {"pc": pc, "track": None}

    # Register Candidate Identity (Embedding) from DB
    from ..core.database import engine
    from sqlmodel import Session, select
    from ..models.db_models import InterviewSession, User
    
    with Session(engine) as db_session:
        # Join session and user to get embedding
        stmt = select(User).join(InterviewSession, InterviewSession.candidate_id == User.id).where(InterviewSession.id == interview_id)
        user = db_session.exec(stmt).first()
        if user and user.face_embedding:
            camera_service.face_detector.register_session_identity(interview_id, user.face_embedding)
            logger.info(f"Identity registered for Session {interview_id}")

    logger.info(f"WebRTC: New Candidate Connection {interview_id}")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState in ["failed", "closed"]:
            await pc.close()
            if interview_id in active_sessions and active_sessions[interview_id]["pc"] == pc:
                del active_sessions[interview_id]
                logger.info(f"WebRTC: Candidate {interview_id} Disconnected")

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            # 1. Wrap with AI
            local_track = VideoTransformTrack(track, interview_id=interview_id)
            # 2. Add to PC (Echo back to candidate)
            pc.addTrack(local_track)
            # 3. Register for Admin Ghost Mode
            active_sessions[interview_id]["track"] = local_track
            logger.info(f"WebRTC: Track registered for Session {interview_id}")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return ApiResponse(
        status_code=200,
        data={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
        message="WebRTC offer processed successfully"
    )

@router.post("/video/watch/{target_session_id}", response_model=ApiResponse[dict])
async def watch(target_session_id: int, params: Offer):
    """
    Admin Ghost Mode: Watch an active session.
    Waits up to 10 seconds for candidate stream to be available.
    """
    import asyncio
    import time
    
    # Check if session exists and wait for track (up to 10 seconds)
    start_time = time.time()
    max_wait = 10
    track = None
    
    while time.time() - start_time < max_wait:
        if target_session_id in active_sessions and active_sessions[target_session_id]["track"]:
            track = active_sessions[target_session_id]["track"]
            break
        await asyncio.sleep(0.5)  # Poll every 500ms
    
    if not track:
        logger.info(f"WebRTC: Admin waiting for Session {target_session_id} - no candidate stream yet")
        return ApiResponse(
            status_code=200,
            data={"status": "WAITING_FOR_CANDIDATE"},
            message="Admin Ghost Mode initialized. Waiting for candidate stream..."
        )

    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)
    
    # Cloud Optimization: Add Google STUN servers for NAT traversal
    ice_config = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
            {"urls": "stun:stun2.l.google.com:19302"}
        ]
    }
    pc = RTCPeerConnection(configuration=ice_config)
    
    # Track the admin PC to prevent garbage collection
    pcs.add(pc)

    logger.info(f"WebRTC: Admin watching Session {target_session_id} - track found, establishing connection")
    
    # Add the Candidate's track to Admin's PC
    try:
        pc.addTrack(track)
        logger.info(f"WebRTC: Track added to Admin PC for Session {target_session_id}")
    except Exception as e:
        logger.error(f"WebRTC: Failed to add track to Admin PC: {e}")
        await pc.close()
        pcs.discard(pc)
        return ApiResponse(
            status_code=500,
            data={"error": str(e)},
            message="Failed to add video track"
        )

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"WebRTC: Admin connection state: {pc.connectionState}")
        if pc.connectionState in ["failed", "closed"]:
            await pc.close()
            pcs.discard(pc)
            logger.info(f"WebRTC: Admin PC closed for Session {target_session_id}")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    logger.info(f"WebRTC: Admin answer sent for Session {target_session_id}")
    return ApiResponse(
        status_code=200,
        data={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
        message="Admin watch session established successfully"
    )

# Shutdown hook to close PCs? 
# In a real app, you'd want to close these on shutdown.
# FastAPI lifespan in server.py could handle this if we exposed `pcs`.
