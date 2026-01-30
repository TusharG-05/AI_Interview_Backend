# AI Interview Platform: API Testing Guide

This project is now a **Pure JSON Backend**. All HTML templates have been removed. Use this guide to interact with the API endpoints.

## 0. API Documentation (Swagger)
The easiest way to test is via the built-in Swagger UI:
- **URL**: `https://localhost:8000/docs`
- Here you can see all schemas, parameters, and even execute requests directly.

---

## 1. Authentication APIs

### Register a User
- **Endpoint**: `POST /api/auth/register`
- **Body**:
```json
{
  "email": "candidate@example.com",
  "password": "strongpassword",
  "full_name": "John Doe",
  "role": "candidate"
}
```
- **Response**: Returns JWT `access_token`.

### Login (JSON)
- **Endpoint**: `POST /api/auth/login`
- **Body**:
```json
{
  "email": "admin@example.com",
  "password": "password"
}
```
- **Response**:
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "role": "admin"
}
```

---

## 2. Admin APIs (Requires Admin Token)

### Create an Interview Room
- **Endpoint**: `POST /api/admin/rooms`
- **Headers**: `Authorization: Bearer <ADMIN_TOKEN>`
- **Body**:
```json
{
  "password": "roompassword",
  "max_sessions": 10
}
```

### Add a Question
- **Endpoint**: `POST /api/admin/questions`
- **Body**:
```json
{
  "content": "Explain the difference between a process and a thread.",
  "topic": "OS",
  "difficulty": "Easy",
  "reference_answer": "..."
}
```

### Get All User Results (Dashboard)
- **Endpoint**: `GET /api/admin/users/results`
- **Response**: A detailed list of all interview sessions, scores, and proctoring flags.

---

## 3. Candidate & Interview APIs

### Join a Room
- **Endpoint**: `POST /api/candidate/join`
- **Body**:
```json
{
  "room_code": "ABCDE",
  "password": "roompassword"
}
```

### Upload Verification Selfie
- **Endpoint**: `POST /api/candidate/upload-selfie`
- **Headers**: `Authorization: Bearer <TOKEN>`
- **Body**: `file` (Image File)
- **Response**:
```json
{
  "message": "Selfie uploaded successfully",
  "path": "app/assets/images/profiles/user_1.jpg"
}
```

### Start Interview
- **Endpoint**: `POST /api/interview/start`
- **Body**: `candidate_name` (Form), `enrollment_audio` (File/Blob)

### Get Next Question
- **Endpoint**: `GET /api/interview/next-question/{session_id}`

### Submit Answer (Voice)
- **Endpoint**: `POST /api/interview/submit-answer`
- **Body**: `session_id` (Form), `question_id` (Form), `audio` (File/Blob)

---

## 4. System Status & Proctoring

### Health Check
- **Endpoint**: `GET /api/status/`
- Returns status of LLM (Ollama), Camera, and Database.

### Real-time Proctoring Alerts (WebSocket)
- **Endpoint**: `ws://localhost:8000/api/status/ws`
- Receives JSON messages when security events occur (e.g., `{"warning": "MULTI-FACE DETECTED"}`).
