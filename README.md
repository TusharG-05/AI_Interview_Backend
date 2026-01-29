# AI Interview Platform

A FastAPI-based application for practicing technical interviews with AI-powered questions and evaluation.

## Features

- **General Questions**: Practice common coding interview questions.
- **Resume-Based Questions**: Upload your resume to get tailored questions.
- **Real-time AI Evaluation**: Immediate feedback on your answers using a local LLM.
- **Webcam Interface**: See yourself during the interview (Client-side, private).
- **Admin Dashboard**: Manage interview rooms, view candidate history, and scores.

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL (via SQLModel)
- **AI**: LangChain + Local LLM (Ollama recommended)
- **Frontend**: HTML/JS with client-side Media APIs
- **Containerization**: Docker & Docker Compose

## Prerequisites

- **Ollama**: [Download Here](https://ollama.com/)
    - Run `ollama serve`
    - Pull the model: `ollama pull qwen2.5-coder:3b` (or update `config/settings.py`)

## Quick Start (Docker) - Recommended

This is the easiest way to run the app on any machine.

1.  **Start the App**
    ```bash
    docker compose up --build
    ```
    *Note: The first build may take time as it installs heavy AI dependencies.*

2.  **Access the Platform**
    - **Candidate Interface**: `http://localhost:8000`
    - **Admin Dashboard**: `http://localhost:8000/admin/dashboard`
    - **API Docs**: `http://localhost:8000/docs`

3.  **Troubleshooting Docker**
    - Ensure Ollama is running on your host machine.
    - If you are on a slow connection, the build might pause on "Installing dependencies". Be patient.

## Local Development Setup

If you prefer to run it without Docker:

1.  **Clone & Setup Environment**
    ```bash
    git clone <repo-url>
    cd AI_Interview_Fastapi
    python -m venv .venv
    .\.venv\Scripts\Activate
    ```

2.  **Install Dependencies**
    ```bash
    # Note: Requires system FFmpeg installed for audio processing
    pip install -r requirements.txt
    ```

3.  **Configure Database**
    - Create a `.env` file from the example below.
    - Run migrations/setup script:
    ```bash
    python scripts/create_db.py
    ```

4.  **Run Application**
    ```bash
    uvicorn main:app --reload
    ```

## Environment Configuration (.env)

| Variable | Default (Docker) | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://postgres:password@db:5432/ai_interview_db` | Connection string for PostgreSQL |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | URL for the Ollama instance |
| `SECRET_KEY` | `your_secret_key` | Secret for JWT Tokens |

## Project Structure

- `auth/`: Authentication logic (JWT, Password hashing)
- `routes/`: API endpoints (Interview, Admin, Auth)
- `services/`: Business logic (LLM chains, Audio processing)
- `models/`: Database models (SQLModel)
- `templates/`: Jinja2 HTML templates
- `static/`: CSS and Assets
