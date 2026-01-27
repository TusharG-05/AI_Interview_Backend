# AI-Driven Interview & Security Monitor

A professional, real-time security monitoring and interview system powered by FastAPI and modern AI models. This system features multi-face detection, gaze tracking, automated audio interviews with speaker verification, and document-based question management.

## 🚀 Key Features

### 🔐 Security & Monitoring
- **Real-time Face Recognition**: High-FPS multi-face detection using MediaPipe and ArcFace (DeepFace).
- **Gaze Tracking**: Detects suspicious behavior (looking left, right, up, down, or blinking/sleeping) with distance-adaptive sensitivity.
- **Worker Auto-Recovery**: Background AI processes automatically restart if they crash.
- **Microphone Signal Check**: Alerts user if they attempt enrollment with a silent or muted microphone.

### 🎙️ Audio Interview System
- **High-Accuracy Transcription**: Powered by **Faster-Whisper (base.en)** with `int8` quantization for optimal CPU performance.
- **Professional TTS**: Automated question delivery using `edge-tts` neural voices.
- **Semantic Evaluation**: AI-driven answer checking using `Sentence-Transformers`.

### 🛠️ Admin Features
- **Centralized Dashboard**: Manage questions and view detailed interview results at `/admin-panel`.
- **Bulk Question Import**: Automated extraction from **PDF**, **Word (.docx)**, or **Text (.txt)**.
- **N+1 Optimized API**: Optimized database layer for high scalability.

---

## 🛠️ Quick Start

### Prerequisites
- **Python 3.11** (Recommended)
- Webcam & Microphone
- Dependencies: `pip install -r requirements.txt`

### Installation
1.  **Create a Virtual Environment**:
    ```bash
    python3.11 -m venv .venv
    source .venv/bin/activate
    ```
2.  **Install AI Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Running the App
```bash
python main.py
```
- **Interview Site**: `https://localhost:8000`
- **Admin Panel**: `https://localhost:8000/admin-panel`

---

## 📂 Project Structure

```
├── app/
│   ├── core/                # Database & Models
│   ├── routers/             # API Endpoints
│   ├── services/            # AI & Business Logic
│   ├── utils/               # Shared Helper Functions (Image Processing, etc.)
│   ├── templates/           # UI Templates
│   └── assets/              # AI Models & Audio Cache
├── main.py                  # Entry Point
└── requirements.txt         # Frozen Dependencies
```

---

## 🔧 AI Models Used
- **Vision**: MediaPipe FaceLandmarker, ArcFace (DeepFace)
- **Audio**: Faster-Whisper (base.en), SpeechBrain (ECAPA-VoxCeleb), Edge-TTS
- **NLP**: all-MiniLM-L6-v2 (Sentence-Transformers)
