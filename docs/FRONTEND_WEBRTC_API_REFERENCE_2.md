# Frontend WebRTC & WebSocket API Reference

This document provides a reference for integrating the **WebRTC Proctoring Stream** and the corresponding **WebSocket Events** triggered by AI proctoring.

---

## 1. WebRTC Connection (`/api/video/offer`)

The connection follows the standard WebRTC signaling flow. The frontend sends an SDP Offer, and the backend returns an SDP Answer.

### 📥 Client → Server (POST Request)
- **Endpoint**: `/api/video/offer`
- **Method**: `POST`
- **Body**:
```json
{
    "sdp": "v=0\r\no=- 42... (standard SDP offer string)",
    "type": "offer",
    "interview_id": 65
}
```

### 📤 Server → Client (Response)
- **Status Code**: `200 OK`
- **Body**:
```json
{
    "status_code": 200,
    "success": true,
    "message": "WebRTC offer processed successfully",
    "data": {
        "sdp": "v=0\r\no=- 84... (standard SDP answer string)",
        "type": "answer"
    }
}
```

---

## 2. WebRTC DataChannel (High-Frequency AI)

Once the DataChannel is `open`, the backend pushes raw AI results every 5th frame.

### 📤 Server → Client (Real-time Updates)
```json
{
    "type": "proctoring_update",
    "interview_id": 65,
    "frame_id": 120,
    "data": {
        "faces": 1,
        "gaze": "Gazing Center",
        "warning": "",
        "detectors": { "face": true, "gaze": true }
    }
}
```
**Possible Warnings**: `MULTIPLE FACES DETECTED`, `NO FACE DETECTED`, `WARNING: Gazing Away`.

---

## 3. WebSocket Integration (Business Logic Events)

While the DataChannel sends "raw" data, the **Main WebSockets** send critical business logic events (Warnings and Suspensions) based on the AI analysis.

### 🕒 When do these happen?
1. **AI Detection**: The WebRTC stream receives a frame.
2. **Analysis**: AI detects a violation (e.g., No Face).
3. **Throttling**: The system checks if it should record the violation (once every 5 seconds).
4. **Trigger**: If recorded, the backend pushes events to the WebSockets.

---

### 📤 Candidate WebSocket (`/ws/api/interview/{id}`)

The candidate receives a simplified warning to alert them to correct their behavior.

#### **Violation Detected**
```json
{
    "event_type": "violation_detected",
    "interview_id": 65,
    "data": {
        "violation_type": "no_face", // or "multiple_faces", "gaze_away"
        "details": "Faces: 0, Auth: False, Gaze: No Gaze",
        "warning_count": 1,
        "max_warnings": 3,
        "timestamp": "2026-05-14T10:45:00Z"
    }
}
```

---

### 📤 Admin WebSocket (`/api/admin/dashboard/ws`)

The Admin Dashboard receives "Enriched" events containing full session metadata.

#### **Violation Detected** (Admin View)
```json
{
    "event_type": "violation_detected",
    "data": {
        "interview_id": 65,
        "interview_status": "LIVE",
        "candidate": { "candidate_name": "John Doe", "candidate_email": "john@example.com" },
        "violation_type": "no_face",
        "details": "Faces: 0, Auth: False, Gaze: No Gaze",
        "timestamp": "2026-05-14T10:45:00Z"
    }
}
```

#### **Interview Suspended** (Critical/Max Warnings)
Sent when the candidate exceeds `max_warnings` or a critical violation occurs.
```json
{
    "event_type": "interview_suspended",
    "data": {
        "interview_id": 65,
        "interview_status": "COMPLETED",
        "reason": "max_warnings_exceeded",
        "warning_count": 3,
        "last_violation": "no_face",
        "suspension_metadata": {
            "auto_suspended": true,
            "suspended_at": "2026-05-14T10:46:00Z"
        }
    }
}
```

---

## 4. Frontend Guidelines

1. **Face Recognition Note**: Face recognition (identity matching) is currently disabled. Focus on Face Count and Gaze.
2. **Event Handling**:
   - Use the **DataChannel** for local UI feedback (e.g., "Adjust your camera").
   - Use the **WebSocket** for terminal actions (e.g., "Interview Terminated due to violations").
3. **Connection Management**: If the WebRTC connection fails, the candidate should still be able to continue the interview via WebSocket-only mode if allowed.
