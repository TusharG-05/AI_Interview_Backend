import multiprocessing
import time

def gaze_worker(frame_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue, max_faces: int, model_path: str):
    try:
        import os
        import cv2
        import numpy as np
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        abs_model_path = os.path.abspath(model_path)
    
        if not os.path.exists(abs_model_path):
            print(f"GazeWorker ERROR: Model file not found at {abs_model_path}", flush=True)

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
        
        landmarker = vision.FaceLandmarker.create_from_options(options)
        print("GazeWorker: MediaPipe Landmarker created successfully.", flush=True)
        
        suspicious_start_time = None
        SUSPICION_THRESHOLD = 1.5
        H_MIN, H_MAX = 0.45, 0.58
        V_MIN, V_MAX = 0.38, 0.62 
        
        while True:
            try:
                bgr_frame = frame_queue.get(timeout=1)
            except:
                continue
                
            if bgr_frame is None: 
                break
                
            try:
                rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                rgb_frame.flags.writeable = False
                
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                results = landmarker.detect(mp_image)
                
                final_status = "No Face"
                
                if results.face_landmarks:
                    num_faces = len(results.face_landmarks)
                    
                    if num_faces > max_faces:
                        final_status = f"Multiple Faces ({num_faces})"
                    else:
                        face_landmarks = results.face_landmarks[0]
                        h, w, _ = rgb_frame.shape

                        def to_px(landmark):
                            return np.array([int(landmark.x * w), int(landmark.y * h)])

                        mesh = [to_px(l) for l in face_landmarks]
                        
                        if len(mesh) > 473:
                            def get_iris_position(p1, p2, iris):
                                total = np.linalg.norm(p2 - p1)
                                if total <= 1e-6: return 0.5
                                return np.linalg.norm(iris - p1) / total

                            r_left_h = get_iris_position(mesh[33], mesh[133], mesh[468])
                            r_right_h = get_iris_position(mesh[362], mesh[263], mesh[473])
                            avg_h = (r_left_h + r_right_h) / 2
                            
                            r_left_v = get_iris_position(mesh[159], mesh[145], mesh[468])
                            r_right_v = get_iris_position(mesh[386], mesh[374], mesh[473])
                            avg_v = (r_left_v + r_right_v) / 2
                            
                            eye_height = np.linalg.norm(mesh[159] - mesh[145])
                            is_blinking = eye_height < (h * 0.012)

                            raw_state = "Center"
                            if avg_h < H_MIN: raw_state = "Right"
                            elif avg_h > H_MAX: raw_state = "Left"
                            elif avg_v < V_MIN: raw_state = "Up"
                            elif avg_v > V_MAX: raw_state = "Down"
                            elif is_blinking:   raw_state = "Blink"
                            
                            if raw_state in ["Down", "Blink"]:
                                if suspicious_start_time is None:
                                    suspicious_start_time = time.time()
                                elapsed = time.time() - suspicious_start_time
                                if elapsed > SUSPICION_THRESHOLD:
                                    final_status = "WARNING: Looking Down/Sleeping"
                                else:
                                    final_status = "Safe: Center (Blinking/Glance)"
                            elif raw_state in ["Left", "Right", "Up"]:
                                final_status = f"WARNING: Looking {raw_state}"
                                suspicious_start_time = None
                            else:
                                final_status = "Safe: Center"
                                suspicious_start_time = None
                                
                if result_queue.full():
                    try: result_queue.get_nowait()
                    except: pass
                result_queue.put(final_status)

            except Exception as e:
                print(f"GazeWorker Logic Error: {e}", flush=True)

    except Exception as e:
        print(f"GazeWorker CRITICAL FAILURE: {e}", flush=True)
    
    if landmarker:
        landmarker.close()

class GazeDetector:
    def __init__(self, model_path='assets/face_landmarker.task', max_faces=1):
        print("Initializing GazeDetector...")
        self.model_path = model_path
        self.frame_queue = multiprocessing.Queue(maxsize=1)
        self.result_queue = multiprocessing.Queue(maxsize=1)
        
        self.worker = multiprocessing.Process(
            target=gaze_worker,
            args=(self.frame_queue, self.result_queue, max_faces, self.model_path)
        )
        self.worker.daemon = True
        self.worker.start()
        
    def process_frame(self, frame_bgr):
        try:
            if not self.frame_queue.full():
                self.frame_queue.put(frame_bgr)
            try:
                return self.result_queue.get_nowait()
            except:
                return None
        except:
            return None
            
    def close(self):
        try:
            self.frame_queue.put(None)
            self.worker.join()
        except:
            self.worker.terminate()
