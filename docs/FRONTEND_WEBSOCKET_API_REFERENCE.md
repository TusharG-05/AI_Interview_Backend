# Frontend WebSocket API Reference

This document provides a clean, comprehensive reference of all WebSocket request and response bodies, query parameters, authentication formats, and exact URL routing for the **Candidate** and **Admin Dashboard** real-time streams.

---

## 🏗️ Overview of WebSocket Streams

The system orchestrates **two distinct WebSocket streams** to handle real-time candidate actions, proctoring events, and admin monitoring.

| Stream Endpoint | Protocol Path | Auth Requirement | Transport Format | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **1. Candidate Event Stream** | `ws://localhost:8000/ws/api/interview/{id}?token={token}` | JWT Query or Cookie | JSON Text | Login, start/resume, client-side violations, and finish. |
| **2. Global Admin Stream** | `ws://localhost:8000/api/admin/dashboard/ws?token={token}` | JWT Query or Cookie | JSON Text | Aggregated real-time monitoring across all active interviews. |

> [!NOTE]
> Replace `ws://` with `wss://` in production secure environments to enforce SSL/TLS encryption.

---

## 🔐 Authentication & Handshake Policy

All WebSocket connections undergo instant JWT validation before connection acceptance. 

1.  **Token Extraction Order**:
    *   **Priority 1**: Query parameter `token` (e.g., `/ws?token=eyJhbGci...`)
    *   **Priority 2**: `access_token` Cookie parsed from the connection headers.
2.  **Handshake Rejection Codes**:
    *   `1008 Policy Violation`: Missing or invalid token.
    *   `4003 Forbidden`: Authenticated candidate attempting to stream/access another candidate's session ID.
    *   `1011 Server Error`: Internal state or connection failures.

---

## 👥 1. Candidate Event Stream (`/ws/api/interview/{interview_id}`)

Binds the candidate to the active interview session, processing status transitions and client-side warnings.

### 📥 Client → Server (Requests)

#### **Candidate Login**
Sent immediately after establishing the WebSocket connection to identify and register the candidate session.
```json
{
    "type": "login",
    "email": "candidate@example.com"
}
```

#### **Start / Resume Interview**
Sent when the candidate clicks the "Start Interview" button or recovers from a connection drop. This sets the database state to `LIVE` and registers the candidate's `start_time`.
```json
{
    "type": "start_interview",
    "interview_id": 62
}
```

#### **Proctoring Violation (Client-Side Detection)**
Sent by the frontend if on-device model libraries (e.g. MediaPipe or face-api.js) detect structural cheating attempts.
```json
{
    "event_type": "violation_messages",
    "violation_type": "no_face",
    "details": "No face detected in webcam feed"
}
```

Accepted `violation_type` values for this message are `no_face`, `multiple_faces`, `gaze_away`, and `unauthorized_person`.

#### **Tab Switch / Tab Return**
Use the same envelope shape for tab visibility changes.
```json
{
    "event_type": "violation_messages",
    "violation_type": "tab_switch",
    "details": "Candidate switched tabs"
}
```

```json
{
    "event_type": "violation_messages",
    "violation_type": "tab_return",
    "details": "Candidate returned to the interview tab"
}
```

The server acknowledges `tab_return` with the same envelope shape and keeps the websocket open.

> [!IMPORTANT]
> **Tab Switch Grace Period**: When `violation_type` is `tab_switch`, a stateful warning is registered. If the candidate does not return (i.e. send `tab_return`) within a **30-second grace window**, the server automatically terminates and suspends the session.

#### **Finish Interview**
Sent when the candidate manually completes the questionnaire. Triggers background evaluation.
```json
{
    "type": "finish_interview",
    "interview_id": 62
}
```

---

### 📤 Server → Client (Confirmations / Notifications)

