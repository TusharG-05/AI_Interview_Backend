# Face/Gaze AI Interview Platform - Setup & Configuration

This guide details the complete configuration for the application environment.

## 1. Environment Configuration (.env)

Ensure your `.env` file contains the following keys. 

> **SECURITY WARNING**: This file contains sensitive credentials (`SECRET_KEY`, `MAIL_PASSWORD`, `NGROK_AUTHTOKEN`). Never commit it to version control.

### Core Settings
```ini
ENV=production
APP_BASE_URL=http://localhost:8000
SECRET_KEY=<your-secure-random-key>
```
*   `SECRET_KEY`: Used for JWT token generation. Change this in production.

### Database (PostgreSQL)
The application uses PostgreSQL 15.
```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=interview_db

# Host Connection (for local scripts/alembic outside docker)
DATABASE_URL=postgresql://postgres:<url-encoded-password>@localhost:5432/interview_db

# Internal Docker Connection (for the app container)
DOCKER_DATABASE_URL=postgresql://postgres:<url-encoded-password>@db:5432/interview_db
```
*   **Note**: If your password contains special characters (e.g., `#`), ensure they are URL-encoded in the connection strings (e.g., `Tush#4184` -> `Tush%234184`).

### AI & LLM (Ollama)
```ini
LLM_MODEL=qwen2.5-coder:3b
OLLAMA_BASE_URL=http://localhost:11434
```
*   `OLLAMA_BASE_URL`: Where your local Ollama instance is running. Docker connects to the host via `http://host.docker.internal:11434` (configured in `docker-compose.yml`, mapped from this var).

### Email Service (SMTP)
Currently configured for Gmail SMTP.
```ini
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```
*   **Gmail**: Use an App Password if 2FA is enabled.

### Remote Access (Ngrok)
Exposes the local server for external interview access tests.
```ini
NGROK_AUTHTOKEN=<your-ngrok-token>
```

## 2. Docker Deployment

### Prerequisites
- Docker & Docker Compose installed.
- Ollama running locally (`ollama serve`).

### Start Application
```bash
# Build and start services
docker compose up -d --build

# View logs
docker compose logs -f app
```

### Database Management
Migrations are managed via Alembic.

```bash
# Apply migrations (inside container)
docker compose exec app alembic upgrade head

# Reset Database (Caution: Deletes all data)
docker compose down -v
docker compose up -d
```

## 3. First-Time Setup (Bootstrap)

The first user registered in the system automatically becomes the **Super Admin**.

1.  **Ensure Database is Empty** (or just initialized).
2.  **Register Super Admin**:
    ```bash
    curl -X POST "http://localhost:8000/api/auth/register" \
         -H "Content-Type: application/json" \
         -d '{"email": "admin@test.com", "password": "securepassword", "full_name": "Super Admin", "role": "super_admin"}'
    ```
    *or use the provided `register_admin.py` script.*

## 4. Verification

Run the unified integration test to verify the entire stack:
```bash
# Assumes python venv is active locally
python tests/integration/test_unified_flow.py
```
