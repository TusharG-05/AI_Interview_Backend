import os
import asyncio
from pathlib import Path
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
            from huggingface_hub import snapshot_download

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading Speaker Verification Model on {device}...")
            
            # Fix for HF Spaces Permission Error / Windows Symlink Error
            # Use /tmp/models on HF Spaces as /app/models may be read-only
            if os.getenv("SPACE_ID"):
                save_path = os.path.abspath("/tmp/models/speechbrain")
            else:
                save_path = os.path.abspath("models/speechbrain")
                
            try:
                if not os.path.exists(os.path.join(save_path, "hyperparams.yaml")):
                    logger.info(f"Downloading SpeechBrain model to {save_path} (no symlinks)...")
                    os.makedirs(save_path, exist_ok=True)
                    snapshot_download(
                        repo_id="speechbrain/spkrec-ecapa-voxceleb",
                        local_dir=save_path,
                        local_dir_use_symlinks=False
                    )
            except Exception as e:
                logger.warning(f"Failed to pre-download model (SpeechBrain): {e}")

            # CRITICAL: Monkey-patch SpeechBrain's fetching to use COPY instead of SYMLINK
            # This prevents WinError 1314 when from_hparams internally fetches files
            try:
                import speechbrain.utils.fetching as sb_fetching
                from speechbrain.utils.fetching import LocalStrategy
                _original_fetch = sb_fetching.fetch

                def _patched_fetch(*args, **kwargs):
                    kwargs.setdefault("local_strategy", LocalStrategy.COPY)
                    if kwargs.get("local_strategy") == LocalStrategy.SYMLINK:
                        kwargs["local_strategy"] = LocalStrategy.COPY
                    return _original_fetch(*args, **kwargs)

                sb_fetching.fetch = _patched_fetch
                logger.info("Patched SpeechBrain fetch strategy: SYMLINK -> COPY")
            except Exception as patch_err:
                logger.warning(f"Could not patch SpeechBrain fetch strategy: {patch_err}")

            from speechbrain.inference.speaker import EncoderClassifier

            # CRITICAL: Use local path as source to verify files are local and avoid HF Hub symlinks
            self._speaker_model = EncoderClassifier.from_hparams(
                source=save_path, 
                run_opts={"device": device},
                savedir=save_path
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
            
            logger.info(f"Attempting HF Inference API for STT: {audio_path}")
            
            loop = asyncio.get_running_loop()
            def _hf_call():
                # CRITICAL: Use Path object to ensure huggingface-hub correctly detects file type
                return client.automatic_speech_recognition(
                    audio=Path(audio_path),
                    model="openai/whisper-large-v3-turbo"
                )
            
            result = await loop.run_in_executor(None, _hf_call)
            text = result.get("text", "").strip()
            logger.info(f"HF Inference STT successful: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"HF Inference STT Error: {e}")
            return ""

    async def groq_inference_stt(self, audio_path: str) -> str:
        """High-performance STT using Groq Whisper LPU."""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return ""

        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            
            logger.info(f"Attempting Groq LPU STT: {audio_path}")
            
            loop = asyncio.get_running_loop()
            def _groq_call():
                with open(audio_path, "rb") as file:
                    return client.audio.transcriptions.create(
                        file=(os.path.basename(audio_path), file.read()),
                        model="whisper-large-v3",
                        response_format="json",
                    )
            
            transcription = await loop.run_in_executor(None, _groq_call)
            text = transcription.text.strip()
            logger.info(f"Groq STT successful: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"Groq STT Error: {e}")
            return ""

    async def _ensure_local_path(self, audio_path: str) -> tuple[str, bool]:
        """
        Ensures the audio exists locally. If it's a URL, downloads it to a temp file.
        Returns (local_path, is_temporary)
        """
        if not audio_path:
            return "", False
            
        if audio_path.startswith(("http://", "https://")):
            import tempfile
            import requests
            try:
                # Use a specific extension based on URL if possible, otherwise .wav
                ext = ".wav"
                if ".mp3" in audio_path.lower(): ext = ".mp3"
                elif ".webm" in audio_path.lower(): ext = ".webm"
                
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                response = requests.get(audio_path, timeout=10)
                response.raise_for_status()
                temp.write(response.content)
                temp.close()
                return temp.name, True
            except Exception as e:
                logger.error(f"Failed to download audio from {audio_path}: {e}")
                return "", False
        
        # Already local
        if not os.path.exists(audio_path):
            return "", False
        return audio_path, False

    async def speech_to_text(self, audio_path: str) -> str:
        """
        Transcribes audio using a multi-layered fallback approach:
        1. Modal (Best accuracy/speed if enabled)
        2. Groq LPU (Extremely Fast)
        3. Hugging Face Inference API (Fallback)
        4. Local Whisper (Final fallback, disabled on cloud to prevent OOM)
        """
        local_path, is_temp = await self._ensure_local_path(audio_path)
        if not local_path:
            return ""

        last_error = None
        text = ""

        try:
            # 1. Try Modal if enabled (Runtime check for testability)
            use_modal_runtime = os.getenv("USE_MODAL", "false").lower() == "true"
            if use_modal_runtime:
                modal_cls = get_modal_transcribe()
                if modal_cls:
                    try:
                        logger.info(f"Using Modal for STT: {local_path}")
                        loop = asyncio.get_running_loop()
                        
                        def _modal_call():
                            with open(local_path, "rb") as f:
                                audio_bytes = f.read()
                            # Instantiate class and call remote method
                            result = modal_cls().transcribe.remote(audio_bytes, self.stt_model_size)
                            if "error" in result:
                                raise Exception(result["error"])
                            return result.get("text", "")
                        
                        text = await loop.run_in_executor(None, _modal_call)
                        if text:
                            return text
                    except Exception as e:
                        last_error = f"Modal STT failed: {str(e)}"
                        logger.warning(last_error)
            
            # 2. Secondary Fallback: Groq LPU (Extremely Fast)
            groq_text = await self.groq_inference_stt(local_path)
            if groq_text:
                return groq_text
            
            # 3. Tertiary Fallback: HF Inference API (Lightweight)
            hf_text = await self.hf_inference_stt(local_path)
            if hf_text:
                return hf_text

            # 4. Local Fallback (Disabled on HF Spaces to prevent OOM)
            is_cloud = os.getenv("SPACE_ID") is not None
            if not is_cloud:
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
                msg = "Cloud Environment detected. Skipping local STT fallback."
                logger.warning(msg)
                if not last_error:
                    last_error = msg

            # If all failed, return the accumulated last error
            return f"[STT Error: {last_error or 'All STT services failed'}]"
            
        except Exception as e:
            logger.error(f"Overall STT Error: {e}")
            return ""
        finally:
            if is_temp and local_path and os.path.exists(local_path):
                try: os.remove(local_path)
                except: pass

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

    async def verify_speaker(self, enrollment_audio, test_audio):
        """
        Verifies if the speaker in test_audio matches the enrollment_audio.
        Returns (is_match, score)
        """
        local_enroll, temp_enroll = await self._ensure_local_path(enrollment_audio)
        local_test, temp_test = await self._ensure_local_path(test_audio)
        
        if not local_enroll or not local_test:
            logger.warning(f"Speaker Verification skipped: missing files ({enrollment_audio}, {test_audio})")
            if temp_enroll: os.remove(local_enroll)
            if temp_test: os.remove(local_test)
            return True, 1.0 # Default to match if files missing to avoid blocking
            
        try:
            import torch
            
            # Prevent loading heavy model on HF Spaces if possible, or use lightweight approach
            if os.getenv("SPACE_ID"):
                logger.warning("Speaker Verification skipped on HF Spaces to save memory")
                return True, 1.0

            # 1. Trigger lazy loading of model
            model = self.speaker_model
            if not model:
                return True, 1.0

            # 2. Perform verification
            # SpeechBrain 1.0+ EncoderClassifier lacks verify_files.
            # We must encode both and calculate cosine similarity manually.
            
            # Load and encode enrollment audio
            wav_enroll = model.load_audio(local_enroll)
            emb_enroll = model.encode_batch(wav_enroll)
            
            # Load and encode test audio
            wav_test = model.load_audio(local_test)
            emb_test = model.encode_batch(wav_test)
            
            # Compute cosine similarity
            import torch.nn.functional as F
            # emb is usually [1, 1, 192] or [1, 192], ensure it's flattened for similarity
            similarity = F.cosine_similarity(emb_enroll.flatten(), emb_test.flatten(), dim=0).item()
            
            match = similarity >= self.verification_threshold
            
            logger.info(f"Speaker Verification: Match={match}, Similarity={similarity:.4f} (Threshold={self.verification_threshold})")
            return match, similarity
            
        except Exception as e:
            logger.error(f"Speaker Verification Error: {e}")
            return True, 1.0 # Default to match on error
        finally:
            if temp_enroll and local_enroll and os.path.exists(local_enroll):
                try: os.remove(local_enroll)
                except: pass
            if temp_test and local_test and os.path.exists(local_test):
                try: os.remove(local_test)
                except: pass

    def cleanup_audio(self, *paths):
        """Removes specified audio files from disk."""
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.error(f"Cleanup Error for {path}: {e}")
