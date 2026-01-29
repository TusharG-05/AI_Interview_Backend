from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from ..services.camera import CameraService
import time
import asyncio
import json

router = APIRouter(tags=["Video"])
camera_service = CameraService()

def frame_generator():
    """Yields MJPEG frames synchronized with the camera service."""
    last_id = -1
    while True:
        frame, current_id = camera_service.get_frame()
        if frame is None:
            placeholder = b'\xff\xd8\xff\xdb\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c\x20\x24\x2e\x27\x20\x22\x2c\x23\x1c\x1c\x28\x37\x29\x2c\x30\x31\x34\x34\x34\x1f\x27\x39\x3d\x38\x32\x3c\x2e\x33\x34\x32\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1a\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x05\x01\x02\x03\x06\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\xf5\x7a\x00\xff\xd9'
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
            time.sleep(0.5)
            continue
        if current_id == last_id:
            time.sleep(0.01)
            continue
        last_id = current_id
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@router.get("/video/video_feed")
async def video_feed():
    """Streams the annotated video feed to the browser (Admin Side)."""
    if not camera_service.running: camera_service.start()
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.websocket("/ws/video")
async def video_websocket(websocket: WebSocket, session_id: Optional[int] = None):
    """Handles external frame processing from candidates (Candidate Side)."""
    await websocket.accept()
    if not camera_service.running: camera_service.start(video_source=None)
    try:
        while True:
            data = await websocket.receive_bytes()
            result = camera_service.process_external_frame(data, session_id=session_id)
            await websocket.send_text(json.dumps(result))
    except WebSocketDisconnect: pass
    except Exception as e: print(f"Video WebSocket Error: {e}")
