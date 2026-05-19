# Frontend WebSocket API Reference

This document provides a clean, comprehensive reference of all WebSocket request and response bodies, query parameters, authentication formats, and exact URL routing for both the **Candidate** and **Admin Dashboard** streams.

---

## Overview of WebSocket Endpoints

| Endpoint Stream | Protocol Path | Auth Requirement | Purpose |
|-----------------|---------------|------------------|---------|
| **1. Candidate WS** | `ws://localhost:8000/ws/api/interview/{interview_id}?token={token}` | JWT Query Param | Client-side violations, login, start, and finish |
| **2. Admin Dashboard WS** | `ws://localhost:8000/api/admin/dashboard/ws?token={token}` | JWT Query Param / Cookie | Real-time monitoring across all active interviews |

*Note: Replace `ws://` with `wss://` in production secure environments.*

---

## 1. Candidate WebSocket (`/ws/api/interview/{interview_id}`)

### 📥 Client → Server (Requests / Triggers)

#### **Candidate Login**
Sent immediately after establishing a WebSocket connection to identify the candidate.
```json
{
    "type": "login",
    "email": "candidate@example.com"
}
```

#### **Start / Resume Interview**
Sent when the candidate starts the interview or resumes after a disconnection. This transitions the interview session to a `LIVE` state in the database.
```json
{
    "type": "start_interview",
    "interview_id": 62
}
```
#### **Proctoring Violation (Client-Side Detection)**
Sent by the frontend if on-device AI/ML models (e.g. MediaPipe or face-api.js) detect facial, gaze, tab-switch, or tab-return violations.

For `tab-switch` and `tab-return`, the server manages warning accumulation and a **30-second grace window** validation before session termination.
```json
{
    "event_type": "violation_detected",
    "violation_type": "no_face", // Acceptable: "no_face", "multiple_faces", "gaze_away", "unauthorized_person", "tab-switch", "tab-return"
    "details": "No face detected in video feed" // Human-readable description
}
```

#### **Finish Interview**
Sent when the candidate manually finishes the interview.
```json
{
    "type": "finish_interview",
    "interview_id": 62
}
```

---

### 📤 Server → Client (Responses / Confirmations)

#### **Violation Detected** (Real-time warning flat format)
Sent instantly to warn the candidate whenever a soft or hard violation accumulates.
```json
{
    "event_type": "violation_detected",
    "interview_id": 62,
    "violation_type": "tab_switch", // Possible: "tab_switch", "multiple_faces", "no_face", "wrong_candidate"
    "details": "Tab switch detected (Attempt 1)",
    "warning_count": 1,
    "max_warnings": 3,
    "timestamp": "2026-05-19T05:03:35.123Z"
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

## 2. Admin Dashboard WebSocket (`/api/admin/dashboard/ws`)

The Admin dashboard feed uses a **Standardized Enriched Format** where nested `proctoring_events` include complete count thresholds, and `dashboard_data` holds aggregated daily state.

### 📤 Server → Client (Enriched Events)

#### **Standard Payload Format Template**
```json
{
    "event_type": "EVENT_NAME",
    "data": {
        "interview_id": 62,
        "interview_status": "LIVE", // Possible: CONNECTED, LIVE, DISCONNECTED, COMPLETED, EXPIRED
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
            "live": 1,
            "proctoring_activity": "5.00%", // Percentage string of sessions with violations today
            "failed_today": 0,
            "passed_today": 0
        },
        "timestamp": "2026-05-19T05:03:35.123Z",
        
        // ... Event Specific Payload Fields (Listed Below) ...
        "started_at": "2026-05-19T05:03:35.123Z",
        "violation_type": "tab_switch",
        "details": "Tab switch detected (Attempt 1)"
    }
}
```

#### **Event Types & Specific Fields**

| `event_type` | Trigger Condition | Extra Fields in `data` |
|--------------|-------------------|------------------------|
| `candidate_connected` | Candidate WebSocket establishes connection | `timestamp` |
| `candidate_logged_in` | Candidate client successfully sends `login` event | `timestamp` |
| `interview_started` | Candidate sends `start_interview` and state goes LIVE | `started_at` |
| `violation_detected` | Proctoring violation is added | `violation_type`, `details`, `timestamp` |
| `interview_suspended` | Candidate is auto-suspended (warnings threshold exceeded) | `reason`, `warning_count`, `max_warnings`, `last_violation`, `suspension_metadata: { auto_suspended: bool, suspended_at: datetime }` |
| `interview_completed` | Candidate manually finishes or is completed | `result_status` (Pass/Fail), `completed_at` |
| `interview_expired` | Session timer exceeds limit | `expired_at` |
| `candidate_disconnected` | Candidate WebSocket loses connection | `timestamp` |
