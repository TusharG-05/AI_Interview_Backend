import cv2
import threading
import time
import os
import numpy as np
from typing import Optional, Tuple
from .face import FaceDetector
from .gaze import GazeDetector
from ..utils.image_processing import decode_image
from ..core.logger import get_logger

logger = get_logger(__name__)

class CameraService:
    """
    Singleton class to manage the camera resource and orchestrate detectors.
    Now supports CLIENT-SIDE streaming via WebSocket.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CameraService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self._initialized = True
        
        self.face_detector: Optional[FaceDetector] = None
        self.gaze_detector: Optional[GazeDetector] = None
        self.running: bool = False
        self._listeners = []
        self._current_warning = "System Initializing..."
        
        # We no longer strictly need these for WebSocket mode, but keeping for compatibility
        self.latest_frame: Optional[bytes] = None
        self.frame_id: int = 0
        self.current_warning_text: str = ""
        self.frame_lock = threading.Lock()
        self._detectors_ready = False

    def start(self, video_source=None):
        """
        Initializes detectors. 
        video_source is ignored in Client-Side mode but kept for signature compatibility.
        """
        if self.running: return
        logger.info("Starting CameraService (Client-Side Streaming Mode)...")
        
        # Init Detectors in background
        def init_detectors():
            logger.info("Background: Initializing Detectors...")
            known_path = "app/assets/known_person.jpg"
            gaze_path = "app/assets/face_landmarker.task"
            
            if os.path.exists(known_path):
                try:
                    self.face_detector = FaceDetector(known_person_path=known_path)
                    logger.info("Background: FaceDetector ready.")
                except Exception as e:
                    logger.error(f"Background: FaceDetector failed: {e}")
            
            if os.path.exists(gaze_path):
                try:
                    self.gaze_detector = GazeDetector(model_path=gaze_path, max_faces=1)
                    logger.info("Background: GazeDetector ready.")
                except Exception as e:
                    logger.error(f"Background: GazeDetector failed: {e}")
            
            self._detectors_ready = True
            logger.info("Background: All Detectors Initialized.")

        threading.Thread(target=init_detectors, daemon=True).start()
        self.running = True

    def stop(self):
        self.running = False
        if self.face_detector:
            self.face_detector.close()
        if self.gaze_detector:
            self.gaze_detector.close()

    def process_external_frame(self, image_bytes):
        """
        Processes a frame received from the client via WebSocket.
        Returns a dict of analysis results.
        """
        if not self._detectors_ready:
             return {"warning": "INITIALIZING AI...", "auth": False, "gaze": "Loading..."}

        # Senior Dev Hardening: Worker Heartbeat Check
        # If a worker process crashed (e.g. OOM or driver error), attempt restart
        if self.face_detector and not self.face_detector.worker.is_alive():
            logger.warning("RECOVERY: FaceDetector worker died. Restarting...")
            self.face_detector = FaceDetector(known_person_path="app/assets/known_person.jpg")
            
        if self.gaze_detector and not self.gaze_detector.worker.is_alive():
            logger.warning("RECOVERY: GazeDetector worker died. Restarting...")
            self.gaze_detector = GazeDetector(model_path="app/assets/face_landmarker.task", max_faces=1)

        try:
            # Decode image using utility
            frame = decode_image(image_bytes)
            
            if frame is None:
                return {"warning": "Bad Frame"}

            # Analyze
            face_status = (False, 1.0, 0, [])
            gaze_status = "No Gaze"
            
            if self.face_detector:
                f_res = self.face_detector.process_frame(frame)
                if f_res: face_status = f_res
            
            if self.gaze_detector:
                g_res = self.gaze_detector.process_frame(frame)
                if g_res: gaze_status = g_res

            # Logic
            found, dist, n_face, locs = face_status
            
            warning = ""
            if n_face > 1: warning = "MULTIPLE FACES DETECTED"
            elif n_face == 0: warning = "NO FACE DETECTED"
            elif n_face == 1 and not found: warning = "SECURITY ALERT: UNAUTHORIZED PERSON"
            elif "WARNING" in str(gaze_status): warning = str(gaze_status)

            # Update state for external status calls
            self._current_warning = warning if warning else "No Issues"
            for callback in self._listeners:
                try: callback(self._current_warning)
                except: pass

            return {
                "auth": bool(found),
                "auth_dist": float(dist) if dist is not None else 1.0,
                "faces": int(n_face),
                "gaze": str(gaze_status),
                "warning": warning,
                "box": locs[0] if locs else None # (top, right, bottom, left)
            }
            
        except Exception as e:
            logger.error(f"Frame Process Error: {e}")
            return {"warning": "Server Error"}

    def update_identity(self, image_bytes: bytes) -> bool:
        """Updates the known person identity and reloads the detector."""
        filepath = "app/assets/known_person.jpg"
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        logger.info("Identity updated. Reloading FaceDetector...")
        
        # Stop old wrapper
        if self.face_detector:
            self.face_detector.close()
        
        # Start new
        try:
            self.face_detector = FaceDetector(known_person_path=filepath)
            return True
        except Exception as e:
            logger.error(f"Failed to reload FaceDetector: {e}")
            return False

    def add_listener(self, callback):
        self._listeners.append(callback)

    def get_current_warning(self):
        return self._current_warning

