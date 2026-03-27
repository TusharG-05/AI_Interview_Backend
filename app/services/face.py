import time
import multiprocessing
import os
import threading
from typing import Any, List, Optional
from ..core.config import IS_ORCHESTRATOR
from ..utils.image_processing import convert_to_rgb, resize_with_aspect_ratio
from ..core.logger import get_logger

logger = get_logger(__name__)


# Modal integration flag
USE_MODAL = os.getenv("USE_MODAL", "false").lower() == "true"

# Lazy import Modal DeepFace
_modal_get_embedding = None

def get_modal_embedding():
    """Lazy load Modal DeepFace class to avoid import errors."""
    global _modal_get_embedding
    if _modal_get_embedding is None:
        try:
            import modal
            # Use from_name for lazy reference to deployed class
            # Note: Deployment name is 'interview-deepface', Class name is 'DeepFaceEmbedder'
            _modal_get_embedding = modal.Cls.from_name("interview-deepface", "DeepFaceEmbedder")
            logger.info("Modal DeepFace class reference obtained")
        except Exception as e:
            logger.warning(f"Modal DeepFace not available: {e}")
            return None
    return _modal_get_embedding


class MediaPipeDetector:
    """Handles face detection using MediaPipe."""
    def __init__(self, model_path='app/assets/face_landmarker.task', num_faces=4, min_confidence=0.5):
        # --- Skip initialization in Orchestrator Mode or HF Space (Lazy) ---
        is_hf = os.getenv("SPACE_ID") is not None
        if IS_ORCHESTRATOR or is_hf:
            logger.info(f"MediaPipeDetector: Skipping eager initialization (Mode: {'Orchestrator' if IS_ORCHESTRATOR else 'HF'})")

            self.detector = None
            return

        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        # specific fix for model path
        if not os.path.exists(model_path):
            # Try absolute path relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # app/services/face.py -> app/assets/face_landmarker.task
            potential_path = os.path.join(base_dir, "..", "assets", "face_landmarker.task")
            if os.path.exists(potential_path):
                model_path = os.path.abspath(potential_path)
            else:
                 # Fallback to project root connection
                 potential_path = os.path.abspath(os.path.join(os.getcwd(), "app", "assets", "face_landmarker.task"))
                 if os.path.exists(potential_path):
                     model_path = potential_path

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=num_faces,
            min_face_detection_confidence=min_confidence
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def detect(self, img_rgb):
        if self.detector is None:
            return []
            
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
    """
    def __init__(self, known_encoding=None):
        self.known_encoding = known_encoding
        # Default local/fallback model is SFace (lightweight: 35MB)
        self.model_name = "SFace"
        
        # --- Skip initialization in Orchestrator Mode ---
        if IS_ORCHESTRATOR:
            logger.info("FaceRecognizer: Skipping local model initialization (Orchestrator Mode)")
            return


        # SFace is light enough to build even on HF Spaces (Free Tier)
        # We only skip if DeepFace is missing
        try:
            # Explicitly handle TensorFlow/Keras environment for SFace
            # tf-keras 2.13.0 is recommended for tensorflow 2.13.0
            try:
                import tf_keras
                import os
                os.environ["TF_USE_LEGACY_KERAS"] = "1"
                logger.info("Initializing tf-keras compatibility layer.")
            except ImportError:
                logger.debug("tf-keras not found, proceeding with default backend.")
                
            from deepface import DeepFace
            # Ensure CPU-only optimization for HF Spaces
            if os.getenv("SPACE_ID"):
                import tensorflow as tf
                tf.config.set_visible_devices([], 'GPU')
                logger.info("HF Space detected: TensorFlow GPU disabled for CPU-only efficiency.")

            logger.info(f"Building local Face Model: {self.model_name} (SFace)...")
            DeepFace.build_model(self.model_name)
            logger.info(f"Local {self.model_name} model ready.")
        except ImportError:
            logger.error("CRITICAL: DeepFace not installed. Local face recognition is DISABLED.")
        except Exception as e:
            logger.warning(f"Local {self.model_name} model build failed (will try lazy load on first attempt): {e}")

    def recognize(self, img_rgb, locs):
        """
        Returns list of booleans indicating matches for each face location.
        Uses Modal (ArcFace) for high accuracy, or Local (SFace) for fallback.
        """
        matches = []
        if self.known_encoding is None: 
            return [False] * len(locs)

        # known_encoding can be a JSON string of a map or a single list (legacy)
        embedding_map = {}
        if isinstance(self.known_encoding, str):
            import json
            try:
                data = json.loads(self.known_encoding)
                if isinstance(data, dict):
                    embedding_map = data
                else:
                    # Legacy: single ArcFace vector
                    embedding_map = {"ArcFace": data}
            except:
                return [False] * len(locs)
        elif isinstance(self.known_encoding, dict):
            embedding_map = self.known_encoding
        else:
            # Fallback for unexpected formats
            return [False] * len(locs)

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
                
                # 1. Try Modal (High Accuracy: ArcFace) if enabled
                if USE_MODAL:
                    modal_cls = get_modal_embedding()
                    if modal_cls:
                        try:
                            # Convert face crop to bytes
                            import cv2
                            _, img_encoded = cv2.imencode('.jpg', cv2.cvtColor(face, cv2.COLOR_RGB2BGR))
                            # Modal app is configured for ArcFace (default)
                            result = modal_cls().get_embedding.remote(img_encoded.tobytes())
                            if result.get("success"):
                                curr_emb = result["embedding"]
                        except Exception as e:
                            logger.warning(f"Modal DeepFace call failed: {e}")
                
                # 2. Local fallback (Lightweight: SFace) if Modal fails or is disabled
                if curr_emb is None:
                    try:
                        # On 512MB tiers, this might still cause a spike, but user confirmed SFace is light enough for HF.
                        from deepface import DeepFace
                        objs = DeepFace.represent(
                            img_path=face, 
                            model_name=self.model_name, # Uses SFace
                            enforce_detection=False, 
                            detector_backend="skip",
                            align=False
                        )
                        curr_emb = objs[0]["embedding"]
                        logger.info(f"Local {self.model_name} fallback successful.")
                    except Exception as e:
                        logger.warning(f"Local {self.model_name} fallback failed: {e}")


                
                if curr_emb is None:
                    matches.append(False)
                    continue

                # Cosine Similarity check against the correct model's known encoding
                target_model = "ArcFace" if USE_MODAL and modal_cls and curr_emb is not None else self.model_name
                known_vec = embedding_map.get(target_model)

                if known_vec is None:
                    logger.warning(f"No known encoding found for model: {target_model}")
                    matches.append(False)
                    continue

                import numpy as np
                a = np.array(known_vec)
                b = np.array(curr_emb)
                
                if a.shape != b.shape:
                    logger.error(f"Dimension mismatch: {target_model} known({a.shape}) vs current({b.shape})")
                    matches.append(False)
                    continue

                cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                
                # Threshold: 0.40 is generally safe for both ArcFace and SFace
                # but SFace is more compact, sometimes more strict.
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
    
    # Cache for embeddings: {interview_id: encoding_ndarray}
    embedding_cache = {}

    while True:
        try:
            item = frame_queue.get(timeout=1)
        except multiprocessing.queues.Empty:
            continue

        if item is None:
            break

        interview_id, frame_bgr, encoding_json = item

        try:
            # Sync session encoding if provided
            if encoding_json and interview_id not in embedding_cache:
                import json
                try:
                    data = json.loads(encoding_json)
                    # We store it as is (dict or list) and let recognizer handle it
                    embedding_cache[interview_id] = data
                except Exception as e:
                    worker_logger.error(f"Failed to parse encoding for Session {interview_id}: {e}")
            
            recognizer.known_encoding = embedding_cache.get(interview_id)
            
            import cv2
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
                result_queue.put((interview_id, is_authorized, 1.0, len(final_locs), final_locs))
        except Exception as e:
            worker_logger.error(f"Face Worker Error [Session {interview_id}]: {e}")


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
        
        # Results map: {interview_id: latest_result}
        self.session_results = {}
        self.session_encodings = {}

    def process_frame(self, frame_bgr, interview_id: int):
        # 1. Provide encoding to worker if not already sent
        encoding = self.session_encodings.get(interview_id)
        
        if not self.frame_queue.full():
            img_small, _ = resize_with_aspect_ratio(frame_bgr, target_height=360)
            self.frame_queue.put((interview_id, img_small, encoding))
        
        # 2. Drain results and update map
        while not self.result_queue.empty():
            try:
                sid, match, conf, n_faces, locs = self.result_queue.get_nowait()
                self.session_results[sid] = (match, conf, n_faces, locs)
            except multiprocessing.queues.Empty:
                break
        
        return self.session_results.get(interview_id, (False, 1.0, 0, []))

    def register_session_identity(self, interview_id: int, encoding_json: str):
        """Pre-cache the candidate encoding for a session."""
        self.session_encodings[interview_id] = encoding_json

    def close(self):
        try:
            self.frame_queue.put(None)
            self.worker.join(timeout=5)
        except Exception as e:
            logger.warning(f"Error closing face worker gracefully: {e}")
            self.worker.terminate()


# Alias for backward compatibility
FaceDetector = FaceService
