"""
Modal.com app for GPU-accelerated DeepFace face recognition.

Deploy: modal deploy app/modal_deepface.py
Test:   modal run app/modal_deepface.py --image-path /path/to/face.jpg
"""
import modal

app = modal.App("interview-deepface")

# Container image with DeepFace and OpenCV
deepface_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0")
    .pip_install(
        "deepface==0.0.93",
        "opencv-python-headless",
        "numpy",
        "tf-keras"
    )
)


@app.function(
    image=deepface_image,
    gpu="T4",  # T4 is sufficient for ArcFace
    timeout=60,
    memory=4096,
    container_idle_timeout=300,  # Keep warm for 5 mins
)
def get_embedding(image_bytes: bytes) -> dict:
    """
    Extract ArcFace embedding from a face image.
    
    Args:
        image_bytes: Raw image bytes (JPEG, PNG, etc.)
    
    Returns:
        dict with 'embedding' (list of floats) and 'success' (bool)
    """
    import tempfile
    import os
    import numpy as np
    from deepface import DeepFace
    
    # Write bytes to temp file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(image_bytes)
        temp_path = f.name
    
    try:
        # Extract embedding using ArcFace
        result = DeepFace.represent(
            img_path=temp_path,
            model_name="ArcFace",
            enforce_detection=False,
            detector_backend="skip",  # Assume face is already cropped
            align=False
        )
        
        embedding = result[0]["embedding"] if result else []
        
        return {
            "embedding": embedding,
            "success": len(embedding) > 0
        }
    except Exception as e:
        return {
            "embedding": [],
            "success": False,
            "error": str(e)
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.function(
    image=deepface_image,
    timeout=30,
    memory=1024,
)
def verify_embeddings(embedding1: list, embedding2: list, threshold: float = 0.40) -> dict:
    """
    Compare two ArcFace embeddings using cosine similarity.
    
    Args:
        embedding1: First face embedding
        embedding2: Second face embedding
        threshold: Similarity threshold (default 0.40 for ArcFace)
    
    Returns:
        dict with 'verified' (bool) and 'similarity' (float)
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
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    result = get_embedding.remote(image_bytes)
    
    if result["success"]:
        print(f"Embedding extracted! Length: {len(result['embedding'])}")
    else:
        print(f"Failed: {result.get('error', 'Unknown error')}")
