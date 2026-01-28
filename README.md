# Face/Gaze Aware AI Interview Platform

A cutting-edge, production-ready technical interview platform that combines **Deep Learning Proctoring** with **LLM-based Technical Evaluation**.

## Features

### 1. Advanced Proctoring
- **Face Recognition**: Verifies candidate identity against a known profile using ArcFace.
- **Gaze Detection**: Monitors for eye gaze deviation (e.g., looking at second screens or notes).
- **Multi-Face Alert**: Detects and flags the presence of multiple people in the frame.

### 2. AI Interview Loop
- **Resume-Driven**: Upload a PDF resume to generate tailored technical questions.
- **Dynamic Interaction**: 
  - **TTS (Text-to-Speech)** reads questions to the candidate.
  - **STT (Speech-to-Text)** transcribes spoken answers in real-time.
- **LLM Evaluation**: Provides nuanced technical scoring (0-10) and qualitative feedback using **Llama/Qwen**.

## Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLModel (SQLite/PostgreSQL)
- **AI/ML**:
  - **Vision**: MediaPipe, DeepFace (ArcFace)
  - **Speech**: Faster-Whisper, Edge-TTS
  - **LLM**: LangChain, Ollama
- **Infrastructure**: Docker, Gunicorn

## Quick Start (Local)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Ollama**:
   Ensure Ollama is running with the required model:
   ```bash
   ollama run qwen2.5-coder:3b
   ```

3. **Start the App**:
   ```bash
   python main.py
   ```
   Access the UI at `http://localhost:8000`.

## Access from Other Devices (Mobile/Tablet)

To access the platform from another device on the same network:

1. **Find your Local IP**: 
   Run `hostname -I` (Linux) or `ipconfig` (Windows) to get your IP (e.g., `192.168.1.15`).
2. **Enable HTTPS (Required for Camera)**:
   Browsers block camera/mic access on `http` for remote IPs. You **must** use `https`.
   - Run `python tools/generate_cert.py` to create `cert.pem` and `key.pem`.
   - Restart the app.
3. **Connect**:
   Visit `https://<YOUR_IP>:8000` on your other device. 
   *(Note: You will see a "Your connection is not private" warning because the certificate is self-signed. Click "Advanced" -> "Proceed" to continue.)*

## Production Deployment

### Docker (Recommended)

1. **Build and Tag**:
   The project is pre-configured for the **`tusharg05`** Docker Hub account.
   ```bash
   docker compose build
   ```

2. **Push to Docker Hub**:
   ```bash
   docker login
   docker compose push
   ```

3. **Deploy**:
   ```bash
   docker compose up -d
   ```

2. **Environment Variables**:
   Create a `.env` file with your production settings:
   ```env
   SECRET_KEY=your-secure-secret
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   DATABASE_URL=sqlite:///./interview_system.db
   ```

## Project Structure
- `app/core/`: Configuration, database init, and unified logging.
- `app/routers/`: API endpoints (Interview, Proctoring, Auth, Admin).
- `app/services/`: Core logic (Vision, Speech, LLM).
- `app/assets/`: Static assets (models, audio, logs).
- `app/templates/`: Jinja2 UI templates.
- `Non_usable/`: Legacy code and temporary files (segregated from production).

## Security & Ethics
This platform is designed for professional evaluation. Always ensure candidates are informed about the AI monitoring features and data usage policies before starting an interview.
