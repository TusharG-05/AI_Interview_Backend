---
title: AI Interview Backend
emoji: 🎥
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

# AI-Powered Proctoring & Interview System

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org)
[![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery)](https://docs.celeryq.dev)

A full-stack platform for automated technical interviews, integrating computer vision for proctoring and LLMs for technical evaluation. The backend provides REST APIs for interview management, real-time monitoring, and result processing, while the frontend delivers a React-based admin dashboard and candidate interview experience.

---

## Key Features

### 🔍 Intelligent Proctoring
- **Identity Verification** — Database-backed face recognition using **ArcFace** (DeepFace) with selfie enrollment workflow.
- **Gaze Tracking** — Real-time monitoring of candidate eye movement via **MediaPipe** Face Landmarker.
- **Live Monitoring** — Admin monitoring capability via **WebRTC** (aiortc) and **WebSocket** dashboard with real-time status updates.
- **Proctoring Events** — Timestamped audit log of violations, warnings, and severity tracking.

### 🤖 AI Interviewer
- **Polyglot Evaluation** — Automated answer scoring using LLMs (Ollama / Modal-hosted).
- **Adaptive Q&A** — Support for **Verbal** (Audio-in/Audio-out) and **Coding** (Text-in) question types with configurable difficulty.
- **Speech Pipeline** — Integrated `Faster-Whisper` for STT, `Edge-TTS` for voice synthesis, and `SpeechBrain` for speaker verification.
- **Document-Based Question Generation** — Upload resumes, job descriptions, or Excel files to auto-generate questions via NLP.

### 📋 Interview Management
- **Session Isolation** — Data separation for concurrent interview sessions with per-session question subsets.
- **Time-Aware Scheduling** — Tokenized invite links with scheduled activation windows, duration limits, and expiry.
- **Email Notifications** — Dual-email service (SMTP + SendGrid fallback) for candidate invitations with invite links.
- **Candidate Lifecycle** — Full status tracking from `invited` → `link_accessed` → `authenticated` → `selfie_uploaded` → `enrollment` → `interview_active` → `completed`.
- **Background Processing** — Celery + Redis for asynchronous result evaluation, scoring, and email delivery.

### 🛡️ Security & Auth
- **JWT Authentication** — HttpOnly cookie-based session management.
- **Role-Based Access** — Three tiers: `super_admin`, `admin`, `candidate`.
- **Token-Based Interview Access** — Candidates access interviews via unique tokens (no account required).
- **Sentry Integration** — Production error tracking and performance monitoring.
- **Rate Limiting** — Redis-backed API rate limiting via `fastapi-limiter`.

---

## Architecture

```
├── app/
│   ├── routers/         # API Endpoints
│   │   ├── admin.py         # Paper, Question, Interview, User, Result CRUD
│   │   ├── auth.py          # JWT Login / Registration
│   │   ├── candidate.py     # Candidate-facing endpoints
│   │   ├── interview.py     # Interview flow (access, questions, answers, finish)
│   │   ├── settings.py      # Runtime configuration
│   │   └── video.py         # Camera & WebRTC streaming
│   ├── services/        # Core Business Logic
│   │   ├── audio.py         # STT (Whisper), TTS (Edge-TTS), Speaker Verification
│   │   ├── camera.py        # Frame capture & proctoring detectors
│   │   ├── email.py         # SMTP + SendGrid email delivery
│   │   ├── face.py          # DeepFace recognition & enrollment
│   │   ├── gaze.py          # MediaPipe gaze direction analysis
│   │   ├── interview.py     # Interview session orchestration
│   │   ├── nlp.py           # LLM-powered question extraction & evaluation
│   │   ├── status_manager.py# Candidate lifecycle state machine
│   │   ├── webrtc.py        # WebRTC peer connections (aiortc)
│   │   └── websocket_manager.py # Real-time admin dashboard broadcast
│   ├── models/          # SQLModel Database Schemas
│   ├── schemas/         # Pydantic Request/Response Models
│   ├── tasks/           # Celery Background Tasks (email, result processing)
│   ├── prompts/         # LLM Prompt Templates
│   ├── core/            # Config, Database, Logger, Celery
│   └── utils/           # Helpers & Image Processing
├── frontend/            # React (Vite) Admin Dashboard & Candidate UI
├── scripts/             # CLI Utilities (seed, migrate, deploy, certs)
├── tests/               # Unit & Integration Test Suites
├── docs/                # SSL Guide, API Testing Guide, DB Schema (DBML)
├── alembic/             # Database Migrations
├── Dockerfile           # Local dev (layered base image)
├── Dockerfile.hf        # Hugging Face Spaces deployment
└── docker-compose.yml   # Full stack: App + PostgreSQL + Ngrok
```

---

## API Overview

All endpoints are prefixed with `/api`. Full interactive docs are available at `/docs` (Swagger) and `/redoc`.

| Module | Endpoint Group | Description |
|--------|---------------|-------------|
| **Auth** | `POST /auth/login`, `POST /auth/register` | JWT authentication & user registration |
| **Admin — Papers** | `CRUD /admin/papers/{id}` | Create, list, update, delete question papers |
| **Admin — Questions** | `CRUD /admin/papers/{id}/questions` | Manage questions; upload documents for AI extraction |
| **Admin — Interviews** | `CRUD /admin/interviews/{id}` | Schedule, list, update, delete interview sessions |
| **Admin — Users** | `CRUD /admin/users/{id}` | Create, list, update, delete users with role management |
| **Admin — Results** | `GET /admin/results`, `GET /admin/result/{id}` | View & update scores, download response audio |
| **Admin — Live** | `GET /admin/live-status`, `WS /admin/ws/dashboard` | Real-time interview monitoring dashboard |
| **Interview** | `GET /interview/access/{token}` | Candidate validates and enters interview |
| **Interview** | `POST /interview/start/{id}` | Start session with enrollment audio |
| **Interview** | `POST /interview/selfie/{id}` | Upload reference selfie for face verification |
| **Interview** | `GET /interview/question/{id}` | Get next question in sequence |
| **Interview** | `POST /interview/answer/audio`, `/text` | Submit verbal or written answers |
| **Interview** | `POST /interview/finish/{id}` | Complete interview & trigger background evaluation |
| **Tools** | `POST /interview/stt`, `GET /interview/tts` | Standalone Speech-to-Text & Text-to-Speech |
| **Video** | `POST /video/frame` | Submit frames for proctoring analysis |
| **Settings** | `GET /settings/config` | Runtime application configuration |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local dev)
- PostgreSQL 15+ (or use the Docker Compose stack)

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials, secrets, and email config
```

Key environment variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key (auto-generated in dev) |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | SMTP credentials for invitations |
| `SENDGRID_API_KEY` | SendGrid fallback for email delivery |
| `SENTRY_DSN` | Sentry error tracking DSN (optional) |
| `USE_MODAL` | Enable Modal cloud GPU offloading (`true`/`false`) |
| `FRONTEND_URL` | Frontend URL for email invitation links |

### 2. Run with Docker Compose
```bash
docker compose up --build -d
```
This launches:
- **App** — FastAPI + Celery worker + Redis (port `8000`)
- **PostgreSQL** — Database (port `5432`)
- **Ngrok** — HTTPS tunnel for remote access (dashboard at port `4040`)

### 3. Run Locally (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python scripts/migrate.py

# Seed initial data (optional)
python scripts/seed_users.py
python scripts/seed_questions.py

# Start the server
python main.py
```
The API serves at `https://localhost:8000` (with SSL) or `http://localhost:8000`.

