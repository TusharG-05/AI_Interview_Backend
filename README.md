# AI Interview Platform

A FastAPI-based application for practicing technical interviews with AI-powered questions and evaluation.

## Features

- **General Questions**: Practice common coding interview questions.
- **Resume-Based Questions**: Upload your resume to get tailored questions.
- **AI Evaluation**: Immediate feedback on your answers using a local LLM.
- **Admin Dashboard**: Manage questions and viewing sessions.

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL (via SQLModel)
- **AI**: LangChain + Local LLM (Ollama recommended)
- **Containerization**: Docker & Docker Compose

## Getting Started

### Prerequisites

- Python 3.11 (Required for dependencies)
- PostgreSQL
- Ollama (running locally)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd AI_Interview_Fastapi
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   .\.venv311\Scripts\Activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_interview_db
   SECRET_KEY=your_secret_key
   ```

5. **Initialize Database**
   ```bash
   python scripts/create_db.py
   ```

6. **Run Application**
   ```bash
   uvicorn main:app --reload
   ```
   Visit `http://localhost:8000`

### Docker Setup

Run the entire stack with one command:

```bash
docker compose up --build
```
The API will be available at `http://localhost:8000`.

## API Documentation

Once running, access the interactive API docs at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Project Structure

- `auth/`: Authentication logic
- `config/`: Configuration settings and DB connection
- `models/`: Database models
- `prompts/`: LangChain prompts
- `routes/`: API endpoints
- `schemas/`: Pydantic data schemas
- `services/`: Business logic
- `static/`: CSS and assets
- `templates/`: HTML templates
