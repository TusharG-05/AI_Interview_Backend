import cv2
import time
import numpy as np
import multiprocessing
import os
import threading
from ..utils.image_processing import convert_to_rgb, resize_with_aspect_ratio
from ..core.logger import get_logger

logger = get_logger(__name__)

# Modal integration flag
USE_MODAL = os.getenv("USE_MODAL", "false").lower() == "true"

# Lazy import Modal DeepFace
_modal_get_embedding = None

def get_modal_embedding():
    """Lazy load Modal DeepFace function to avoid import errors when Modal not installed."""
    global _modal_get_embedding
    if _modal_get_embedding is None:
        try:
            from ..modal_deepface import get_embedding
            _modal_get_embedding = get_embedding
            logger.info("Modal DeepFace function loaded successfully")
        except ImportError as e:
            logger.warning(f"Modal DeepFace not available: {e}")
            return None
    return _modal_get_embedding


class MediaPipeDetector:
    """Handles face detection using MediaPipe."""
    def __init__(self, model_path='app/assets/face_landmarker.task', num_faces=4, min_confidence=0.5):
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=num_faces,
            min_face_detection_confidence=min_confidence
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def detect(self, img_rgb):
        import mediapipe as mp
        h, w = img_rgb.shape[:2]
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        detection_result = self.detector.detect(mp_image)
        
        locs = []
        if detection_result.face_landmarks:
            for landmarks in detection_result.face_landmarks:
                xs = [lm.x for lm in landmarks]
                ys = [lm.y for lm in landmarks]
                
                t, l, b, r = int(min(ys) * h), int(min(xs) * w), int(max(ys) * h), int(max(xs) * w)
                
                # Add padding
                hp, wp = int((b-t)*0.1), int((r-l)*0.1)
                locs.append((max(0, t-hp), min(w, r+wp), min(h, b+hp), max(0, l-wp)))
        return locs


class FaceRecognizer:
    """
    Handles face recognition using DeepFace.
    Currently disabled due to heavy model usage.
    """
    def __init__(self, known_encoding=None):
        self.known_encoding = known_encoding
        self.model_name = "ArcFace"
        try:
            from deepface import DeepFace
            DeepFace.build_model(self.model_name)
        except ImportError:
            logger.warning("DeepFace not installed - face recognition disabled")
        except Exception as e:
            logger.warning(f"DeepFace model build failed: {e} - face recognition may not work")

    def recognize(self, img_rgb, locs):
        """
        Returns list of booleans indicating matches for each face location.
        Uses Cosine Similarity on ArcFace embeddings.
        Routes to Modal GPU if USE_MODAL=true.
        """
        matches = []
        if self.known_encoding is None: return [False] * len(locs)

        for (t, r, b, l) in locs:
            # Padding check
            h, w = img_rgb.shape[:2]
            if t < 0 or l < 0 or b > h or r > w: continue
            
            face = img_rgb[t:b, l:r]
            if face.size == 0: 
                matches.append(False)
                continue
            
            try:
                curr_emb = None
                
                # Try Modal if enabled
                if USE_MODAL:
                    modal_fn = get_modal_embedding()
                    if modal_fn:
                        # Convert face crop to bytes
                        import cv2
                        _, img_encoded = cv2.imencode('.jpg', cv2.cvtColor(face, cv2.COLOR_RGB2BGR))
                        result = modal_fn.remote(img_encoded.tobytes())
                        if result.get("success"):
                            curr_emb = result["embedding"]
                
                # Local fallback if Modal didn't work
                if curr_emb is None:
                    from deepface import DeepFace
                    objs = DeepFace.represent(
                        img_path=face, 
                        model_name=self.model_name, 
                        enforce_detection=False, 
                        detector_backend="skip",
                        align=False
                    )
                    curr_emb = objs[0]["embedding"]
                
                # Cosine Similarity
                a = np.array(self.known_encoding)
                b = np.array(curr_emb)
                cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                
                # ArcFace Threshold: roughly 0.4 - 0.5 for similarity
                matches.append(bool(cos_sim > 0.40))
                
            except Exception as e:
                logger.debug(f"Face recognition error: {e}")
                matches.append(False)
        
        return matches



def face_worker_process(frame_queue, result_queue):
    """Worker process logic: Processes frames for multiple sessions."""
    from ..core.logger import setup_logging
    setup_logging()
    worker_logger = get_logger("face_worker")

    detector = MediaPipeDetector()
    recognizer = FaceRecognizer() # No global encoding
    
    # Cache for embeddings: {session_id: encoding_ndarray}
    embedding_cache = {}

    while True:
        try:
            item = frame_queue.get(timeout=1)
        except multiprocessing.queues.Empty:
            continue

        if item is None:
            break

        session_id, frame_bgr, encoding_json = item

        try:
            # Sync session encoding if provided
            if encoding_json and session_id not in embedding_cache:
                import json
                embedding_cache[session_id] = np.array(json.loads(encoding_json))
            
            recognizer.known_encoding = embedding_cache.get(session_id)
            
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            h, w = frame_rgb.shape[:2]
            target_h = 540
            s = target_h / h if h > target_h else 1.0
            img = cv2.resize(frame_rgb, (0,0), fx=s, fy=s) if s < 1.0 else frame_rgb
            
            locs = detector.detect(img)
            matches = recognizer.recognize(img, locs)
            is_authorized = any(matches) if matches else False
            final_locs = [(int(t/s), int(r/s), int(b/s), int(l/s)) for (t,r,b,l) in locs]

            if not result_queue.full():
                result_queue.put((session_id, is_authorized, 1.0, len(final_locs), final_locs))
        except Exception as e:
            worker_logger.error(f"Face Worker Error [Session {session_id}]: {e}")


class FaceService:
    """The main interface for face-related services (Multi-User Isolated)."""
    def __init__(self):
        logger.info("Starting Multi-User Face Service (Isolated Sessions)...")
        
        self.frame_queue = multiprocessing.Queue(maxsize=10)
        self.result_queue = multiprocessing.Queue(maxsize=10)
        self.worker = multiprocessing.Process(
            target=face_worker_process, 
            args=(self.frame_queue, self.result_queue)
        )
        self.worker.daemon = True
        self.worker.start()
        
        # Results map: {session_id: latest_result}
        self.session_results = {}
        self.session_encodings = {}

    def process_frame(self, frame_bgr, session_id: int):
        # 1. Provide encoding to worker if not already sent
        encoding = self.session_encodings.get(session_id)
        
        if not self.frame_queue.full():
            img_small, _ = resize_with_aspect_ratio(frame_bgr, target_height=360)
            self.frame_queue.put((session_id, img_small, encoding))
        
        # 2. Drain results and update map
        while not self.result_queue.empty():
            try:
                sid, match, conf, n_faces, locs = self.result_queue.get_nowait()
                self.session_results[sid] = (match, conf, n_faces, locs)
            except multiprocessing.queues.Empty:
                break
        
        return self.session_results.get(session_id, (False, 1.0, 0, []))

    def register_session_identity(self, session_id: int, encoding_json: str):
        """Pre-cache the candidate encoding for a session."""
        self.session_encodings[session_id] = encoding_json

    def close(self):
        try:
            self.frame_queue.put(None)
            self.worker.join(timeout=5)
        except Exception as e:
            logger.warning(f"Error closing face worker gracefully: {e}")
            self.worker.terminate()


# Alias for backward compatibility
FaceDetector = FaceService
