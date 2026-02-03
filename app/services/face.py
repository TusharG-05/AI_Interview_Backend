import cv2
import time
import numpy as np
import multiprocessing
import os
import threading
from ..utils.image_processing import convert_to_rgb, resize_with_aspect_ratio
from ..core.logger import get_logger

logger = get_logger(__name__)


class MediaPipeDetector:
    """Handles face detection using MediaPipe."""
    def __init__(self, model_path='app/assets/face_landmarker.task', num_faces=4, min_confidence=0.5):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=num_faces,
            min_face_detection_confidence=min_confidence
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def detect(self, img_rgb):
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


# class FaceRecognizer:
#     """
#     Handles face recognition using DeepFace.
#     Currently disabled due to heavy model usage.
#     """
#     def __init__(self, known_encoding=None):
#         self.known_encoding = known_encoding
#         # self.model_name = "ArcFace"
#         # try:
#         #     DeepFace.build_model(self.model_name)
#         # except:
#         #     pass
#
#     def recognize(self, img_rgb, locs):
#         """Returns matches based on known encoding. Currently returns NO matches."""
#         # matches = []
#         # if self.known_encoding is None: return matches
#         # ... logic commented out ...
#         return []


def face_worker_process(frame_queue, result_queue, known_encoding):
    """Worker process logic encapsulated in a function."""
    from ..core.logger import setup_logging
    setup_logging()
    worker_logger = get_logger("face_worker")

    # Initialize MediaPipe
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    
    base_options = python.BaseOptions(model_asset_path='app/assets/face_landmarker.task')
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        num_faces=4,
        min_face_detection_confidence=0.5
    )
    detector = vision.FaceLandmarker.create_from_options(options)

    def recognition_loop():
        # Pre-warm DeepFace model
        try:
            from deepface import DeepFace
            DeepFace.build_model("ArcFace")
        except:
            pass

        while True:
            time.sleep(0.01)
            with state['lock']:
                img_copy = state['img'].copy() if state['img'] is not None else None
                locs_copy = list(state['locs'])
            
            if img_copy is not None and locs_copy:
                try:
                    # Slow recognition happens in background thread
                    # Convert MediaPipe locs (top, right, bottom, left) to DeepFace bboxes if needed
                    # DeepFace represent can take a list of alignments or full image.
                    # For accuracy in 2026, we use ArcFace.
                    matches = []
                    for (t, r, b, l) in locs_copy:
                        # Crop face
                        face_img_rgb = img_copy[max(0, t):b, max(0, l):r]
                        if face_img_rgb.size == 0: continue
                        
                        # DeepFace expectation: BGR for numpy arrays
                        face_img_bgr = cv2.cvtColor(face_img_rgb, cv2.COLOR_RGB2BGR)
                        
                        from deepface import DeepFace
                        objs = DeepFace.represent(
                            img_path=face_img_bgr, 
                            model_name="ArcFace", 
                            enforce_detection=False,
                            detector_backend="skip",
                            align=True # Standard ArcFace alignment
                        )
                        
                        if objs and known_encoding is not None:
                            embedding = np.array(objs[0]["embedding"])
                            # Manual Cosine Distance: 1 - (A.B / (|A||B|))
                            dot = np.dot(embedding, known_encoding)
                            norm_a = np.linalg.norm(embedding)
                            norm_b = np.linalg.norm(known_encoding)
                            dist = 1 - (dot / (norm_a * norm_b))
                            matches.append(dist)

                    if matches:
                        min_dist = min(matches)
                        # ArcFace Cosine threshold is typically around 0.4 for high security
                        match = min_dist <= 0.45 
                        with state['lock']:
                            state['match'] = match
                            state['conf'] = float(min_dist)
                except Exception as e:
                    # print(f"Recognition Thread Error: {e}")
                    pass
            time.sleep(0.3) # Throttle recognition thread for efficiency

    recog_thread = threading.Thread(target=recognition_loop, daemon=True)
    recog_thread.start()

    while True:
        try:
            frame_bgr = frame_queue.get(timeout=1)
        except:
            continue

        if frame_bgr is None:
            break

        try:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
            h, w = frame_rgb.shape[:2]
            target_h = 540
            s = target_h / h if h > target_h else 1.0
            img = cv2.resize(frame_rgb, (0,0), fx=s, fy=s) if s < 1.0 else frame_rgb
            
            locs = detector.detect(img)
            
            # Recognition is skipped
            match_val, conf_val = False, 1.0 
            
            # Map back coordinates
            final_locs = [(int(t/s), int(r/s), int(b/s), int(l/s)) for (t,r,b,l) in locs]

            if not result_queue.full():
                result_queue.put((match_val, conf_val, len(final_locs), final_locs))
        except Exception as e:
            worker_logger.error(f"Face Worker Error: {e}")


class FaceService:
    """The main interface for face-related services."""
    def __init__(self, known_person_path="known_person.jpg"):
        logger.info("Starting Zero-Lag Modernized Face Service (2026)...")
        try:
            # Generate encoding for known person using DeepFace
            logger.info("FaceDetector: Loading DeepFace/ArcFace Model...")
            from deepface import DeepFace
            objs = DeepFace.represent(
                img_path=known_person_path, 
                model_name="ArcFace", 
                enforce_detection=True,
                detector_backend="opencv"
            )
            logger.info("FaceDetector: DeepFace Model Loaded.")
            self.known_encoding = np.array(objs[0]["embedding"]) if objs else None
        except Exception as e:
            logger.error(f"Known Person Load Error: {e}")
            self.known_encoding = None

        self.frame_queue = multiprocessing.Queue(maxsize=1)
        self.result_queue = multiprocessing.Queue(maxsize=1)
        self.worker = multiprocessing.Process(
            target=face_worker_process, 
            args=(self.frame_queue, self.result_queue, self.known_encoding)
        )
        self.worker.daemon = True
        self.worker.start()
        self.last_result = (False, 1.0, 0, [])

    def process_frame(self, frame_bgr):
        img_rgb = convert_to_rgb(frame_bgr)
        img_small, s = resize_with_aspect_ratio(img_rgb, target_height=360)

        if not self.frame_queue.full():
            self.frame_queue.put(img_small)
        
        try:
            match, conf, n_faces, locs = self.result_queue.get_nowait()
            scaled_locs = [(int(t/s), int(r/s), int(b/s), int(l/s)) for (t,r,b,l) in locs]
            self.last_result = (match, conf, n_faces, scaled_locs)
            return self.last_result
        except:
            return self.last_result

    def close(self):
        try:
            self.frame_queue.put(None)
            self.worker.join()
        except:
            self.worker.terminate()


# Alias for backward compatibility
FaceDetector = FaceService
