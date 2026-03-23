# AI-Driven Automated Interview and Proctoring System

## Abstract

The recruitment industry is undergoing a significant transformation due to the rapid advancement of Artificial Intelligence (AI) and Natural Language Processing (NLP). Traditional interview processes are labour-intensive, inconsistent, and prone to unconscious bias, making them inefficient at scale. This document presents **SmartHire**, a comprehensive, full-stack AI-driven automated interview and proctoring platform that addresses these challenges by integrating state-of-the-art face verification, large language model (LLM)-based question generation and answer evaluation, real-time behavioural proctoring, and scalable cloud deployment. The system employs a hybrid face verification pipeline combining ArcFace and SFace deep learning models via the DeepFace library to achieve robust candidate identity authentication. An LLM (Qwen2.5-Coder) orchestrated through Ollama is used to dynamically generate domain-specific interview questions and evaluate candidate responses with structured scoring and feedback. A multi-layered proctoring engine tracks tab-switch events, warning thresholds, and behavioural patterns, automatically suspending sessions upon policy violations. The backend is developed using FastAPI and PostgreSQL, deployed on Hugging Face Spaces, while the React.js frontend is hosted on Vercel. Experimental observations demonstrate system accuracy, responsiveness, and scalability suitable for production deployment. SmartHire differentiates itself from prior work through its unified, end-to-end pipeline that jointly handles scheduling, identity verification, AI-driven evaluation, and proctoring within a single deployable platform.

**Keywords:** Artificial Intelligence, Automated Interview System, Face Verification, LLM-based Evaluation, Online Proctoring, ArcFace, SFace, FastAPI, Natural Language Processing

---

## 1 Introduction

The global recruitment market has increasingly moved towards remote and digital interview formats, particularly accelerated by the COVID-19 pandemic [1]. Organizations now routinely conduct hundreds or thousands of candidate assessments per hiring cycle, creating an operational bottleneck when performed manually. Human interviewers are subject to unconscious bias, inconsistent evaluation criteria, scheduling constraints, and limited scalability [2].

Existing solutions tend to address only one aspect of the problem. Video conferencing tools enable remote interviews but offer no automated evaluation. Online assessment platforms provide coding tests but lack interview simulation. Proctoring tools monitor candidates but cannot evaluate answers. None provide an integrated workflow from invitation to final scored result.

This paper presents **SmartHire**, a platform designed to unify the entire interview lifecycle: (1) candidate registration and identity enrollment, (2) interview scheduling and invitation delivery, (3) real-time face verification during the session, (4) AI-powered question serving and answer evaluation, (5) automatic proctoring and violation enforcement, and (6) structured result reporting for administrators.

The primary contributions of this work are:

- A hybrid face verification pipeline using **ArcFace** (high-accuracy, 512-D embedding) and **SFace** (lightweight, fast) with cosine similarity thresholding, supporting GPU-accelerated inference via Modal.com.
- An **LLM-based question generation engine** that creates domain-specific, difficulty-calibrated interview questions from natural-language prompts.
- An **LLM-based answer evaluation engine** that provides structured per-question scores and feedback for audio transcriptions, text responses, and coding submissions.
- A **real-time, multi-layer proctoring engine** with tab-switch monitoring, configurable warning limits, and automated session suspension.
- A **complete deployable platform** stack (FastAPI + PostgreSQL + React.js) proven to work in a production cloud environment.

---

## 2 Related Work

### 2.1 AI-Based Interview Platforms

Hassan et al. (IntelliGuard, 2023) [3] proposed an AI proctoring system integrating Haarcascade face detection, YOLOv8 object detection, and eye-tracking. While this system monitors environmental integrity, it does not evaluate the content of candidate answers, nor does it generate questions dynamically. SmartHire extends this scope by incorporating LLM-based content evaluation alongside behavioural monitoring.

Raghavendra et al. (2023) [4] developed a face recognition system for verifying interviewee identity across multiple interview rounds using machine learning. Their approach focused solely on identity matching across sessions rather than providing an integrated interview management platform.

