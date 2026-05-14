import multiprocessing
import time
import logging

logger = logging.getLogger(__name__)

def gaze_worker(frame_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue, max_faces: int, model_path: str):
    """
    Processes video frames using MediaPipe FaceLandmarker.
    Calculates eye ratios to determine gaze direction and blink state.
    """
    import logging
    worker_logger = logging.getLogger("gaze_worker")
    worker_logger.info("GazeWorker: Process Started")
    
    landmarker = None
    try:
        import os
        import cv2
        import numpy as np
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        from ..utils.image_processing import convert_to_rgb
        
        abs_model_path = os.path.abspath(model_path)
        
        # Resolve model path relative to app/assets
        if not os.path.exists(abs_model_path):
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            potential_paths = [
                os.path.join(curr_dir, "..", "assets", "face_landmarker.task"),
                os.path.join(os.getcwd(), "app", "assets", "face_landmarker.task"),
                "/app/app/assets/face_landmarker.task", # Docker/HF common path
                "/app/assets/face_landmarker.task" # Alternative HF path
            ]
            for p in potential_paths:
                if os.path.exists(p):
                    abs_model_path = os.path.abspath(p)
                    worker_logger.info(f"GazeWorker: Found model at: {p}")
                    break

        if os.getenv("SPACE_ID"):
            worker_logger.info("Cloud Environment (HF Spaces) detected. Using CPU-optimized MediaPipe settings.")
    
        worker_logger.info(f"GazeWorker: Initializing MediaPipe FaceLandmarker with model: {abs_model_path}")
    
        if not os.path.exists(abs_model_path):
            worker_logger.error(f"GazeWorker: CRITICAL ERROR - Model file missing at {abs_model_path}. Proctoring will fail.")
            return

        base_options = python.BaseOptions(model_asset_path=abs_model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=max_faces,
            min_face_detection_confidence=0.25,
            min_face_presence_confidence=0.25,
            min_tracking_confidence=0.25
        )
        
        try:
            landmarker = vision.FaceLandmarker.create_from_options(options)
            worker_logger.info("GazeWorker: MediaPipe landmarker initialized successfully.")
        except Exception as mp_e:
            worker_logger.error(f"GazeWorker: MediaPipe creation failed: {mp_e}")
            return
        
        # State tracking for grace period
        suspicious_start_time = None
        SUSPICION_THRESHOLD = 3.0  # Seconds before flagging any suspicious gaze
        
        # Thresholds (Tuned based on user feedback)
        H_MIN, H_MAX = 0.44, 0.56
        V_MIN, V_MAX = 0.48, 0.62 
        
        while True:
            try:
                bgr_frame = frame_queue.get(timeout=1)
            except multiprocessing.queues.Empty:
                continue
                
            if bgr_frame is None: 
                break
                
            try:
                # Convert to RGB inside the worker using utility
                rgb_frame = convert_to_rgb(bgr_frame)
                rgb_frame.flags.writeable = False # Efficiency
                
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                results = landmarker.detect(mp_image)
                
                final_status = "No Face" # Default
                
                if results.face_landmarks:
                    num_faces = len(results.face_landmarks)
                    
                    if num_faces > max_faces:
                        final_status = f"Multiple Faces ({num_faces})"
                    else:
                        face_landmarks = results.face_landmarks[0]
                        h, w, _ = rgb_frame.shape

                        # Helper to map normalized points to pixels
                        def to_px(landmark):
                            return np.array([int(landmark.x * w), int(landmark.y * h)])

                        # Extract key points for eye analysis
                        mesh = [to_px(l) for l in face_landmarks]
                        
                        if len(mesh) > 473:
                            # Helper for Iris Ratio (0.0=Left, 0.5=Center, 1.0=Right)
                            def get_iris_position(p1, p2, iris):
                                total = np.linalg.norm(p2 - p1)
                                if total <= 1e-6: return 0.5
                                return np.linalg.norm(iris - p1) / total

                            # -- Horizontal --
                            r_left_h = get_iris_position(mesh[33], mesh[133], mesh[468])
                            r_right_h = get_iris_position(mesh[362], mesh[263], mesh[473])
                            avg_h = (r_left_h + r_right_h) / 2
                            
                            # -- Vertical --
                            r_left_v = get_iris_position(mesh[159], mesh[145], mesh[468])
                            r_right_v = get_iris_position(mesh[386], mesh[374], mesh[473])
                            avg_v = (r_left_v + r_right_v) / 2
                            
                            # -- Distance-Adaptive Blink Detection --
                            face_height = np.linalg.norm(mesh[10] - mesh[152])
                            eye_height = np.linalg.norm(mesh[159] - mesh[145])
                            is_blinking = eye_height < (face_height * 0.05)

                            # --- DECISION LOGIC ---
                            raw_state = "Center"
                            
                            if avg_h < H_MIN: raw_state = "Right"
                            elif avg_h > H_MAX: raw_state = "Left"
                            elif avg_v < V_MIN: raw_state = "Up"
                            elif avg_v > V_MAX: raw_state = "Down"
                            elif is_blinking:   raw_state = "Blink"
                            
                            # Process Unified Grace Period (5 Seconds)
                            # Any state other than "Center" increments the timer
                            if raw_state != "Center":
                                if suspicious_start_time is None:
                                    suspicious_start_time = time.time()
                                
                                elapsed = time.time() - suspicious_start_time
                                
                                if elapsed > SUSPICION_THRESHOLD:
                                    # Formulate descriptive warning
                                    msg = f"Looking {raw_state}" if raw_state != "Blink" else "Sleeping/Eyes Closed"
                                    final_status = f"WARNING: {msg}"
                                else:
                                    final_status = f"Safe: Center (Brief {raw_state})"
                                    
                            else:
                                final_status = "Safe: Center"
                                suspicious_start_time = None
                                
                if result_queue.full():
                    try: result_queue.get_nowait()
                    except multiprocessing.queues.Empty: pass
                result_queue.put(final_status)

            except Exception as e:
                worker_logger.error(f"GazeWorker Logic Error: {e}")

    except Exception as e:
        worker_logger.critical(f"GazeWorker CRITICAL FAILURE: {e}")
        import traceback
        worker_logger.error(traceback.format_exc())

    if landmarker:
        landmarker.close()

