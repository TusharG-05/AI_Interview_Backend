# AI-Driven Interview & Security Monitor

A professional, real-time security monitoring and interview system powered by FastAPI and modern AI models. This system features multi-face detection, gaze tracking, automated audio interviews with speaker verification, and document-based question management.

## 🚀 Key Features

### 🔐 Security & Monitoring
- **Real-time Face Recognition**: High-FPS multi-face detection using MediaPipe and ArcFace (DeepFace).
- **Gaze Tracking**: Detects suspicious behavior (looking left, right, up, down, or blinking/sleeping).
- **Speaker Verification**: Uses voice fingerprinting (ECAPA-TDNN) to ensure only the candidate answers, preventing accomplices or "cheatingmates".
- **Noise Robustness**: Built-in noise reduction for robust performance in office environments.

### 🎙️ Audio Interview System
- **Professional Female Voice**: Automated question delivery using `edge-tts`.
- **Intelligent Flow Control**: Microphone activates 2 seconds after the computer ends speaking.
- **Zero-Lag Architecture**: All heavy transcription (Faster-Whisper) and semantic evaluation run in a post-interview batch to preserve video performance.
- **Semantic Matching**: Concept-based answer checking using `Sentence-Transformers`.

### 🛠️ Admin Features
- **Hidden Admin Panel**: Access at `/admin-panel` to manage questions and view results.
- **Bulk Question Import**: Extract question-answer pairs automatically from **PDF**, **Word (.docx)**, or **Text (.txt)** files.

## 🛠️ Quick Start

### Prerequisites
- Python 3.9+
- Webcam & Microphone
- Dependencies: `pip install -r requirements.txt`

### Installation
1.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    ```
2.  **Install AI Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Running the App
```bash
python main.py
```
- **Interview Site**: `http://localhost:8000`
- **Admin Panel**: `http://localhost:8000/admin-panel`

---

## 📂 Project Structure

```
├── app/
│   ├── core/                # Database & Models
│   ├── routers/             # API Endpoints (Admin, Interview, Video, Site)
│   ├── services/            # Logic (Audio, NLP, Camera, Face, Gaze)
│   ├── templates/           # UI (Index, Admin)
│   └── assets/              # AI Models & Audio Cache
├── main.py                  # Entry Point
└── requirements.txt         # Frozen Dependencies
```

---

## 🔧 AI Models Used
- **Face Detection**: MediaPipe FaceLandmarker
- **Face recognition**: ArcFace (via DeepFace)
- **STT (Transcription)**: Faster-Whisper
- **TTS (Speech)**: Edge-TTS
- **Semantic Similarity**: all-MiniLM-L6-v2 (Sentence-Transformers)
- **Speaker Verification**: ECAPA-TDNN (SpeechBrain)
