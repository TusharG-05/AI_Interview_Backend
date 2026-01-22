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
        print(f"Initializing AudioService (STT: {stt_model_size})...")

        self.female_voice = "en-US-AvaNeural"

        # STT Model
        self.stt_model = WhisperModel(
            stt_model_size,
            device="cpu",
            compute_type="int8"
        )

        # Speaker Verification Model
        print("Loading Speaker Verification Model...")
        self.speaker_model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            run_opts={"device": "cpu"}
        )

        self.verification_threshold = 0.25
        print("AudioService initialized.")

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

    def reduce_noise(self, audio_path):
        audio, sr = self.load_audio(audio_path)
        reduced = nr.reduce_noise(y=audio, sr=sr, prop_decrease=0.8)
        self.save_audio(reduced, sr, audio_path)
        return audio_path

    def get_voice_print(self, audio_path):
        audio, sr = self.load_audio(audio_path, target_sr=16000)
        signal = torch.tensor(audio).unsqueeze(0)
        embeddings = self.speaker_model.encode_batch(signal)
        return embeddings

    def verify_speaker(self, enrollment_audio, test_audio):
        self.reduce_noise(test_audio)

        emb1 = self.get_voice_print(enrollment_audio)
        emb2 = self.get_voice_print(test_audio)

        similarity = torch.nn.functional.cosine_similarity(emb1, emb2)
        score = float(similarity[0][0])

        return score >= self.verification_threshold, score

    def speech_to_text(self, audio_path):
        if not os.path.exists(audio_path):
            return ""

        self.reduce_noise(audio_path)

        segments, _ = self.stt_model.transcribe(audio_path, beam_size=5)
        return " ".join(seg.text for seg in segments).strip()

    def save_audio_blob(self, blob, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(blob)
        return output_path
