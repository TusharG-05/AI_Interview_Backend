"""
Modal.com app for GPU-accelerated Whisper speech-to-text.

Deploy: modal deploy app/modal_whisper.py
Test:   modal run app/modal_whisper.py::transcribe --audio-path /path/to/audio.wav
"""
import modal

# Define the Modal app
app = modal.App("interview-whisper-stt")

# Define the container image with faster-whisper
whisper_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "faster-whisper==1.0.3", 
        "numpy<2.0.0", 
        "requests",
        "nvidia-cublas-cu12",
        "nvidia-cudnn-cu12"
    )
    # Ensure CTranslate2 can find the pip-installed CUDA libraries
    .env({
        "LD_LIBRARY_PATH": "/usr/local/lib/python3.11/site-packages/nvidia/cublas/lib:/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib"
    })
)


@app.cls(
    image=whisper_image,
    gpu="T4",  # NVIDIA T4 - good balance of speed/cost
    timeout=120,
    retries=2,
    memory=4096,  # 4GB RAM
    scaledown_window=300, # Keep warm for 5 mins
)
class WhisperSTT:
    @modal.enter()
    def load_model(self):
        """Load Whisper model once when the container starts."""
        import time
        from faster_whisper import WhisperModel
        
        print("🚀 Loading Whisper Model...")
        start_time = time.time()
        self.model = WhisperModel(
            "base.en", # Default size, can be overridden if needed via logic
            device="cuda",
            compute_type="float16"
        )
        print(f"✨ Whisper Model Loaded in {time.time() - start_time:.2f}s")

    @modal.method()
    def transcribe(self, audio_bytes: bytes, model_size: str = "base.en") -> dict:
        """
        Transcribes audio bytes to text using Whisper on GPU.
        
        Args:
            audio_bytes: Raw audio file bytes (WAV, MP3, etc.)
            model_size: Whisper model size (currently using pre-loaded base.en)
        
        Returns:
            dict with 'text' and 'language' keys
        """
        import tempfile
        import os
        
        # Write bytes to temp file (faster-whisper needs file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        try:
            # Transcribe with interview-optimized settings
            segments, info = self.model.transcribe(
                temp_path,
                beam_size=3,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                no_speech_threshold=0.5,
                initial_prompt="Interview answer about technology and programming."
            )
            
            text = " ".join(seg.text for seg in segments).strip()
            
            return {
                "text": text if text else "[Silence/No Speech Detected]",
                "language": info.language,
                "duration": info.duration
            }
        except Exception as e:
            print(f"❌ Transcription Error: {str(e)}")
            return {"error": str(e), "text": ""}
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)


@app.local_entrypoint()
def main(audio_path: str = "test.wav"):
    """CLI entrypoint for testing: modal run app/modal_whisper.py --audio-path audio.wav"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    
    stt = WhisperSTT()
    result = stt.transcribe.remote(audio_bytes)
    
    if "error" in result:
        logger.error(f"Failed: {result['error']}")
    else:
        logger.info(f"Transcription: {result['text']}")
        logger.info(f"Language: {result['language']}")
        logger.info(f"Duration: {result.get('duration', 0):.2f}s")
