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
        "interview_status": "CONNECTED", // Possible: SCHEDULED, CONNECTED, LIVE, DISCONNECTED, COMPLETED, EXPIRED
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

## 3. Video Proctoring WebSocket (`/video/stream/{id}`)

This is a high-frequency **Binary WebSocket** used for real-time AI proctoring (face detection, gaze tracking, and authentication).

### 📥 Client → Server (Binary Data)

The client should send raw video frames as binary data (`Blob` or `ArrayBuffer`). Frames are typically captured from a `<video>` element or `MediaStreamTrack` and sent at a rate of 1-5 frames per second.

- **Format**: `Binary (JPEG/PNG)`
- **Endpoint**: `/video/stream/{interview_id}?token=ACCESS_TOKEN`

### 📤 Server → Client (Proctoring Updates)

The server returns a JSON object for **every** frame processed.

#### **Proctoring Update**
```json
{
    "type": "proctoring_update",
    "interview_id": 62,
    "timestamp": 1715422800.123,
    "data": {
        "auth": true,               // Whether the face matches the registered candidate
        "auth_dist": 0.42,          // Confidence score (lower is better for matching)
        "faces": 1,                 // Number of faces detected in the frame
        "gaze": "Gazing Center",    // Gaze direction or "WARNING: Gazing Away"
        "warning": "",              // "MULTIPLE FACES DETECTED", "NO FACE DETECTED", etc.
        "box": [100, 200, 300, 150] // [top, right, bottom, left] of the detected face
    }
}
```

#### **Possible Warnings**
- `""` (Empty string means no issues)
- `INITIALIZING AI...` (Models are still loading on the server)
- `MULTIPLE FACES DETECTED`
- `NO FACE DETECTED`
- `SECURITY ALERT: UNAUTHORIZED PERSON` (Face does not match the candidate)
- `WARNING: Gazing Away`
- `Bad Frame` (Frame decoding failed)

---

## 4. System Status WebSocket (`/status/ws`)

A lightweight feed purely for real-time proctoring warnings (without the full AI coordinate data).

### 📤 Server → Client (JSON)

#### **Warning Feed**
```json
{
    "warning": "NO FACE DETECTED"
}
```
Possible values match the `warning` field in the Video Proctoring stream.
