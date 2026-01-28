import os
import asyncio
import edge_tts
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

import numpy as np

try:
    import torch
except ImportError:
    torch = None

try:
    import soundfile as sf
except ImportError:
    sf = None

try:
    import resampy
except ImportError:
    resampy = None

try:
    from scipy.signal import butter, lfilter
except ImportError:
    butter = None
    lfilter = None

try:
    import noisereduce as nr
except ImportError:
    nr = None


class AudioService:
    def __init__(self, stt_model_size="base"):
        print(f"Initializing AudioService (Lazy Loading enabled)...")
        self.stt_model_size = stt_model_size
        self.female_voice = "en-US-AvaNeural"
        
        self._stt_model = None

    @property
    def stt_model(self):
        if self._stt_model is None:
            if WhisperModel is None:
                print("Audio dependencies (Whisper) missing. STT disabled.")
                return None
            print(f"Loading Whisper Model ({self.stt_model_size})...")
            self._stt_model = WhisperModel(
                self.stt_model_size,
                device="cpu",
                compute_type="int8"
            )
        return self._stt_model

    async def text_to_speech(self, text, output_path):
        communicate = edge_tts.Communicate(text, self.female_voice)
        await communicate.save(output_path)
        return output_path

    # ---------- WINDOWS SAFE AUDIO ----------
    def load_audio(self, audio_path, target_sr=None):
        if sf is None:
            print("Audio dependencies (soundfile) missing. Cannot load audio.")
            return np.zeros(10), 16000

        audio, sr = sf.read(audio_path)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        if target_sr and sr != target_sr:
            audio = resampy.resample(audio, sr, target_sr)
            sr = target_sr

        return audio.astype(np.float32), sr

    def save_audio(self, audio, sr, path):
        if sf is None:
            return
        sf.write(path, audio, sr)

    def cleanup_audio(self, audio_path):
        try:
            audio, sr = self.load_audio(audio_path)
            if nr is None:
                print("Audio dependencies (noisereduce) missing. Skipping cleanup.")
                return audio_path
            
            reduced = nr.reduce_noise(y=audio, sr=sr, prop_decrease=0.8)
            self.save_audio(reduced, sr, audio_path)
            return audio_path
        except Exception as e:
            print(f"Audio Cleanup Error: {e}")
            return audio_path

    def speech_to_text(self, audio_path):
        if not os.path.exists(audio_path):
            return ""

        try:
            segments, _ = self.stt_model.transcribe(audio_path, beam_size=5)
            text = " ".join(seg.text for seg in segments).strip()
            print(f"Transcribed: {text}")
            return text
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

    def save_audio_blob(self, blob, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(blob)
        return output_path