### 4. API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 5. SSL Configuration
To enable camera access on non-localhost devices:
```bash
python3 scripts/generate_cert.py
```
For detailed instructions on trusting certificates or using Ngrok, see the [SSL Configuration Guide](docs/SSL_GUIDE.md).

---

## Frontend

The React frontend is located in `frontend/` and built with **Vite**.

```bash
cd frontend
npm install
npm run dev
```
The frontend runs on `http://localhost:3000` and proxies API requests to the backend.

---

## Modal Cloud (Optional GPU Acceleration)

For faster AI processing, offload heavy models to Modal's GPU cloud:

### 1. Install & Authenticate
```bash
pip install modal
modal token new
```

### 2. Deploy Modal Functions
```bash
modal deploy app/modal_whisper.py     # Whisper STT
modal deploy app/modal_llm.py         # LLM Evaluation
modal deploy app/modal_deepface.py    # DeepFace Recognition
```

### 3. Enable in Your App
```bash
export USE_MODAL=true
```

> **Note:** By default `USE_MODAL=false`, so Docker/local uses CPU-based inference. Set `USE_MODAL=true` only when Modal functions are deployed.

---

## Hugging Face Spaces Deployment

The project includes `Dockerfile.hf` optimized for Hugging Face Spaces:

```bash
# Deploy using the HF deploy script
bash scripts/deploy_hf.sh
```

For detailed deployment instructions, see [deployment_guide.md](deployment_guide.md).

---

## Database

The system uses **PostgreSQL** with **SQLModel** (SQLAlchemy) and **Alembic** for migrations.

### Core Models
| Model | Purpose |
|-------|---------|
| `User` | Admin/Candidate accounts with face embeddings |
| `QuestionPaper` | Collection of interview questions per admin |
| `Questions` | Individual questions with type, difficulty, expected answers |
| `InterviewSession` | Scheduled interview with token, time constraints, status |
| `SessionQuestion` | Randomized question subset assigned to a session |
| `InterviewResult` | Aggregated scores and overall evaluation |
| `Answers` | Per-question responses with transcriptions and scores |
| `ProctoringEvent` | Timestamped audit log of proctoring violations |
| `StatusTimeline` | Candidate lifecycle status change history |

### Migrations
```bash
# Auto-generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

---

## Testing

```bash
# Run the full integration test suite
docker compose exec app python -m pytest tests/integration/test_api.py

# Run unit tests
python -m pytest tests/unit/

# Run all tests
python -m pytest
```

See [docs/API_TESTING_GUIDE.md](docs/API_TESTING_GUIDE.md) for detailed API testing instructions.

---

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `scripts/create_super_admin.py` | Create a super admin user |
| `scripts/seed_users.py` | Seed sample admin/candidate users |
| `scripts/seed_questions.py` | Seed sample question papers |
| `scripts/seed_dummy_data.py` | Seed comprehensive dummy data |
| `scripts/generate_cert.py` | Generate self-signed SSL certificates |
| `scripts/migrate.py` | Run Alembic database migrations |
| `scripts/reset_db.py` | Reset the database (destructive) |
| `scripts/health_check.py` | Check backend health status |
| `scripts/deploy_hf.sh` | Deploy to Hugging Face Spaces |

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | FastAPI, Uvicorn, SQLModel, Alembic, PostgreSQL |
| **AI/ML** | DeepFace, MediaPipe, Faster-Whisper, SpeechBrain, LangChain + Ollama |
| **Task Queue** | Celery, Redis |
| **Frontend** | React, Vite, ESLint |
| **Deployment** | Docker, Docker Compose, Hugging Face Spaces, Ngrok |
| **Cloud GPU** | Modal (Whisper, LLM, DeepFace) |
| **Monitoring** | Sentry, structured logging |
| **Email** | SMTP, SendGrid |

---

## License

Proprietary & Confidential.
