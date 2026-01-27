import uvicorn
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    # Ensure spawn method is used (default on Windows, but good to be explicit for stability)
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
        
    print("Starting Server in STABLE mode (Reload Disabled for camera stability)...")
    
    # Auto-setup ffmpeg path for pydub
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except ImportError:
        print("Warning: static-ffmpeg not found. Audio processing will fail if ffmpeg is not in PATH.")

    import os
    import socket
    
    # Get local IP for easier connecting
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    ssl_config = {}
    if os.path.exists("cert.pem") and os.path.exists("key.pem"):
        print(f"\n[SECURE MODE] SSL Certificates found.")
        print(f" -> Access from your laptop at: https://{local_ip}:8000")
        print(f" -> Access from your laptop at: https://0.0.0.0:8000 (if IP dynamic)")
        ssl_config = {
            "ssl_keyfile": "key.pem",
            "ssl_certfile": "cert.pem"
        }
    else:
        print("\n[WARNING] No SSL Certificates found. Camera/Mic will ONLY work on localhost.")
        print(" -> Run `python tools/generate_cert.py` to enable remote access.")

    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=False, **ssl_config)