# =============================================================================
# BACKEND API: GazeDetector Class
# =============================================================================
from ..core.config import IS_ORCHESTRATOR

class GazeDetector:
    def __init__(self, model_path='app/assets/face_landmarker.task', max_faces=1):
        logger.info("Initializing GazeDetector...")
        self.model_path = model_path
        
        # --- Run inline in Orchestrator Mode (no subprocess, memory-safe) ---
        if IS_ORCHESTRATOR:
            logger.info("GazeDetector: Orchestrator Mode - using inline (in-thread) gaze analysis (no subprocess).")
            self.worker = None
            self.frame_queue = None
            self.result_queue = None
            self._inline_landmarker = None  # Lazily initialized on first frame
            self._suspicious_start_time = None
            self._process_counter = 0
            self._last_gaze_result = None
            return

        self.frame_queue = multiprocessing.Queue(maxsize=1)
        self.result_queue = multiprocessing.Queue(maxsize=1)
        
        logger.info(f"GazeDetector initialized with model: {model_path}")
        self.worker = multiprocessing.Process(
            target=gaze_worker,
            args=(self.frame_queue, self.result_queue, max_faces, self.model_path)
        )
        self.worker.daemon = True
        self.worker.start()
        logger.info("Gaze Worker started.")
        
    def _init_inline_landmarker(self):
        """Lazily initialize MediaPipe FaceLandmarker for inline gaze processing."""
        import os
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        model_path = self.model_path
        if not os.path.exists(model_path):
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            for candidate in [
                os.path.join(curr_dir, "..", "assets", "face_landmarker.task"),
                os.path.join(os.getcwd(), "app", "assets", "face_landmarker.task"),
                "/app/app/assets/face_landmarker.task",
            ]:
                if os.path.exists(candidate):
                    model_path = os.path.abspath(candidate)
                    break

        if not os.path.exists(model_path):
            logger.error(f"GazeDetector: Inline mode — model file not found at '{model_path}'.")
            return

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1,
            min_face_detection_confidence=0.25,
            min_face_presence_confidence=0.25,
            min_tracking_confidence=0.25,
        )
        self._inline_landmarker = vision.FaceLandmarker.create_from_options(options)
        logger.info("GazeDetector: Inline FaceLandmarker initialized.")

    def _process_gaze_inline(self, frame_bgr):
        """Run gaze analysis inline (no subprocess). Returns a gaze status string."""
        import cv2
        import numpy as np
        import mediapipe as mp

        H_MIN, H_MAX = 0.44, 0.56
        V_MIN, V_MAX = 0.48, 0.62
        SUSPICION_THRESHOLD = 3.0

        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self._inline_landmarker.detect(mp_image)

        if not results.face_landmarks:
            return "No Face"

        face_landmarks = results.face_landmarks[0]
        h, w, _ = rgb_frame.shape
        mesh = [np.array([int(lm.x * w), int(lm.y * h)]) for lm in face_landmarks]

        if len(mesh) <= 473:
            return "Safe: Center"

        def iris_ratio(p1, p2, iris):
            total = np.linalg.norm(p2 - p1)
            return 0.5 if total <= 1e-6 else np.linalg.norm(iris - p1) / total

        avg_h = (iris_ratio(mesh[33], mesh[133], mesh[468]) + iris_ratio(mesh[362], mesh[263], mesh[473])) / 2
        avg_v = (iris_ratio(mesh[159], mesh[145], mesh[468]) + iris_ratio(mesh[386], mesh[374], mesh[473])) / 2
        face_h = np.linalg.norm(mesh[10] - mesh[152])
        eye_h  = np.linalg.norm(mesh[159] - mesh[145])
        is_blinking = eye_h < (face_h * 0.05)

        if   avg_h < H_MIN:    raw = "Right"
        elif avg_h > H_MAX:    raw = "Left"
        elif avg_v < V_MIN:    raw = "Up"
        elif avg_v > V_MAX:    raw = "Down"
        elif is_blinking:      raw = "Blink"
        else:                  raw = "Center"

        if raw != "Center":
            if self._suspicious_start_time is None:
                self._suspicious_start_time = __import__("time").time()
            elapsed = __import__("time").time() - self._suspicious_start_time
            if elapsed > SUSPICION_THRESHOLD:
                return f"WARNING: {'Sleeping/Eyes Closed' if raw == 'Blink' else f'Looking {raw}'}"
            return f"Safe: Center (Brief {raw})"
        else:
            self._suspicious_start_time = None
            return "Safe: Center"

    def process_frame(self, frame_bgr):
        if IS_ORCHESTRATOR:
            if not hasattr(self, "_process_counter"):
                self._process_counter = 0
            self._process_counter += 1

            # Throttle to every 5th frame to save CPU
            if self._process_counter % 5 != 0:
                return self._last_gaze_result

            # Lazily initialize the landmarker on first real processing call
            if self._inline_landmarker is None:
                try:
                    self._init_inline_landmarker()
                except Exception as e:
                    logger.error(f"GazeDetector: Inline init failed: {e}")
                    return None

            if self._inline_landmarker is None:
                return None

            try:
                result = self._process_gaze_inline(frame_bgr)
                self._last_gaze_result = result
                return result
            except Exception as e:
                logger.error(f"GazeDetector: Inline processing error: {e}")
                return self._last_gaze_result

        try:
            # Send BGR directly; worker will convert to RGB
            if not self.frame_queue.full():
                self.frame_queue.put(frame_bgr)
                
            try:
                return self.result_queue.get_nowait()
            except multiprocessing.queues.Empty:
                return None
        except Exception as e:
            logger.error(f"Gaze API Error: {e}")
            return None
            
    def close(self):
        try:
            self.frame_queue.put(None)
            self.worker.join(timeout=5)
        except Exception as e:
            logger.warning(f"Error closing gaze worker gracefully: {e}")
            self.worker.terminate()
