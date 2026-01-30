# AI-Powered Recruitment & Interview Backend

A robust, high-performance API backend that integrates **Computer Vision Proctoring** with **LLM-based Technical Evaluation**. This project is architected as a headless service to support decoupled frontend applications.

## Features

### 1. Advanced AI Proctoring (Vision)
- **Face Recognition**: Verifies candidate identity using ArcFace (DeepFace).
- **Gaze Detection**: High-accuracy monitoring for eye deviation using MediaPipe.
- **Security Alerts**: Real-time detection of multiple faces or suspicious activity via WebSockets.

### 2. Automated Interview Service (Speech & NLP)
- **STT/TTS Pipeline**: 
  - Real-time transcription of candidate answers using **Faster-Whisper**.
  - Natural question-reading via **Edge-TTS**.
- **LLM Assessment**: Automated technical scoring and feedback generation using LangChain (Qwen/Llama).
- **Speaker Verification**: AI-powered audio fingerprinting to ensure the correct candidate is speaking.

## Installation & Setup

1. **Environment Config**:
   Copy `.env.example` to `.env` and fill in your credentials.
   ```bash
   cp .env.example .env
   ```

2. **Run with Docker (Recommended)**:
   ```bash
   docker compose up --build -d
   ```

3. **Manual Start**:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

4. **HTTPS / Camera Requirement**:
   To enable camera access on non-localhost devices, run the cert generator:
   ```bash
   python3 tools/generate_cert.py
   ```
   For detailed instructions on trusting certificates or using Ngrok, see the [SSL Configuration Guide](docs/SSL_GUIDE.md).

## API Documentation
The API documentation is automatically generated and accessible via Swagger UI when the server is running:
- **Swagger**: `https://localhost:8000/docs`
- **Audit Tool**: Run `python3 tests/integration/test_api.py` to verify system health.

## Standardized Project Structure
- `app/core/`: Application constants, unified logger, and database connections.
- `app/models/`: SQLModel database schemas.
- `app/routers/`: Modularized API endpoints (Auth, Admin, Candidate, Interview).
- `app/services/`: Core business logic implementing Vision, Audio, and NLP pipelines.
- `app/assets/`: Persistent storage for models, audio recordings, and logs.
- `tests/`: Integration and unit test suites.
- `scripts/`: Production management utilities (seeding, migration, admin creation).

## Development Guidelines
- **API First**: Headless architecture ensuring all communication is handled via standardized JSON responses.
- **Security**: Uses HttpOnly, Secure cookies for JWT session management.
- **Verification**: Always run the integration tests (`tests/integration/test_api.py`) before pushing code.

