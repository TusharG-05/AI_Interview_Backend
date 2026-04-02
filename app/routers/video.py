from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from ..services.camera import CameraService
from ..schemas.shared.api_response import ApiResponse
from pydantic import BaseModel
import time
import asyncio
import json
from ..core.logger import get_logger



logger = get_logger(__name__)

router = APIRouter(prefix="/video", tags=["Video"])

_camera_service = None

def get_camera_service():
    """Lazy-load the camera service to save memory on cloud startup."""
    global _camera_service
    if _camera_service is None:
        from ..services.camera import CameraService
        _camera_service = CameraService()
    return _camera_service

import asyncio

async def frame_generator(interview_id: int):
    """Yields MJPEG frames synchronized with the camera service for a specific session."""
    last_id = -1
    camera_service = get_camera_service()
    while True:
        frame, current_id = camera_service.get_frame(interview_id)
        if frame is None:
            # Placeholder for inactive sessions
            placeholder = b'\xff\xd8\xff\xdb\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c\x20\x24\x2e\x27\x20\x22\x2c\x23\x1c\x1c\x28\x37\x29\x2c\x30\x31\x34\x34\x34\x1f\x27\x39\x3d\x38\x32\x3c\x2e\x33\x34\x32\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1a\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x05\x01\x02\x03\x06\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xf5\x7a\x00\xff\xd9'
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
            await asyncio.sleep(1.0) # Async sleep to avoid blocking thread pool
            continue
        if current_id == last_id:
            await asyncio.sleep(0.01)
            continue
        last_id = current_id
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@router.get("/video_feed")
async def video_feed(interview_id: Optional[int] = Query(None)):
    """Streams the isolated annotated video feed for a specific session."""
    camera_service = get_camera_service()
    if not camera_service.running: camera_service.start()
    
    if interview_id is None:
        # Return a placeholder frame when no interview_id provided
        async def placeholder_generator():
            placeholder = b'\xff\xd8\xff\xdb\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c\x20\x24\x2e\x27\x20\x22\x2c\x23\x1c\x1c\x28\x37\x29\x2c\x30\x31\x34\x34\x34\x1f\x27\x39\x3d\x38\x32\x3c\x2e\x33\x34\x32\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1a\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x05\x01\x02\x03\x06\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xf5\x7a\x00\xff\xd9'
            while True:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
                await asyncio.sleep(1.0)
        
        return StreamingResponse(placeholder_generator(), media_type="multipart/x-mixed-replace; boundary=frame")
    
    return StreamingResponse(frame_generator(interview_id), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/status")
async def proctoring_status(interview_id: int = Query(0)):
    """Returns the current proctoring warning and detection details for a session."""
    camera_service = get_camera_service()
    warning = camera_service.get_current_warning(interview_id)
    detectors_ready = camera_service._detectors_ready
    last_result = camera_service.session_results.get(interview_id, {})
    return ApiResponse(
        status_code=200,
        data={
            "interview_id": interview_id,
            "warning": warning,
            "detectors_ready": detectors_ready,
            "faces_detected": last_result.get("faces", "N/A"),
            "gaze": last_result.get("gaze", "N/A"),
            "detectors": last_result.get("detectors", {}),
        },
        message="OK"
    )


# class EnrollRequest(BaseModel):
#     image_b64: str    # Base64-encoded JPEG/PNG snapshot
#     interview_id: Optional[int] = 0


# @router.post("/enroll", response_model=ApiResponse[dict])
# async def enroll_identity(params: EnrollRequest):
#     """
#     Registers the candidate's face from a snapshot for the current test session.
#     Extracts a DeepFace (SFace) embedding and stores it in memory only.
#     No data is persisted to the database.
#     """
#     import base64, json
#     import numpy as np
#     import cv2
#     from fastapi import HTTPException

#     camera_service = get_camera_service()
#     if not camera_service._detectors_ready:
#         from fastapi import HTTPException as _HTTPException
#         raise _HTTPException(status_code=503, detail="AI detectors are still initializing. Please wait a moment.")

#     try:
#         img_bytes = base64.b64decode(params.image_b64)
#         arr = np.frombuffer(img_bytes, np.uint8)
#         img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
#         if img_bgr is None:
#             from fastapi import HTTPException as _HTTPException
#             raise _HTTPException(status_code=400, detail="Could not decode image.")

#         img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

#         # Detect face
#         from ..services.face import MediaPipeDetector
#         detector = MediaPipeDetector()
#         locs = detector.detect(img_rgb)
#         if not locs:
#             from fastapi import HTTPException as _HTTPException
#             raise _HTTPException(status_code=400, detail="No face detected in the snapshot. Try better lighting or move closer.")

#         # Crop largest face (first result)
#         t, r, b, l = locs[0]
#         face_crop = img_rgb[t:b, l:r]

#         # Get SFace embedding
#         from deepface import DeepFace
#         result = DeepFace.represent(
#             img_path=face_crop,
#             model_name="SFace",
#             enforce_detection=False,
#             detector_backend="skip",
#             align=False
#         )
#         embedding = result[0]["embedding"]

#         # Register in-memory
#         encoding_json = json.dumps({"SFace": embedding})
#         camera_service.face_detector.register_session_identity(params.interview_id, encoding_json)
#         logger.info(f"Enrollment: Identity registered for Session {params.interview_id} (dim={len(embedding)})")

#         return ApiResponse(
#             status_code=200,
#             data={"enrolled": True, "embedding_dim": len(embedding)},
#             message="Identity enrolled. You will now be authenticated in real-time."
#         )

#     except Exception as e:
#         if hasattr(e, 'status_code'):
#             raise
#         logger.error(f"Enrollment error: {e}", exc_info=True)
#         from fastapi import HTTPException as _HTTPException
#         raise _HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")


# @router.delete("/enroll", response_model=ApiResponse[dict])
# async def clear_identity(interview_id: int = Query(0)):
#     """Clears the in-memory enrolled identity when the session stops."""
#     camera_service = get_camera_service()
#     if camera_service.face_detector and hasattr(camera_service.face_detector, 'session_encodings'):
#         camera_service.face_detector.session_encodings.pop(interview_id, None)
#         logger.info(f"Enrollment: Identity cleared for Session {interview_id}")
#     return ApiResponse(
#         status_code=200,
#         data={"cleared": True},
#         message="Identity cleared."
#     )


# --- WebRTC Signaling ---
# aiortc requires native system libs (libsrtp2, libav) that are unavailable on some
# platforms (e.g. HF Spaces). Import it conditionally so startup never crashes.
try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
    from ..services.webrtc import VideoTransformTrack
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    logger.warning("aiortc not installed — WebRTC endpoints are disabled on this deployment.")


class Offer(BaseModel):
    sdp: str
    type: str
    interview_id: Optional[int] = None

# Global set to keep references to PCs
pcs = set()
# Global registry for active sessions: {interview_id: {"pc": pc, "track": video_track}}
active_sessions = {}

@router.post("/offer", response_model=ApiResponse[dict])
async def offer(params: Offer):
    """
    Candidate Connection (Proctoring Source). 
    Registers identity and initializes session-isolated AI.
    """
    logger.info(f"WebRTC: Offer received for interview_id: {params.interview_id}")
    
    if not WEBRTC_AVAILABLE:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="WebRTC (aiortc) is not available on this deployment.")


    # Cloud Optimization: Add Google STUN servers for NAT traversal
    ice_servers = [
        RTCIceServer(urls="stun:stun.l.google.com:19302"),
        RTCIceServer(urls="stun:stun1.l.google.com:19302"),
        RTCIceServer(urls="stun:stun2.l.google.com:19302")
    ]
    configuration = RTCConfiguration(iceServers=ice_servers)
    pc = RTCPeerConnection(configuration=configuration)
    pcs.add(pc)
    
    interview_id = params.interview_id or 0
    active_sessions[interview_id] = {"pc": pc, "track": None}


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

    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)


    # Register Candidate Identity (Embedding) from DB
    from ..core.database import engine
    from sqlmodel import Session, select
    from ..models.db_models import InterviewSession, User
    
    with Session(engine) as db_session:
        # Join session and user to get embedding
        stmt = select(User).join(InterviewSession, InterviewSession.candidate_id == User.id).where(InterviewSession.id == interview_id)
        user = db_session.exec(stmt).first()
        if user and user.face_embedding:
            cam = get_camera_service()
            if cam.face_detector:
                cam.face_detector.register_session_identity(interview_id, user.face_embedding)
                logger.info(f"Identity registered for Session {interview_id}")
            else:
                logger.info(f"Identity registration skipped: Face detector is not initialized in this environment.")


    logger.info(f"WebRTC: Handshake complete for Session {interview_id}")

    return ApiResponse(
        status_code=200,
        data={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
        message="WebRTC offer processed successfully"
    )


@router.post("/watch/{target_session_id}", response_model=ApiResponse[dict])
async def watch(target_session_id: int, params: Offer):
    """
    Admin Ghost Mode: Watch an active session.
    Waits up to 10 seconds for candidate stream to be available.
    """
    if not WEBRTC_AVAILABLE:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="WebRTC (aiortc) is not available on this deployment.")
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
    ice_servers = [
        RTCIceServer(urls="stun:stun.l.google.com:19302"),
        RTCIceServer(urls="stun:stun1.l.google.com:19302"),
        RTCIceServer(urls="stun:stun2.l.google.com:19302")
    ]
    configuration = RTCConfiguration(iceServers=ice_servers)
    pc = RTCPeerConnection(configuration=configuration)
    
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
            data={"error": "Track Error"},
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
