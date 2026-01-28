import cv2
import time
import numpy as np
import multiprocessing
import os
import threading

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

def face_recognition_worker(frame_queue, result_queue, known_encoding):
    print("FaceWorker: Started (MediaPipe Mode)", flush=True)

    # Initialize MediaPipe Detector
    model_path = 'assets/face_landmarker.task'
    if not os.path.exists(model_path):
        print(f"FaceWorker ERROR: Model missing at {model_path}")
        return

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        num_faces=1,
        min_face_detection_confidence=0.5
    )
    detector = vision.FaceLandmarker.create_from_options(options)

    while True:
        try:
            frame_bgr = frame_queue.get(timeout=1)
        except:
            continue

        if frame_bgr is None:
            break

        try:
            # Convert to RGB
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
            # Smart Resize
            h, w = frame_rgb.shape[:2]
            target_h = 540
            s = target_h / h if h > target_h else 1.0
            img = cv2.resize(frame_rgb, (0,0), fx=s, fy=s) if s < 1.0 else frame_rgb
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)
            detection = detector.detect(mp_image)
            
            new_locs = []
            
            if detection.face_landmarks:
                match_val = True 
                conf_val = 0.99
                
                ih, iw = img.shape[:2]
                for landmarks in detection.face_landmarks:
                    xs = [lm.x for lm in landmarks]
                    ys = [lm.y for lm in landmarks]
                    t, l, b, r = int(min(ys) * ih), int(min(xs) * iw), int(max(ys) * ih), int(max(xs) * iw)
                    
                    # Pad
                    hp, wp = int((b-t)*0.1), int((r-l)*0.1)
                    new_locs.append((max(0, t-hp), min(iw, r+wp), min(ih, b+hp), max(0, l-wp)))
            else:
                match_val = False
                conf_val = 0.0

            # Scale back
            final_locs = [(int(t/s), int(r/s), int(b/s), int(l/s)) for (t,r,b,l) in new_locs]

            if not result_queue.full():
                result_queue.put((match_val, conf_val, len(final_locs), final_locs))

        except Exception as e:
            print(f"FaceWorker Runtime Error: {e}")

    detector.close()
    print("FaceWorker: Stopped")


class FaceDetector:
    def __init__(self, known_person_path="assets/known_person.jpg"):
        print("Starting FaceDetector...")
        self.known_encoding = None 
        
        self.frame_queue = multiprocessing.Queue(maxsize=1)
        self.result_queue = multiprocessing.Queue(maxsize=1)
        
        self.worker = multiprocessing.Process(
            target=face_recognition_worker, 
            args=(self.frame_queue, self.result_queue, self.known_encoding)
        )
        self.worker.daemon = True
        self.worker.start()

    def process_frame(self, frame_bgr):
        h, w = frame_bgr.shape[:2]
        s = 360.0 / h if h > 360 else 1.0
        
        img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img_small = cv2.resize(img_rgb, (0,0), fx=s, fy=s) if s < 1.0 else img_rgb

        if not self.frame_queue.full():
            self.frame_queue.put(img_small)
        
        try:
            match, conf, n_faces, locs = self.result_queue.get_nowait()
            scaled_locs = [(int(t/s), int(r/s), int(b/s), int(l/s)) for (t,r,b,l) in locs]
            return match, conf, n_faces, scaled_locs
        except:
            return None, None, 0, []

    def close(self):
        try:
            self.frame_queue.put(None)
            self.worker.join()
        except:
            self.worker.terminate()
