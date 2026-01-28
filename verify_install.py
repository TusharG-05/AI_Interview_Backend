
import sys

print(f"Python version: {sys.version}")

try:
    import fastapi
    print("FastAPI imported successfully")
except ImportError as e:
    print(f"FastAPI import failed: {e}")

try:
    import cv2
    print("OpenCV imported successfully")
except ImportError as e:
    print(f"OpenCV import failed: {e}")

try:
    from faster_whisper import WhisperModel
    print("Faster-Whisper imported successfully")
except ImportError as e:
    print(f"Faster-Whisper import failed: {e}")

try:
    import torch
    print(f"Torch imported successfully (Version: {torch.__version__})")
except ImportError as e:
    print(f"Torch import failed: {e}")

print("Verification complete.")
