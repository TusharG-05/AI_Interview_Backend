# API Documentation for Frontend Developers

Base URL: `http://localhost:8000`

## 1. Authentication
**Base Path**: `/`

| Method | Endpoint | Request Body (JSON) | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/login` | `{"email": "...", "password": "..."}` | JSON Login. Returns `access_token`. |
| `POST` | `/token` | `form-data: username, password` | **Legacy/Swagger**. Form-based login. |
| `POST` | `/register` | `{"email": "...", "password": "...", "full_name": "...", "role": "..."}` | Register a new user (`candidate` or `admin`). |

---

## 2. Admin Dashboard
**Base Path**: `/admin`
*Requires `Authorization: Bearer <token>` (Admin Role)*

| Method | Endpoint | Request Body (JSON) | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/rooms` | - | List all interview rooms. |
| `POST` | `/rooms` | `{"password": "...", "max_sessions": 30}` | Create a new interview room. |
| `PUT` | `/rooms/{id}` | `{"is_active": true, "max_sessions": ...}` | Update room settings. |
| `DELETE` | `/rooms/{id}` | - | Delete a room. |
| `GET` | `/history` | - | View all interview history (all candidates). |

---

## 3. Candidate Dashboard
**Base Path**: `/candidate`
*Requires `Authorization: Bearer <token>` (Candidate Role)*

| Method | Endpoint | Request Body (JSON) | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/join` | `{"room_code": "...", "password": "..."}` | Join a room. Returns `session_id`. |
| `GET` | `/history` | - | View my past interviews. |

---

## 4. Interview Process
**Base Path**: `/interview`
*Requires `Authorization: Bearer <token>`*

### Setup & Context
| Method | Endpoint | Request/Body | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/process-resume` | `multipart/form-data`: `resume` (PDF) | Extract text from resume PDF. |
| `GET` | `/general-questions` | - | Fetch static/general coding questions. |

### Question Generation
| Method | Endpoint | Request Body (JSON) | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/generate-resume-question` | `{"context": "...", "resume_text": "..."}` | Generate dynamic question based on resume. |

### Answering
| Method | Endpoint | Request Body (JSON) | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/evaluate-answer?session_id={id}` | `{"question": "...", "answer": "..."}` | Submit text answer. Returns feedback & score. |
| `POST` | `/submit-audio` | `multipart/form-data`: `audio` (wav), `session_id`, `question` | Submit audio answer. Returns transcription & feedback. |
| `POST` | `/finish?session_id={id}` | - | End interview and calculate total score. |



---

## 5. Video Service
**Base Path**: `/video`

| Method | Endpoint | Type | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/video_feed` | Stream (MJPEG) | **(Optional)** Server-side processed video feed. Ideally use client-side `navigator.mediaDevices` for performance. |
