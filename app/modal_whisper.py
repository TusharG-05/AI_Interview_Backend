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
    .pip_install("faster-whisper==1.0.3", "numpy")
)


@app.function(
    image=whisper_image,
    gpu="T4",  # NVIDIA T4 - good balance of speed/cost
    timeout=120,
    retries=2,
    memory=4096,  # 4GB RAM
)
def transcribe(audio_bytes: bytes, model_size: str = "base.en") -> dict:
    """
    Transcribes audio bytes to text using Whisper on GPU.
    
    Args:
        audio_bytes: Raw audio file bytes (WAV, MP3, etc.)
        model_size: Whisper model size (tiny, base, small, medium, large)
    
    Returns:
        dict with 'text' and 'language' keys
    """
    import tempfile
    import os
    from faster_whisper import WhisperModel
    
    # Write bytes to temp file (faster-whisper needs file path)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    
    try:
        # Load model on GPU
        model = WhisperModel(
            model_size,
            device="cuda",
            compute_type="float16"  # FP16 for GPU speed
        )
        
        # Transcribe with interview-optimized settings
        segments, info = model.transcribe(
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
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.local_entrypoint()
def main(audio_path: str = "test.wav"):
    """CLI entrypoint for testing: modal run app/modal_whisper.py --audio-path audio.wav"""
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    
    result = transcribe.remote(audio_bytes)
    print(f"Transcription: {result['text']}")
    print(f"Language: {result['language']}")
    print(f"Duration: {result['duration']:.2f}s")
