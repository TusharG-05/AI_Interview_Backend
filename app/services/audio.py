import os
import asyncio
import edge_tts
from faster_whisper import WhisperModel
import numpy as np
import torch
import soundfile as sf
from speechbrain.inference.speaker import EncoderClassifier
from pydub import AudioSegment


class AudioService:
    def __init__(self, stt_model_size="tiny.en"):
        print(f"Initializing AudioService (Lazy Loading enabled)...")
        self.stt_model_size = stt_model_size
        self.female_voice = "en-US-AvaNeural"
        
        # Models (Lazy loaded)
        self._stt_model = None
        self._speaker_model = None
        self.verification_threshold = 0.25

    @property
    def stt_model(self):
        if self._stt_model is None:
            # Sweet spot: base.en is much better than tiny, faster than base.
            model_to_use = "base.en" if self.stt_model_size != "tiny.en" else "tiny.en"
            print(f"Loading Whisper Model ({model_to_use})...")
            self._stt_model = WhisperModel(
                model_to_use,
                device="cpu",
                compute_type="float32", 
                cpu_threads=2 # Leave cores for camera/gaze to avoid 15min hang
            )
        return self._stt_model

    @property
    def speaker_model(self):
        if self._speaker_model is None:
            print("Loading Speaker Verification Model...")
            self._speaker_model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                run_opts={"device": "cpu"}
            )
        return self._speaker_model

    async def text_to_speech(self, text, output_path):
        communicate = edge_tts.Communicate(text, self.female_voice)
        await communicate.save(output_path)
        return output_path

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
            print(f"DEBUG: Converted {file_path} to 16kHz WAV.")
        except Exception as e:
            print(f"ERROR converting audio {file_path}: {e}")

    def load_audio(self, audio_path, target_sr=None):
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
        try:
            self.fix_audio_format(audio_path)
            return audio_path
        except Exception as e:
            print(f"Audio Cleanup Error: {e}")
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

    def speech_to_text(self, audio_path):
        if not os.path.exists(audio_path):
            return ""

        # Assumes audio_path is already cleaned if desired
        try:
            # optimized for speed & accuracy
            segments, info = self.stt_model.transcribe(
                audio_path, 
                beam_size=1, 
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                no_speech_threshold=0.5, # Stops "bathroom" hallucinations
                initial_prompt="Interview answer about technology and programming."
            )
            text = " ".join(seg.text for seg in segments).strip()
            # If still nothing, return a clean string
            return text if text else "[Silence/No Speech Detected]"
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

    def save_audio_blob(self, blob, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(blob)
        return output_path
