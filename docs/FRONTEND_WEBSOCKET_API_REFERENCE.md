# Frontend WebSocket API Reference

This document provides a clean reference of all WebSocket request and response bodies for both the **Candidate** and **Admin Dashboard** streams.

---

## 1. Candidate WebSocket (`/ws/api/interview/{id}`)

### 📥 Client → Server (Requests)

#### **Candidate Login**
Sent immediately after connection to identify the candidate.
```json
{
    "type": "login",
    "email": "candidate@example.com"
}
```

#### **Start Interview**
Sent when the candidate clicks "Start Interview" in the UI.
```json
{
    "type": "start_interview",
    "interview_id": 62
}
```

#### **Tab Switch**
Sent when the candidate switches tabs or leaves the window.
```json
{
    "type": "tab_switch",
    "interview_id": 62
}
```

#### **Tab Return**
Sent when the candidate returns to the interview tab.
```json
{
    "type": "tab_return",
    "interview_id": 62
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

### 📤 Server → Client (Responses)

#### **Violation Detected** (Real-time warning)
```json
{
    "event_type": "violation_detected",
    "interview_id": 62,
    "data": {
        "violation_type": "tab_switch",
        "violation_count": 1,
        "timestamp": "2026-05-06T13:20:15.123Z",
        "details": "Tab switch detected (Attempt 1)"
    }
}
```

#### **Interview Suspended** (Auto-termination)
```json
{
    "event_type": "interview_suspended",
    "interview_id": 62,
    "data": {
        "reason": "multiple_tab_switch",
        "warning_count": 3,
        "max_warnings": 3,
        "last_violation": "tab_switch",
        "suspended_at": "2026-05-06T13:21:00.000Z"
    }
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

## 2. Admin WebSocket (`/api/admin/dashboard/ws`)

All Admin events now use a **Standardized Enriched Format**. The `interview_id` is always located inside the `data` object.

### 📤 Server → Client (Enriched Events)

#### **Format Template**
```json
{
    "event_type": "EVENT_NAME",
    "data": {
        "interview_id": 62,
        "interview_status": "LIVE",
        "candidate": {
            "candidate_id": 123,
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com"
        },
        "proctoring_events": {
            "tab_switch_count": 0
        },
        "dashboard_data": {
            "live": 1,
            "proctoring_activity": "5.00%",
            "failed_today": 0,
            "passed_today": 0
        },
        // ... event specific fields below ...
        "timestamp": "2026-05-06T13:15:00Z"
    }
}
```

#### **Event Names & Specific Fields**

| `event_type` | Trigger | Extra Fields in `data` |
|--------------|---------|------------------------|
| `candidate_connected` | Candidate WS connects | `timestamp` |
| `candidate_logged_in` | Candidate sends `login` | `timestamp` |
| `interview_started` | Candidate sends `start_interview` | `started_at` |
| `violation_detected` | Any proctoring violation | `violation_type`, `details`, `timestamp` |
| `interview_suspended` | Candidate is suspended | `reason`, `warning_count`, `suspended_at` |
| `interview_completed` | Candidate finishes | `result_status`, `completed_at` |
| `interview_expired` | Time limit exceeded | `expired_at` |
| `candidate_disconnected` | Candidate WS disconnects | `timestamp` |

---

### Example: Enriched Violation Event (Admin Side)
```json
{
    "event_type": "violation_detected",
    "data": {
        "interview_id": 62,
        "interview_status": "LIVE",
        "candidate": {
            "candidate_id": 123,
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com"
        },
        "proctoring_events": {
            "tab_switch_count": 2
        },
        "dashboard_data": { "live": 1, "proctoring_activity": "5.00%", "failed_today": 0, "passed_today": 0 },
        "violation_type": "tab_switch",
        "details": "Tab switch detected (Attempt 2)",
        "timestamp": "2026-05-06T13:20:15Z"
    }
}
```
