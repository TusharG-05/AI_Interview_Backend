import threading
from typing import Optional, List, Dict, Union
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from pydantic import BaseModel
from ..services.camera import CameraService
from ..schemas.shared.api_response import ApiResponse
from ..core.logger import get_logger
from ..auth.dependencies import get_current_user_ws
from ..models.db_models import User
from ..services import websocket_handler as handler

# Proctoring/Heartbeat Limit (Rate limiting handled per-endpoint when needed)
heavy_throttle = []



logger = get_logger(__name__)

router = APIRouter(prefix="/video", tags=["Video"])

# --- Camera Service Singleton ---
def get_camera_service():
    """Returns the CameraService singleton instance."""
    return CameraService()

# --- Proctoring Helpers ---


@router.get("/status", dependencies=heavy_throttle)
async def proctoring_status(interview_id: int = Query(0)):
    """Returns the current proctoring warning and detection details for a session."""
    camera_service = get_camera_service()
    if not camera_service._detectors_ready:
        return ApiResponse(status_code=202, data={"status": "initializing"}, message="Detectors are not ready yet.")
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

@router.websocket("/stream/{interview_id}")
async def websocket_video_stream(
    websocket: WebSocket, 
    interview_id: int,
    current_user: User = Depends(get_current_user_ws)
):
    """
    Binary WebSocket Fallback for Video Proctoring.
    """
    connected = await handler.handle_video_stream_connect(interview_id, websocket, current_user)
    if not connected:
        return
    
    try:
        while True:
            try:
                data = await websocket.receive_bytes()
                if not data:
                    break
                await handler.process_video_frame(interview_id, websocket, data)
            except WebSocketDisconnect:
                raise
            except Exception as e:
                handler.log_error(interview_id, f"Error receiving video bytes: {e}")
                break
                
    except WebSocketDisconnect:
        await handler.handle_video_stream_disconnect(interview_id)
    except Exception as e:
        handler.log_error(interview_id, f"Critical Video Stream error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


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

# Global set to keep references to PCs — prevents garbage collection of open connections.
pcs = set()
# Global registry for active sessions: {interview_id: {"pc": pc, "track": video_track}}
active_sessions = {}
# Lock to guard concurrent mutations from the DataChannel and Track event handlers,
# which can fire simultaneously and cause a race condition when linking channel ↔ track.
_sessions_lock = threading.Lock()

@router.get("/credentials", response_model=ApiResponse[dict])
async def get_webrtc_credentials():
    """
    Returns the ICE/TURN server configuration from environment variables.
    This allows the client to avoid hardcoding sensitive credentials.
    """
    from ..core.config import TURN_USERNAME, TURN_PASSWORD
    
    ice_servers = [
        {"urls": "stun:stun.l.google.com:19302"},
        {"urls": "stun:stun.relay.metered.ca:80"},
    ]
    
    if TURN_USERNAME and TURN_PASSWORD:
        # Return all Metered TURN variants so the browser can use whichever is fastest
        turn_urls = [
            "turn:global.relay.metered.ca:80",
            "turn:global.relay.metered.ca:80?transport=tcp",
            "turn:global.relay.metered.ca:443",
            "turns:global.relay.metered.ca:443?transport=tcp",
        ]
        for url in turn_urls:
            ice_servers.append({
                "urls": url,
                "username": TURN_USERNAME,
                "credential": TURN_PASSWORD
            })
        
    return ApiResponse(
        status_code=200,
        data={"iceServers": ice_servers},
        message="Credentials retrieved successfully"
    )


async def close_all_peer_connections():
    """
    Cleanly close ALL open WebRTC PeerConnections.
    Called by server.py on application shutdown to prevent resource leaks
    when candidates are still connected at the time the server stops.
    """
    import asyncio
    if pcs:
        logger.info(f"WebRTC Shutdown: Closing {len(pcs)} active PeerConnection(s)...")
        await asyncio.gather(*[pc.close() for pc in pcs], return_exceptions=True)
        pcs.clear()
        logger.info("WebRTC Shutdown: All PeerConnections closed.")

@router.post("/offer", response_model=ApiResponse[dict], dependencies=heavy_throttle)
async def offer(params: Offer):
    """
    Candidate Connection (Proctoring Source). 
    Registers identity and initializes session-isolated AI.
    """
    logger.info(f"WebRTC: Offer received for interview_id: {params.interview_id}")
    
    if not WEBRTC_AVAILABLE:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="WebRTC (aiortc) is not available on this deployment.")


    # Cloud Optimization: Add STUN + TURN servers for NAT traversal
    # These should ideally be loaded from environment variables for production.
    from ..core.config import TURN_URL, TURN_USERNAME, TURN_PASSWORD
    
    ice_servers = [
        RTCIceServer(urls="stun:stun.l.google.com:19302"),
        RTCIceServer(urls="stun:stun1.l.google.com:19302"),
    ]
    
    if TURN_URL and TURN_USERNAME and TURN_PASSWORD:
        logger.info("WebRTC: Adding TURN server to configuration")
        ice_servers.append(RTCIceServer(
            urls=TURN_URL,
            username=TURN_USERNAME,
            credential=TURN_PASSWORD
        ))

    configuration = RTCConfiguration(iceServers=ice_servers)
    pc = RTCPeerConnection(configuration=configuration)
    pcs.add(pc)
    
    interview_id = params.interview_id or 0
    
    # 1. Register for Admin Ghost Mode (Identity handled below)
    with _sessions_lock:
        active_sessions[interview_id] = {"pc": pc, "track": None, "channel": None}

    @pc.on("datachannel")
    def on_datachannel(channel):
        logger.info(f"WebRTC: DataChannel received from client for Session {interview_id}")
        with _sessions_lock:
            if interview_id in active_sessions:
                active_sessions[interview_id]["channel"] = channel
                # FIX: Link the channel to an already-initialized track if it arrived first.
                track = active_sessions[interview_id].get("track")
                if track:
                    track.channel = channel
                    logger.info(f"WebRTC: DataChannel retroactively linked to existing track for Session {interview_id}")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"WebRTC: Candidate connection state changed to '{pc.connectionState}' for Session {interview_id}")
        if pc.connectionState in ["failed", "closed", "disconnected"]:
            # FIX: Remove from the pcs set to prevent the memory leak of dangling PeerConnections.
            pcs.discard(pc)
            with _sessions_lock:
                if interview_id in active_sessions and active_sessions[interview_id]["pc"] == pc:
                    del active_sessions[interview_id]
            logger.info(f"WebRTC: Candidate Session {interview_id} cleaned up (state: {pc.connectionState})")
            # Close the connection only on failed/disconnected, not on already-closed
            if pc.connectionState != "closed":
                try:
                    await pc.close()
                except Exception:
                    pass

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            with _sessions_lock:
                # FIX: Safely retrieve the DataChannel even if it arrived before the track.
                current_channel = active_sessions.get(interview_id, {}).get("channel")
                local_track = VideoTransformTrack(track, interview_id=interview_id, channel=current_channel)
                
                # Add to PC (Echo back to candidate)
                pc.addTrack(local_track)
                
                # Register for Admin Ghost Mode
                active_sessions[interview_id]["track"] = local_track
            logger.info(f"WebRTC: Track registered for Session {interview_id} (DataChannel ready: {bool(current_channel)})")

    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # 🔥 DEPLOYMENT FIX: Wait for ICE gathering to complete on the server side
    # This ensures that the Answer sent back to the browser contains the TURN relay 
    # candidates, which are required for Render/HF environments.
    import asyncio
    import time
    gather_timeout = 2.0  # Max wait 2 seconds
    start_gather = time.time()
    while pc.iceGatheringState != "complete" and (time.time() - start_gather) < gather_timeout:
        await asyncio.sleep(0.05)


    # --- FACE RECOGNITION DISABLED ---
    # Identity (face embedding) registration is commented out for now.
    # Face count detection (NO FACE / MULTIPLE FACES) still works.
    # To re-enable, uncomment the block below.
    #
    # from ..core.database import engine
    # from sqlmodel import Session, select
    # from ..models.db_models import InterviewSession, User
    #
    # with Session(engine) as db_session:
    #     # Join session and user to get embedding
    #     stmt = select(User).join(InterviewSession, InterviewSession.candidate_id == User.id).where(InterviewSession.id == interview_id)
    #     user = db_session.exec(stmt).first()
    #     if user and user.face_embedding:
    #         cam = get_camera_service()
    #         if cam.face_detector:
    #             cam.face_detector.register_session_identity(interview_id, user.face_embedding)
    #             logger.info(f"Identity registered for Session {interview_id}")
    #         else:
    #             logger.info(f"Identity registration skipped: Face detector is not initialized in this environment.")


    logger.info(f"WebRTC: Handshake complete for Session {interview_id}")

    return ApiResponse(
        status_code=200,
        data={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
        message="WebRTC offer processed successfully"
    )


@router.post("/watch/{target_session_id}", response_model=ApiResponse[dict], dependencies=heavy_throttle)
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
