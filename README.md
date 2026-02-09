# AI-Powered Proctoring & Interview System

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org)

A backend system for automated technical interviews, integrating computer vision for proctoring and LLMs for technical evaluation. This project operates as a headless service providing REST APIs for interview management, real-time monitoring, and result processing.

## Key Features

### Intelligent Proctoring
- **Identity Verification**: Database-backed face recognition using **ArcFace** (DeepFace).
- **Gaze Tracking**: Real-time monitoring of candidate eye movement (MediaPipe).
- **Ghost Mode**: Admin monitoring capability via WebRTC.

### AI Interviewer
- **Polyglot Evaluation**: Automated answer scoring using LLMs.
- **Adaptive Q&A**: Support for **Verbal** (Audio-in/Audio-out) and **Coding** (Text-in) questions.
- **Speech Pipeline**: Integrated `Faster-Whisper` for STT and `Edge-TTS` for voice synthesis.

### Management
- **Session Isolation**: Data separation for concurrent interview sessions.
- **Time-Aware Scheduling**: Tokenized invite links with scheduled activation windows.
- **Auditing**: Logging of proctoring events, answers, and scores.

---

## Architecture

The project is structured as a modular API service containerized with Docker.

```
├── app/
│   ├── routers/      # API Endpoints (Auth, Admin, Interview, Video)
│   ├── services/     # Core Logic (Camera, Audio, NLP)
│   ├── models/       # SQLModel Database Schemas
│   └── core/         # Config & Security
├── scripts/          # Simulation & Admin Utilities
└── tests/            # Integration Tests
```

To enable camera access on non-localhost devices, run the cert generator:
   ```bash
   python3 scripts/generate_cert.py
   ```
   For detailed instructions on trusting certificates or using Ngrok, see the [SSL Configuration Guide](docs/SSL_GUIDE.md).

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local dev)

### 1. Configure Environment
Copy the example configuration:
```bash
cp .env.example .env
# Edit .env with your specific secrets if needed
```

### 2. Run with Docker
Launch the application stack:
```bash
docker compose up --build -d
```
The API serves at: `http://localhost:8000`

### 3. API Documentation
Endpoints are documented via Swagger UI:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Modal Cloud (Optional GPU Acceleration)

For faster speech-to-text processing, you can offload Whisper to Modal's GPU cloud:

### 1. Install Modal CLI
```bash
pip install modal
modal token new
```

### 2. Deploy Whisper Function
```bash
modal deploy app/modal_whisper.py
```

### 3. Enable Modal in Your App
```bash
export USE_MODAL=true
uvicorn main:app --port 8001
```

> **Note:** By default `USE_MODAL=false`, so Docker/local uses CPU-based Whisper. Set `USE_MODAL=true` only when Modal is deployed.

---

## Testing

Run the integration test suite:
```bash
docker compose exec app python -m pytest tests/integration/test_api.py
```

---

## Security
- **Authentication**: JWT-based session management with HttpOnly cookies.
- **Access Control**: Role-based separation (Admin/Candidate).
- **Data Storage**: Binary storage for biometric data.

---

## License
Proprietary & Confidential.
