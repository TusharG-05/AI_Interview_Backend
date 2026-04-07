"""
Modal.com app for GPU-accelerated DeepFace face recognition.

Deploy: modal deploy app/modal_deepface.py
Test:   modal run app/modal_deepface.py --image-path /path/to/face.jpg
"""
import modal
import io

app = modal.App("interview-deepface")

# Container image with DeepFace and OpenCV
# Using a base image with CUDA libraries for better GPU support
deepface_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0")
    .pip_install(
        "deepface==0.0.93",
        "opencv-python-headless",
        "numpy<2.0.0", # Faster-whisper/deepface compatibility
        "tf-keras",
        "Pillow",
        "tensorflow[and-cuda]" # Ensure CUDA libs are available
    )
)


@app.cls(
    image=deepface_image,
    gpu="T4",  # T4 is sufficient for ArcFace
    timeout=120, # Increased for model building
    memory=4096,
    scaledown_window=300,  # Keep warm for 5 mins
)
class DeepFaceEmbedder:
    @modal.enter()
    def load_model(self):
        """Build DeepFace model once when container starts."""
        import time
        from deepface import DeepFace
        print("🚀 Building DeepFace (ArcFace) model...")
        start_time = time.time()
        # Pre-build model to avoid lazy loading on first request
        DeepFace.build_model("ArcFace")
        print(f"✨ DeepFace Model Built in {time.time() - start_time:.2f}s")

    @modal.method()
    def get_embedding(self, image_bytes: bytes) -> dict:
        """
        Extract ArcFace embedding from a face image.
        
        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)
        
        Returns:
            dict with 'embedding' (list of floats) and 'success' (bool)
        """
        import tempfile
        import os
        import io
        from deepface import DeepFace
        from PIL import Image
        
        temp_path = None
        try:
            # First try to validate and convert image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as temporary file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                img.save(f.name, 'JPEG')
                temp_path = f.name
            
            # Extract embedding using ArcFace
            result = DeepFace.represent(
                img_path=temp_path,
                model_name="ArcFace",
                enforce_detection=False,  # Don't enforce detection to handle pre-cropped faces
                detector_backend="skip",  # Skip detection if face is already cropped
                align=False  # Skip alignment for faster processing
            )
            
            embedding = result[0]["embedding"] if result else []
            
            return {
                "embedding": embedding,
                "success": len(embedding) > 0
            }
        except Exception as e:
            # If primary method fails, try with detection enabled
            try:
                result = DeepFace.represent(
                    img_path=temp_path,
                    model_name="ArcFace",
                    enforce_detection=True,
                    detector_backend="retinaface",
                    align=True
                )
                
                embedding = result[0]["embedding"] if result else []
                
                return {
                    "embedding": embedding,
                    "success": len(embedding) > 0
                }
            except Exception as e2:
                print(f"❌ DeepFace Error: {str(e)}")
                return {
                    "embedding": [],
                    "success": False,
                    "error": f"Primary error: {str(e)}, Fallback error: {str(e2)}"
                }
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


@app.function(
    image=deepface_image,
    timeout=30,
    memory=1024,
)
def verify_embeddings(embedding1: list, embedding2: list, threshold: float = 0.40) -> dict:
    """
    Compare two ArcFace embeddings using cosine similarity.
    """
    import numpy as np
    
    if not embedding1 or not embedding2:
        return {"verified": False, "similarity": 0.0}
    
    a = np.array(embedding1)
    b = np.array(embedding2)
    
    # Cosine similarity
    similarity = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    return {
        "verified": similarity > threshold,
        "similarity": similarity
    }


@app.local_entrypoint()
def main(image_path: str = "test_face.jpg"):
    """CLI test: modal run app/modal_deepface.py --image-path face.jpg"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    import os
    if not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        return

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    embedder = DeepFaceEmbedder()
    result = embedder.get_embedding.remote(image_bytes)
    
    if result["success"]:
        logger.info(f"Embedding extracted! Length: {len(result['embedding'])}")
    else:
        logger.error(f"Failed: {result.get('error', 'Unknown error')}")
