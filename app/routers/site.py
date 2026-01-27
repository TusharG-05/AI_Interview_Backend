from fastapi import APIRouter, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from ..services.camera import CameraService
import asyncio

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
camera_service = CameraService()

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_json({"warning": message})
            except:
                pass # Connection likely dead

manager = ConnectionManager()

# Bridge Camera Service -> WebSockets
def camera_status_callback(warning_key):
    # This runs in a thread, so we must schedule the async broadcast carefully
    # ideally we use an event loop, but for simplicity in this synchronous bridge:
    # We will use a fire-and-forget approach or rely on the fact that
    # starlette websockets are async.
    # A robust way is to use `asyncio.run_coroutine_threadsafe` if we have a loop reference.
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast(warning_key), loop)
        else:
            # Fallback if no loop is readily available (rare in FastAPI)
            pass 
    except:
        pass

# Hack: We need to register the listener once. 
# We'll do it when the first client connects or lazily.
_listener_registered = False

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Start camera via lazy load if not already
    camera_service.start()
    return templates.TemplateResponse("index.html", {"request": request})

@router.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    global _listener_registered
    
    await manager.connect(websocket)
    
    # Register the bridge if not already
    if not _listener_registered:
        camera_service.add_listener(camera_status_callback)
        _listener_registered = True
        
    try:
        # Send initial state
        await websocket.send_json({"warning": camera_service.get_current_warning()})
        
        while True:
            # Keep alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/admin-panel", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/webcam-test", response_class=HTMLResponse)
async def webcam_test(request: Request):
    return templates.TemplateResponse("webcam_test.html", {"request": request})

@router.get("/status")
def get_status():
    from ..services.camera import CameraService
    cam = CameraService()
    # Assuming cam.latest_gaze_status exists or we need to expose it
    # We need to quickly patch CameraService to expose this strictly.
    # Actually, let's just implement a quick check.
    # We will need to store this status in CameraService.
    # For now, let's return a placeholder until we update CameraService.
    # But wait, CameraService handles frame processing loop. 
    # Let's peek into CameraService._process_loop logic.
    return {"warning": cam.get_current_warning()}