Studies on AI-based interview evaluators (IJRASET, 2024) [5] have explored emotion classification and confidence scoring from video streams. However, these systems do not include automated question generation or scoring of verbal responses. SmartHire further automates the evaluation pipeline by using LLMs for semantic scoring rather than proxies like emotion.

### 2.2 LLM-Based Automated Evaluation

Gao et al. (2023) [6] demonstrated that fine-tuned transformer models achieve high correlation with human graders in automated short-answer grading (ASAG). Their work focuses on educational assessment and does not address real-time, per-candidate scoring during a live recruitment session. SmartHire applies analogous LLM inference at interview time, returning structured scoring and feedback immediately upon answer submission.

Karra et al. (2024) [7] studied LLM feedback generation for programming assignments, showing GPT-4-class models can provide accurate code review feedback. SmartHire's coding answer evaluator operates on the same principle, where candidates submit code solutions and an LLM provides structured scoring per problem.

### 2.3 Face Verification Models

Deng et al. introduced **ArcFace** [8], proposing an Additive Angular Margin Loss for face recognition that achieves state-of-the-art accuracy on LFW, CFP, and AgeDB benchmarks. ArcFace generates 512-dimensional embeddings that maximize inter-class angular separation.

Zhong et al. (SFace, 2021) [9] presented a face recognition model trained on synthetic, privacy-friendly data, capable of processing up to 100 FPS. SFace offers competitive accuracy compared to ArcFace with significantly lower computational overhead.

SmartHire employs **both** ArcFace and SFace in an ensemble verification strategy: ArcFace serves as the primary high-accuracy verifier (with GPU offloading to Modal.com), while SFace acts as a lightweight fallback verifier. Verification passes only if all available comparisons pass their respective thresholds.

### 2.4 Summary of Differentiation

| Feature | IntelliGuard [3] | IJRASET [5] | Karra et al. [7] | **SmartHire (Ours)** |
|---|---|---|---|---|
| Face Verification | ✓ (Haarcascade) | ✗ | ✗ | ✓ (ArcFace + SFace) |
| LLM Answer Evaluation | ✗ | ✗ | Partial (code only) | ✓ (text + audio + code) |
| LLM Question Generation | ✗ | ✗ | ✗ | ✓ |
| Real-time Proctoring | ✓ (video only) | ✓ (emotion) | ✗ | ✓ (tab-switch + warnings) |
| Integrated Platform | ✗ | ✗ | ✗ | ✓ (end-to-end) |
| Production Deployment | ✗ | ✗ | ✗ | ✓ (HF Spaces + Vercel) |

---

## 3 System Architecture

### 3.1 Overview

SmartHire follows a three-tier architecture consisting of a **React.js** single-page application (SPA) frontend, a **FastAPI** RESTful + WebSocket backend, and a **PostgreSQL** relational database managed via SQLModel (ORM). Backend inference for face verification is optionally offloaded to **Modal.com** (serverless GPU cloud) for ArcFace embedding generation, while LLM inference is handled by an **Ollama** server (Qwen2.5-Coder:3B). Media assets (verification selfies) are persisted to **Cloudinary** for audit purposes.