#### **Violation Acknowledged (Warning Alert)**
Sent back to warn the candidate whenever a violation registers. It indicates how close they are to suspension.
```json
{
    "violation_type": "no_face",
    "interview_id": 62,
    "timestamp": "2026-05-19T05:03:35.123Z",
    "details": "No face detected in webcam feed",
    "warning_count": 1,
    "max_warnings": 3
}
```

#### **Start Confirmation**
```json
{
    "type": "start_interview_confirmation",
    "status": "success"
}
```

#### **Finish Confirmation**
```json
{
    "type": "interview_finished_confirmation",
    "status": "success",
    "message": "Interview finished. Results are being processed."
}
```

---

## 🌍 2. Global Admin Stream (`/api/admin/dashboard/ws`)

Enables real-time monitoring across **all active interview sessions**. It utilizes a **Standardized Enriched Format** containing `proctoring_events` counters and day-aggregated aggregate `dashboard_data`.

### 📤 Server → Client (Enriched Event Broadcaster)

#### **Standard Enriched Payload Schema**
```json
{
    "event_type": "EVENT_NAME",
    "data": {
        "interview_id": 62,
        "interview_status": "LIVE", // CONNECTED, LIVE, DISCONNECTED, COMPLETED, EXPIRED
        "candidate": {
            "candidate_id": 123,
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com"
        },
        "proctoring_events": {
            "tab_switch_count": 1,
            "warning_count": 1,
            "max_warnings": 3
        },
        "dashboard_data": {
            "live": 2,                     // Total active interviews currently running
            "proctoring_activity": "5.00%", // Daily percentage of interviews with violations
            "failed_today": 0,
            "passed_today": 1
        },
        "timestamp": "2026-05-19T05:03:35.123Z",
        
        // ... Event Specific Payload Fields (Dynamically Appended Below) ...
        "started_at": "2026-05-19T05:03:35.123Z",
        "violation_type": "tab_switch",
        "details": "Tab switch detected (Attempt 1)"
    }
}
```

#### **Trigger Event Scenarios & Dynamic Fields**

The backend appends specific attributes to the `data` block based on the type of event:

| `event_type` | Trigger Scenario | Dynamic Fields Appended to `data` |
| :--- | :--- | :--- |
| **`candidate_connected`** | Candidate event stream handshake completes. | `timestamp` |
| **`candidate_logged_in`** | Candidate client successfully sends `login` event. | `timestamp` |
| **`interview_started`** | Candidate sends `start_interview` and session goes LIVE. | `started_at` |
| **`violation_detected`** | A soft or hard proctoring violation is saved. | `violation_type`, `details`, `timestamp` |
| **`interview_suspended`** | Candidate warnings exceed threshold (session terminated). | `reason`, `warning_count`, `max_warnings`, `last_violation`, `suspension_metadata: { auto_suspended: true, suspended_at: datetime }` |
| **`interview_completed`** | Candidate manually completes interview or finishes. | `result_status` (Pass/Fail), `completed_at` |
| **`interview_expired`** | Session scheduler time windows expire. | `expired_at` |
| **`candidate_disconnected`**| Candidate closes/drops WebSocket connection. | `timestamp` |

---

## ⚠️ Proctoring Violation Classifications

When presenting or integrating the proctoring stream, keep in mind how the backend classifies and reacts to different incoming violation types:

| Violation Code | Default Severity | Action Taken |
| :--- | :--- | :--- |
| **`tab_switch`** | `warning` | Increments session `warning_count`. Triggers auto-suspension if threshold reached. |
| **`MULTIPLE FACES DETECTED`** | `warning` | Increments session `warning_count`. Triggers auto-suspension if threshold reached. |
| **`NO FACE DETECTED`** | `info` | Logs event in proctoring audit trail. Does NOT increment warnings. |
| **`SECURITY ALERT: UNAUTHORIZED PERSON`**| `info` | Logs event in proctoring audit trail (Face mismatch). |
| **`gaze_away`** | `warning` | Increments session `warning_count` (Looks away from screen). |
| **`low_audio`** | `info` | Logs microphone state warning. |
