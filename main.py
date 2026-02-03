import uvicorn
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import shutil
import multiprocessing
from app.server import app

if __name__ == "__main__":
    # Removed multiprocessing.freeze_support() and set_start_method('spawn') 
    # as they were causing segmentation faults with certain AI libraries on Linux.
    
    print("Starting Server in API-ONLY Mode...")
    
    # Ensure ffmpeg is available
    if not shutil.which("ffmpeg"):
        try:
            import static_ffmpeg
            static_ffmpeg.add_paths()
        except ImportError:
            print("Warning: static_ffmpeg not installed.")
            
    ssl_config = {}
    if os.path.exists("cert.pem") and os.path.exists("key.pem"):
        print(f"\n[SECURE MODE] SSL Certificates found.")
        ssl_config = {
            "ssl_keyfile": "key.pem",
            "ssl_certfile": "cert.pem"
        }
    else:
        print("\n[WARNING] No SSL Certificates found. HTTPS disabled.")

    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=False, **ssl_config)
