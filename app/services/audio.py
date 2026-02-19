import os
import asyncio
from ..core.logger import get_logger

logger = get_logger(__name__)

# Modal integration flag
USE_MODAL = os.getenv("USE_MODAL", "false").lower() == "true"

# Lazy import Modal only when needed
_modal_transcribe = None

def get_modal_transcribe():
    """Lazy load Modal Whisper class to avoid import errors."""
    global _modal_transcribe
    if _modal_transcribe is None:
        try:
            import modal
            # Use from_name for lazy reference to deployed class
            # Note: Deployment name is 'interview-whisper-stt', Class name is 'WhisperSTT'
            _modal_transcribe = modal.Cls.from_name("interview-whisper-stt", "WhisperSTT")
            logger.info("Modal Whisper class reference obtained")
        except Exception as e:
            logger.warning(f"Modal Whisper not available: {e}")
            return None
    return _modal_transcribe


class AudioService:
    def __init__(self, stt_model_size="base.en"):
        logger.info(f"Initializing AudioService (Lazy Loading enabled)...")
        logger.info(f"Modal STT: {'ENABLED' if USE_MODAL else 'DISABLED (local)'}")
        self.stt_model_size = stt_model_size
        self.female_voice = "en-US-AvaNeural"
        
        # Models (Lazy loaded)
        self._stt_model = None
        self._speaker_model = None
        self.verification_threshold = 0.25

    @property
    def stt_model(self):
        # Prevent loading heavy local model on HF Spaces
        if os.getenv("SPACE_ID"):
            logger.warning("Local STT model loading blocked on HF Spaces to prevent OOM")
            return None

        if self._stt_model is None:
            import torch
            from faster_whisper import WhisperModel
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading Whisper Model ({self.stt_model_size}) on {device}...")
            self._stt_model = WhisperModel(
                self.stt_model_size,
                device=device,
                compute_type="int8" if device == "cpu" else "float16", 
                cpu_threads=4
            )
        return self._stt_model

    @property
    def speaker_model(self):
        if self._speaker_model is None:
            import torch
            from speechbrain.inference.speaker import EncoderClassifier
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading Speaker Verification Model on {device}...")
            self._speaker_model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb", 
                run_opts={"device": device},
                savedir="/tmp/speechbrain_model"
            )
        return self._speaker_model

    async def hf_inference_stt(self, audio_path: str) -> str:
        """Secondary lightweight STT using HF Inference API."""
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            logger.warning("HF_TOKEN not set, skipping HF Inference STT")
            return ""

        try:
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=hf_token)
            
            logger.info("Attempting HF Inference API for STT...")
            # Passing the path directly allows the client to detect content type
            result = client.automatic_speech_recognition(
                audio=audio_path,
                model="openai/whisper-large-v3-turbo"
            )
            text = result.get("text", "").strip()
            logger.info(f"HF Inference STT successful: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"HF Inference STT Error: {e}")
            return ""

    async def speech_to_text(self, audio_path):
        if not os.path.exists(audio_path):
            return ""

        last_error = None

        try:
            # 1. Try Modal if enabled
            if USE_MODAL:
                modal_cls = get_modal_transcribe()
                if modal_cls:
                    try:
                        logger.info(f"Using Modal for STT: {audio_path}")
                        loop = asyncio.get_running_loop()
                        
                        def _modal_call():
                            with open(audio_path, "rb") as f:
                                audio_bytes = f.read()
                            # Instantiate class and call remote method
                            result = modal_cls().transcribe.remote(audio_bytes, self.stt_model_size)
                            if "error" in result:
                                raise Exception(result["error"])
                            return result.get("text", "")
                        
                        text = await loop.run_in_executor(None, _modal_call)
                        if text: return text
                    except Exception as e:
                        last_error = f"Modal STT failed: {str(e)}"
                        logger.warning(last_error)
            
            # 2. Secondary Fallback: HF Inference API (Lightweight)
            hf_text = await self.hf_inference_stt(audio_path)
            if hf_text:
                return hf_text

            # 3. Local Fallback (Only if NOT on HF Spaces)
            if not os.getenv("SPACE_ID"):
                logger.info("Falling back to local STT...")
                model = self.stt_model
                if model:
                    loop = asyncio.get_running_loop()
                    def _transcribe():
                        segments, info = model.transcribe(
                            audio_path, 
                            beam_size=1, 
                            vad_filter=True,
                            vad_parameters=dict(min_silence_duration_ms=500),
                            no_speech_threshold=0.5
                        )
                        return " ".join(seg.text for seg in segments).strip()

                    text = await loop.run_in_executor(None, _transcribe)
                    return text if text else "[Silence/No Speech Detected]"
            else:
                msg = "Cloud Environment detected. Skipping heavy local STT fallback."
                logger.error(msg)
                if not last_error:
                    last_error = msg

            return f"[STT Error: {last_error or 'Services unavailable'}]"
            
        except Exception as e:
            logger.error(f"Overall STT Error: {e}")
            return ""

    async def text_to_speech(self, text, output_path):
        """Converts text to speech using edge-tts."""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, self.female_voice)
            await communicate.save(output_path)
            logger.info(f"TTS generated: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return None

    def save_audio_blob(self, blob, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(blob)
        return output_path

    def calculate_energy(self, audio_path):
        """Calculates RMS energy of an audio file to detect silence."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return audio.rms
        except Exception as e:
            logger.error(f"Energy Check Error: {e}")
            return 0

    def convert_to_wav(self, input_path):
        """Converts any audio file to WAV format and returns the path."""
        try:
            from pydub import AudioSegment
            output_path = input_path.rsplit(".", 1)[0] + ".wav"
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format="wav")
            return output_path
        except Exception as e:
            logger.error(f"WAV Conversion Error: {e}")
            return None

    def cleanup_audio(self, *paths):
        """Removes specified audio files from disk."""
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.error(f"Cleanup Error for {path}: {e}")
