import os
import asyncio
import edge_tts
from faster_whisper import WhisperModel
import numpy as np
import torch
import soundfile as sf
import resampy
from speechbrain.inference.speaker import EncoderClassifier
from pydub import AudioSegment
from ..core.logger import get_logger

logger = get_logger(__name__)


class AudioService:
    def __init__(self, stt_model_size="base.en"):
        logger.info(f"Initializing AudioService (Lazy Loading enabled)...")
        self.stt_model_size = stt_model_size
        self.female_voice = "en-US-AvaNeural"
        
        # Models (Lazy loaded)
        self._stt_model = None
        self._speaker_model = None
        self.verification_threshold = 0.25

    @property
    def stt_model(self):
        if self._stt_model is None:
            # Upgrade: base.en with int8 quantization is faster/better on i7
            logger.info(f"Loading Whisper Model ({self.stt_model_size})...")
            self._stt_model = WhisperModel(
                self.stt_model_size,
                device="cpu",
                compute_type="int8", 
                cpu_threads=4 # i7 can handle more threads for faster results
            )
        return self._stt_model

    @property
    def speaker_model(self):
        if self._speaker_model is None:
            logger.info("Loading Speaker Verification Model...")
            self._speaker_model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                run_opts={"device": "cpu"}
            )
        return self._speaker_model

    async def text_to_speech(self, text, output_path):
        communicate = edge_tts.Communicate(text, self.female_voice)
        await communicate.save(output_path)
        return output_path

    # ---------- AUDIO VALIDATION & HARDENING ----------

    def validate_audio_integrity(self, file_path: str) -> bool:
        """Verifies if the file exists, has size, and is readable as audio."""
        if not os.path.exists(file_path):
            logger.error(f"Validation Failed: File does not exist at {file_path}")
            return False
            
        if os.path.getsize(file_path) < 100:
            logger.error(f"Validation Failed: File too small/empty at {file_path}")
            return False
            
        try:
            # Quick check: can we read the header?
            with sf.SoundFile(file_path) as f:
                if f.frames == 0:
                    logger.error(f"Validation Failed: Audio file has 0 frames {file_path}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Validation Failed: File is not a valid audio format: {e}")
            return False

    # ---------- WINDOWS SAFE AUDIO ----------

    def fix_audio_format(self, file_path: str):
        """Converts ANY audio (WebM, etc.) to 16kHz Mono WAV."""
        try:
            audio = AudioSegment.from_file(file_path)
            audio = audio.set_frame_rate(16000).set_channels(1)
            # Normalize to -20dBFS for consistent AI results
            change_in_dbfs = -20.0 - audio.dBFS
            audio = audio.apply_gain(change_in_dbfs)
            audio.export(file_path, format="wav")
            logger.debug(f"Converted {file_path} to 16kHz WAV.")
        except Exception as e:
            logger.error(f"Error converting audio {file_path}: {e}")

    def load_audio(self, audio_path, target_sr=None):
        if not self.validate_audio_integrity(audio_path):
            raise ValueError(f"Cannot load invalid audio file: {audio_path}")
            
        audio, sr = sf.read(audio_path)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        if target_sr and sr != target_sr:
            audio = resampy.resample(audio, sr, target_sr)
            sr = target_sr

        return audio.astype(np.float32), sr

    def save_audio(self, audio, sr, path):
        sf.write(path, audio, sr)

    def cleanup_audio(self, audio_path):
        """
        Windows-safe audio fix. Disables intensive NR for speed.
        The VAD filter in STT handles the rest.
        """
        if not self.validate_audio_integrity(audio_path):
            logger.warning(f"Skipping cleanup for invalid audio: {audio_path}")
            return audio_path
            
        try:
            self.fix_audio_format(audio_path)
            return audio_path
        except Exception as e:
            logger.error(f"Audio Cleanup Error: {e}")
            return audio_path

    def get_voice_print(self, audio_path):
        audio, sr = self.load_audio(audio_path, target_sr=16000)
        signal = torch.tensor(audio).unsqueeze(0)
        embeddings = self.speaker_model.encode_batch(signal)
        return embeddings

    def verify_speaker(self, enrollment_audio, test_audio):
        # Assumes test_audio is already cleaned if desired
        emb1 = self.get_voice_print(enrollment_audio)
        emb2 = self.get_voice_print(test_audio)

        similarity = torch.nn.functional.cosine_similarity(emb1, emb2)
        score = float(similarity[0][0])

        return score >= self.verification_threshold, score

    async def speech_to_text(self, audio_path):
        if not os.path.exists(audio_path):
            return ""

        # Assumes audio_path is already cleaned if desired
        try:
            loop = asyncio.get_running_loop()
            
            # Non-blocking wrapper for heavy STT
            def _transcribe():
                segments, info = self.stt_model.transcribe(
                    audio_path, 
                    beam_size=1, 
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    no_speech_threshold=0.5, # Stops "bathroom" hallucinations
                    initial_prompt="Interview answer about technology and programming."
                )
                return " ".join(seg.text for seg in segments).strip()

            text = await loop.run_in_executor(None, _transcribe)
            
            # If still nothing, return a clean string
            return text if text else "[Silence/No Speech Detected]"
        except Exception as e:
            logger.error(f"STT Error: {e}")
            return ""

    def save_audio_blob(self, blob, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(blob)
        return output_path

    def calculate_energy(self, audio_path):
        """Calculates RMS energy of an audio file to detect silence."""
        try:
            audio = AudioSegment.from_file(audio_path)
            return audio.rms
        except Exception as e:
            logger.error(f"Energy Check Error: {e}")
            return 0

    def convert_to_wav(self, input_path):
        """Converts any audio file to WAV format and returns the path."""
        try:
            output_path = input_path.rsplit(".", 1)[0] + ".wav"
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format="wav")
            return output_path
        except Exception as e:
            logger.error(f"WAV Conversion Error: {e}")
            return None
