import cv2
import numpy as np

def decode_image(image_bytes: bytes) -> np.ndarray:
    """Decodes raw image bytes into an OpenCV-compatible BGR image."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def resize_with_aspect_ratio(image: np.ndarray, target_height: int = 480) -> tuple[np.ndarray, float]:
    """Resizes an image to a target height while maintaining aspect ratio."""
    h, w = image.shape[:2]
    if h <= target_height:
        return image, 1.0
        
    s = target_height / h
    new_w = int(w * s)
    resized = cv2.resize(image, (new_w, target_height), interpolation=cv2.INTER_AREA)
    return resized, s

def convert_to_rgb(image: np.ndarray) -> np.ndarray:
    """Converts a BGR image to RGB."""
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
