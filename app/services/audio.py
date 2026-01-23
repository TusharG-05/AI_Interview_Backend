import os
import asyncio
import edge_tts
from faster_whisper import WhisperModel
import numpy as np
import torch
import soundfile as sf
import resampy
from scipy.signal import butter, lfilter
from speechbrain.inference.speaker import EncoderClassifier
import noisereduce as nr


class AudioService:
    def __init__(self, stt_model_size="base"):
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
            print(f"Loading Whisper Model ({self.stt_model_size})...")
            self._stt_model = WhisperModel(
                self.stt_model_size,
                device="cpu",
                compute_type="int8"
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
        Applies noise reduction and saves to the same file.
        Returns the path to the cleaned audio.
        """
        try:
            audio, sr = self.load_audio(audio_path)
            # Gentle noise reduction
            reduced = nr.reduce_noise(y=audio, sr=sr, prop_decrease=0.8)
            self.save_audio(reduced, sr, audio_path)
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
            segments, _ = self.stt_model.transcribe(audio_path, beam_size=5)
            return " ".join(seg.text for seg in segments).strip()
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

    def save_audio_blob(self, blob, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(blob)
        return output_path
