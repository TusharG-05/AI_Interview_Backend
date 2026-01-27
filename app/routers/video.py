from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.camera import CameraService
import time
import asyncio
import json

router = APIRouter()
camera_service = CameraService()

@router.websocket("/ws/video")
async def video_websocket(websocket: WebSocket):
    await websocket.accept()
    print("Client connected to Video Stream.")
    
    # Ensure detectors are ready (lazy init)
    if not camera_service.running:
        camera_service.start(video_source=None) # Start without local hardware

    try:
        while True:
            # Receive frame bytes from client
            data = await websocket.receive_bytes()
            
            # Process Frame
            result = camera_service.process_external_frame(data)
            
            # Send Analysis back (JSON)
            await websocket.send_text(json.dumps(result))
            
    except WebSocketDisconnect:
        print("Client disconnected from Video Stream.")
    except Exception as e:
        print(f"Video WebSocket Error: {e}")