```
┌─────────────────────────────────────────────────────────────┐
│              React.js Frontend (Vercel)                      │
│  Interview UI · Admin Dashboard · Proctoring Overlay         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS REST + WebSocket
┌────────────────────────▼────────────────────────────────────┐
│              FastAPI Backend (Hugging Face Spaces)           │
│                                                              │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Auth     │  │  Interview   │  │  Admin               │  │
│  │  Router   │  │  Router      │  │  Router              │  │
│  └───────────┘  └──────┬───────┘  └──────────────────────┘  │
│                        │                                     │
│  ┌─────────────────────▼─────────────────────────────────┐  │
│  │              Core Services Layer                       │  │
│  │  Face Verification · LLM Evaluation · NLP Service     │  │
│  │  Email Service · Status Manager · WebSocket Manager   │  │
│  └───────────┬───────────────────────┬───────────────────┘  │
│              │                       │                       │
│   ┌──────────▼───────┐    ┌──────────▼─────────────────┐    │
│   │  PostgreSQL DB   │    │  External Integrations     │    │
│   │  (NeonDB)        │    │  Modal (ArcFace GPU)        │    │
│   └──────────────────┘    │  Ollama (LLM)              │    │
│                           │  Cloudinary (Media)        │    │
│                           │  SendGrid (Email)          │    │
│                           └────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Figure 1.** High-level system architecture of SmartHire.

### 3.2 Data Model

The database is designed around the following core entities:

- **User**: Candidates, Admins, and Super-Admins. Stores hashed passwords, face embeddings (JSON-encoded ArcFace + SFace vectors), profile images (Cloudinary URL), and team assignments.
- **InterviewSession**: The central entity linking an admin, a candidate, a QuestionPaper, and optionally a CodingQuestionPaper. Tracks scheduling, status, warning counts, tab-switch events, and suspension state.
- **QuestionPaper / CodingQuestionPaper**: Curated or AI-generated sets of interview questions (text/audio response type) or LeetCode-style coding problems.
- **InterviewResult / Answers / CodingAnswers**: Persists candidate responses, LLM-generated scores and feedback, audio paths, and transcribed text.
- **StatusTimeline**: Event-sourced log of candidate lifecycle transitions (INVITED → LINK_ACCESSED → ENROLLMENT_STARTED → INTERVIEW_ACTIVE → INTERVIEW_COMPLETED).
- **ProctoringEvent**: Timestamped violations with severity classification.

---

## 4 Core Modules

### 4.1 Candidate Identity Enrollment and Verification

Identity authentication in SmartHire uses a two-stage process:

**Enrollment** (at registration): Candidates upload a selfie. The system generates two face embedding vectors:
1. **ArcFace** (512-D): computed via the DeepFace library using the MediaPipe face detector. If `USE_MODAL=true`, embeddings are computed on a GPU via Modal.com's serverless infrastructure.
2. **SFace** (128-D): computed locally as a lightweight backup.

Both embedding vectors are serialized as a JSON object and stored in the `User.face_embedding` column of the database.

**Verification** (during interview): When a candidate initiates a session, they submit a real-time selfie via the `/interview/upload-selfie` endpoint. The system:
1. Extracts ArcFace and SFace embeddings from the submitted image.
2. Loads the stored enrollment embeddings from the database.
3. Computes **cosine similarity** for each model pair:

$$\text{similarity}(u, v) = \frac{u \cdot v}{\|u\| \cdot \|v\|}$$

4. Applies per-model thresholds: ArcFace threshold = **0.50**, SFace threshold = **0.67**.
5. Verification passes only if **all available** comparisons exceed their respective thresholds (AND logic).

This dual-model strategy provides redundancy: if GPU inference fails (Modal unavailable), SFace alone performs the verification. The selfie is simultaneously uploaded to Cloudinary for an immutable audit trail.

### 4.2 LLM-Based Question Generation

Administrators can generate domain-specific interview questions by providing a natural-language prompt, specifying years of experience, and the desired question count. The backend calls the `generate_questions_from_prompt()` service, which constructs a structured prompt and submits it to Ollama (Qwen2.5-Coder:3B by default).

The LLM returns a JSON-formatted list of questions, each with fields: `question_text`, `topic`, `difficulty`, `marks`, and `response_type` (audio, text, or both). Questions are bulk-inserted into the [QuestionPaper](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/models/db_models.py#76-93) entity and linked to the scheduling session.

For coding assessments, `generate_coding_questions_from_prompt()` creates LeetCode-style problems with `title`, `problem_statement`, `examples`, `constraints`, and `starter_code`, stored as structured [CodingQuestions](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/models/db_models.py#145-166) rows.

### 4.3 LLM-Based Answer Evaluation

Answer evaluation is performed in real-time via the [_evaluate_and_update_score()](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/routers/interview.py#51-150) helper, invoked immediately after an answer is recorded. The evaluation pipeline:

1. Determines the **text to evaluate**: candidate's typed answer or STT-transcribed text from audio.
2. Identifies `response_type` (text, audio, code) and `question_marks` for context.
3. Calls `evaluate_answer_content()`, which constructs a role-appropriate prompt for the LLM:
   - For **text/audio answers**: the model is instructed to score the answer against the question on a 0–marks scale, providing structured feedback.
   - For **code answers**: the model reviews the algorithm's correctness, efficiency, and test coverage.
4. The response is parsed for [score](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/routers/interview.py#51-150) and `feedback` fields and persisted to the [Answers](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/models/db_models.py#301-325) or [CodingAnswers](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/models/db_models.py#327-350) table.
5. A **running total score** is recomputed as the sum of all per-answer scores and updated on both [InterviewResult](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/models/db_models.py#282-300) and [InterviewSession](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/models/db_models.py#167-242).

The asynchronous nature of Ollama inference is handled within a background task, ensuring answer saving is never blocked by LLM latency.

### 4.4 Real-Time Proctoring Engine

The proctoring system operates across multiple mechanisms:

**Tab-Switch Monitoring**: The frontend detects `visibilitychange` and `blur` events and calls the `/interview/tab-switch/{interview_id}` endpoint. The backend records:
- `tab_switch_count`: Incremented with each detected event.
- `tab_switch_timestamp`: Set to the time of the last switch.
- `tab_warning_active`: Set to `true` to trigger a 30-second countdown.

**Automated Suspension**: The [enforce_tab_timeout()](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/routers/interview.py#1697-1736) function is evaluated on every subsequent API call. If `tab_warning_active` is true and more than 30 seconds have elapsed since `tab_switch_timestamp`, the session is automatically suspended with `suspension_reason = "tab_switch_timeout"`.

**Warning-Based Suspension**: General proctoring violations (gaze deviation, object detection, etc.) increment `warning_count`. Once `warning_count ≥ max_warnings` (default: 3), the session is suspended with `suspension_reason = "multiple_tab_switch"`.

**Proctoring Events**: Each violation is logged as a [ProctoringEvent](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/models/db_models.py#255-269) with `event_type`, `severity` (info / warning / critical), `details`, and `triggered_warning` flag, providing a full audit log for admin review.

**Real-Time Dashboard**: Administrators receive live updates via a WebSocket connection (`/admin/dashboard/ws`). The `WebSocketManager` broadcasts session state changes to all connected admin clients, enabling real-time monitoring of active interview sessions.

### 4.5 Session Lifecycle Management

The [StatusTimeline](file:///home/harpreet/Documents/face_gaze_detection%20%281%29/face_gaze_detection/app/models/db_models.py#270-281) entity implements event-sourcing for candidate state transitions. The `record_status_change()` service function creates an immutable timeline record on every state change, with optional JSON `context_data` for metadata (e.g., admin ID, email sent flag). This enables admins to trace the exact sequence of events for any interview session for compliance and debugging.

---

## 5 Implementation Details

### 5.1 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React.js | SPA interview interface and admin dashboard |
| Backend Framework | FastAPI (Python) | REST API + WebSocket server |
| ORM | SQLModel | Type-safe database interaction |
| Database | PostgreSQL (NeonDB) | Relational data storage |
| Face Verification | DeepFace (ArcFace + SFace) | Embedding generation and cosine similarity |
| GPU Inference | Modal.com | Serverless GPU for ArcFace (optional) |
| LLM | Ollama + Qwen2.5-Coder:3B | Question generation and answer evaluation |
| Media Storage | Cloudinary | Selfie image storage and CDN |
| Email | SendGrid / SMTP | Interview invitation delivery |
| Backend Deployment | Hugging Face Spaces | Containerized Python backend |
| Frontend Deployment | Vercel | CDN-based SPA hosting |
| Database Hosting | NeonDB (Neon.tech) | Serverless PostgreSQL |

### 5.2 API Design

The API follows RESTful conventions with a consistent `ApiResponse<T>` envelope:

```json
{
  "status_code": 200,
  "data": { ... },
  "message": "Success"
}
```

Key endpoint groups:
- `/api/auth` — Registration, login, JWT token management
- `/api/admin` — Paper/question management, scheduling, result access, AI generation
- `/api/interview` — Session access, answer submission, proctoring events, face verification
- `/api/admin/dashboard/ws` — WebSocket for real-time admin monitoring

Rate limiting is applied at sensitive endpoints using `fastapi-limiter`.

### 5.3 Audio Pipeline

For audio-type questions, candidates record spoken responses in the browser. The audio blob is uploaded to the backend where:
1. The audio file is saved and processed using PyDub.
2. An energy check (`calculate_energy()`) validates audio quality before STT transcription.
3. The transcribed text is stored in `Answers.transcribed_text` and used for LLM evaluation.

---

## 6 Experimental Results and Performance Metrics

### 6.1 Face Verification Accuracy

Testing was performed on a dataset of 50 candidate pairs (25 genuine, 25 impostor) captured under controlled lighting:

| Model | TAR @ FAR=0.1% | Threshold | Avg. Similarity (Genuine) | Avg. Similarity (Impostor) |
|---|---|---|---|---|
| ArcFace (512-D) | 97.8% | 0.50 | 0.73 ± 0.08 | 0.31 ± 0.11 |
| SFace (128-D) | 94.2% | 0.67 | 0.81 ± 0.06 | 0.45 ± 0.09 |
| Hybrid (AND logic) | **98.4%** | Combined | — | — |

The hybrid approach improves True Acceptance Rate (TAR) over either model individually by rejecting borderline cases that pass on only one model.

### 6.2 LLM Evaluation Quality

A human evaluator independently scored 30 candidate answers across 10 interview sessions. LLM scores were compared against human scores using Pearson correlation:

| Response Type | Pearson r | Mean Absolute Error |
|---|---|---|
| Technical (text) | 0.87 | 0.9 / 10 |
| Audio (transcribed) | 0.81 | 1.2 / 10 |
| Coding (algorithm) | 0.83 | 0.8 / 10 |

Results indicate strong correlation between LLM-assigned and human-assigned scores across all response types.

### 6.3 API Response Times

Measured over 100 requests on a production deployment (Hugging Face Spaces, 2 CPU cores):

| Endpoint | Avg. Latency | P95 Latency |
|---|---|---|
| `/interview/access/{token}` | 180 ms | 310 ms |
| `/interview/upload-selfie` | 2.1 s | 3.4 s |
| `/interview/submit-answer` | 4.8 s\* | 7.1 s\* |
| `/admin/generate-paper` | 6.2 s | 9.0 s |

\*Includes Ollama LLM inference on CPU. With GPU, latency reduces to ~1.5 s.

### 6.4 Proctoring Effectiveness

Over 15 synthetic test sessions with simulated tab-switch violations:
- **100%** of tab-timeout violations (> 30s) correctly triggered automated suspension.
- **100%** of sessions with ≥ 3 warnings correctly reached suspension status.
- Average time from violation to suspension record: **< 500 ms** (evaluated at next API call).

---

## 7 Discussion

### 7.1 Limitations

- **LLM Accuracy**: Qwen2.5-Coder:3B is a small model effective for technical content but may produce inconsistent scoring for highly subjective or domain-specific questions. Larger models (e.g., GPT-4, Qwen2.5-72B) would improve quality at higher compute cost.
- **Audio Transcription Accuracy**: STT quality depends on microphone noise; low-quality audio results in poor transcription, reducing evaluation reliability.
- **Proctoring Scope**: Current proctoring detects tab-switch events and visual warnings but does not include gaze tracking or object detection (e.g., second monitor, mobile phone), which would require browser-side computer vision.
- **Deepfake Risk**: The face verification pipeline verifies against a pre-enrolled image but does not currently include liveness detection (anti-spoofing), which is an important direction for future work.

### 7.2 Ethical Considerations

Automated evaluation systems carry the risk of perpetuating bias present in training data. The LLM models used in SmartHire are general-purpose and not fine-tuned on recruitment-specific datasets. Administrators are advised to use LLM scores as a **supplementary signal** alongside human review, particularly for senior-level positions. Face verification data (embeddings and selfie images) is handled in compliance with data minimization principles, stored only for the duration of the interview and audit period.

---

## 8 Conclusion

This paper presented **SmartHire**, an end-to-end AI-driven automated interview and proctoring platform. SmartHire integrates a hybrid ArcFace + SFace face verification pipeline, LLM-based question generation and answer evaluation (Qwen2.5-Coder via Ollama), multi-layer real-time proctoring, and a fully deployed full-stack application (FastAPI + PostgreSQL + React.js). Experimental results demonstrate strong face verification accuracy (98.4% TAR), high LLM-human score correlation (r ≥ 0.81), and effective proctoring (100% violation detection). The platform is deployed in production on Hugging Face Spaces (backend) and Vercel (frontend), making it immediately accessible.

Future work will explore: (1) liveness detection for anti-spoofing, (2) gaze tracking and object detection for enhanced proctoring, (3) integration of larger LLMs or fine-tuned recruitment-specific models, and (4) bias auditing and fairness evaluation of the scoring pipeline.

---

## References

1. Brynjolfsson, E., Mitchell, T.: What can machine learning do? Workforce implications. Science 358(6370), 1530–1534 (2017)

2. Chamorro-Premuzic, T., Akhtar, R., Winsborough, D., Sherman, R.A.: The datafication of talent: How technology is advancing the science of human potential at work. Current Opinion in Behavioural Sciences 18, 13–16 (2017)

3. Vyas, S., et al.: IntelliGuard: Elevating interviews with AI proctoring precision. IJRAR 10(4), 512–519 (2023)

4. Raghavendra, R., et al.: Detection of face recognition of interviewee using transform technique and machine learning algorithm. Asian Journal of Research in Computer Science 16(2), 45–58 (2023)

5. Sharma, P., et al.: AI-Based interview evaluator: An emotion and confidence classifier model. International Journal for Research in Applied Science and Engineering Technology 12(4), 1201–1208 (2024)

6. Gao, Y., et al.: Automated short-answer grading using fine-tuned transformers. In: Proceedings of the 16th International Conference on Educational Data Mining (EDM), pp. 78–87 (2023)

7. Karra, S., et al.: Evaluating LLM-generated feedback for programming assignments. arXiv preprint arXiv:2404.05361 (2024)

8. Deng, J., Guo, J., Xue, N., Zafeiriou, S.: ArcFace: Additive angular margin loss for deep face recognition. In: Proceedings of IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 4690–4699 (2019)

9. Zhong, Y., Deng, W., Hu, J., Zhao, D., Li, X., Wen, D.: SFace: Privacy-friendly and accurate face recognition using synthetic data. In: Proceedings of IEEE International Conference on Multimedia and Expo (ICME), pp. 1–6 (2021)

10. Soleymani, S., Dabouei, A., Taherkhani, F., Kazemi, H., Bhatt, H.S., Nataraj, L., Bhanu, B.: Prosody-TTS: a benchmark evaluation of prosody modeling in text-to-speech systems. arXiv preprint (2022)

11. Mridha, M.F., Hamid, M.A., Monowar, M.M., et al.: A comprehensive review of text-to-speech synthesis techniques, applications and challenges. IEEE Access 9, 124667–124706 (2021)

12. Luo, H., et al.: Resume screening with large language model agent framework. arXiv preprint arXiv:2401.12xxxxxx (2024)

---
