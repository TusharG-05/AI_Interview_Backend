from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
