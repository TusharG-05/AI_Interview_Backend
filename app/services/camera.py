import cv2
import threading
import time
import os
import numpy as np
from typing import Optional, Tuple
# from .face import FaceDetector
# from .gaze import GazeDetector
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
        
        # Session Isolation: {session_id: value}
        self.session_frames: dict[int, bytes] = {}
        self.session_frame_ids: dict[int, int] = {}
        self.session_warnings: dict[int, str] = {}
        
        self.frame_lock = threading.Lock()
        self._detectors_ready = False
        self._monitor_thread = None

    def start(self, video_source=None):
        """
        Initializes detectors. 
        video_source is ignored in Client-Side mode but kept for signature compatibility.
        """
        if self.running: return
        logger.info("Starting CameraService (Client-Side Streaming Mode)...")
        
        # Init Detectors in background (Stateless initialization)
        def init_detectors():
            logger.info("Background: Initializing Detectors...")
            gaze_path = "app/assets/face_landmarker.task"
            
            try:
                from .face import FaceDetector
                # FaceDetector no longer needs known_path in constructor (Multi-User Refactor)
                self.face_detector = FaceDetector()
                logger.info("Background: FaceDetector ready.")
            except Exception as e:
                logger.error(f"Background: FaceDetector failed: {e}")
            
            if os.path.exists(gaze_path):
                try:
                    from .gaze import GazeDetector
                    self.gaze_detector = GazeDetector(model_path=gaze_path, max_faces=1)
                    logger.info("Background: GazeDetector ready.")
                except Exception as e:
                    logger.error(f"Background: GazeDetector failed: {e}")
            
            self._detectors_ready = True
            logger.info("Background: All Detectors Initialized.")

        threading.Thread(target=init_detectors, daemon=True).start()
        self.running = True
        self.start_monitor()

    def stop(self):
        self.running = False
        if self.face_detector:
            self.face_detector.close()
        if self.gaze_detector:
            self.gaze_detector.close()

    def process_frame_ndarray(self, frame: np.ndarray, session_id: int):
        """
        Core logic: Processes a numpy BGR frame (from WS or WebRTC).
        Returns: (annotated_frame, result_dict)
        """
        try:
            # Analyze
            face_status = (False, 1.0, 0, [])
            gaze_status = "No Gaze"
            
            if self.face_detector:
                f_res = self.face_detector.process_frame(frame, session_id)
                if f_res: face_status = f_res
            
            if self.gaze_detector:
                g_res = self.gaze_detector.process_frame(frame)
                if g_res: gaze_status = g_res

            found, dist, n_face, locs = face_status
            
            # --- ANNOTATE ---
            if locs:
                for (top, right, bottom, left) in locs:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            warning = ""
            if n_face > 1: warning = "MULTIPLE FACES DETECTED"
            elif n_face == 0: warning = "NO FACE DETECTED"
            elif n_face == 1 and not found: warning = "SECURITY ALERT: UNAUTHORIZED PERSON"
            elif "WARNING" in str(gaze_status): warning = str(gaze_status)

            # Update latest frame for MJPEG stream (Isolate by session)
            with self.frame_lock:
                _, buffer = cv2.imencode('.jpg', frame)
                self.session_frames[session_id] = buffer.tobytes()
                self.session_frame_ids[session_id] = self.session_frame_ids.get(session_id, 0) + 1

            # --- PERSIST PROCTORING EVENT ---
            if warning:
                from ..core.database import engine
                from sqlmodel import Session
                from ..models.db_models import ProctoringEvent
                
                with Session(engine) as db_session:
                    event = ProctoringEvent(
                        session_id=session_id,
                        event_type=warning,
                        details=f"Faces: {n_face}, Auth: {found}, Gaze: {gaze_status}"
                    )
                    db_session.add(event)
                    db_session.commit()

            # Update state for external status calls (Isolate by session)
            self.session_warnings[session_id] = warning if warning else "No Issues"
            for callback in self._listeners:
                try: callback(session_id, self.session_warnings[session_id])
                except: pass

            result_dict = {
                "auth": bool(found),
                "auth_dist": float(dist) if dist is not None else 1.0,
                "faces": int(n_face),
                "gaze": str(gaze_status),
                "warning": warning,
                "box": locs[0] if locs else None
            }
            return frame, result_dict

        except Exception as e:
            logger.error(f"Core Frame Process Error: {e}")
            return frame, {"warning": "Server Error"}

    def start_monitor(self):
        """Starts background monitoring for detector health."""
        if self._monitor_thread and self._monitor_thread.is_alive(): return
        
        def monitor_loop():
            logger.info("Detector Monitor Started.")
            while self.running:
                time.sleep(5)
                # Face Detector Check
                if self.face_detector and not self.face_detector.worker.is_alive():
                    logger.warning("MONITOR: FaceDetector worker died. Restarting...")
                    try:
                        from .face import FaceDetector
                        self.face_detector = FaceDetector()
                    except Exception as e:
                        logger.error(f"MONITOR: Failed to restart FaceDetector: {e}")
                
                # Gaze Detector Check
                if self.gaze_detector and not self.gaze_detector.worker.is_alive():
                    logger.warning("MONITOR: GazeDetector worker died. Restarting...")
                    try:
                        from .gaze import GazeDetector
                        self.gaze_detector = GazeDetector(model_path="app/assets/face_landmarker.task", max_faces=1)
                    except Exception as e:
                        logger.error(f"MONITOR: Failed to restart GazeDetector: {e}")

        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()

    def process_external_frame(self, image_bytes, session_id: Optional[int] = None):
        """
        Processes a frame received from the client via WebSocket.
        Returns a dict of analysis results.
        """
        if not self._detectors_ready:
             return {"warning": "INITIALIZING AI...", "auth": False, "gaze": "Loading..."}

        try:
            # Decode image using utility
            frame = decode_image(image_bytes)
            
            if frame is None:
                return {"warning": "Bad Frame"}

            # Delegate to core logic
            _, result = self.process_frame_ndarray(frame, session_id)
            return result
            
        except Exception as e:
            logger.error(f"Frame Process Error: {e}")
            return {"warning": "Server Error"}

    def get_frame(self, session_id: int) -> Tuple[Optional[bytes], int]:
        """Returns the latest annotated frame and its unique ID for a specific session."""
        with self.frame_lock:
            return self.session_frames.get(session_id), self.session_frame_ids.get(session_id, 0)



    def add_listener(self, callback):
        self._listeners.append(callback)

    def get_current_warning(self, session_id: int):
        return self.session_warnings.get(session_id, "System Active")

