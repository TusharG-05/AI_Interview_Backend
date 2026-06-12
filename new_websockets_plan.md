  # AI Interview Backend - WebSocket API Documentation

This document outlines the WebSocket connections and real-time events available in the system. All endpoints are fully secured and support role-based access.

---

## 1. Candidate Interview WebSocket

Used by the candidate during the live interview to send status updates, verify face presence, and report proctoring violations.

* **Endpoint**: `wss://<api-domain>/ws/api/interview/{interview_id}?token=<candidate_jwt>`
* **Role Required**: `CANDIDATE` (JWT must belong to the candidate assigned to the interview).

### 1.1 Events Sent BY the Candidate (Frontend -> Backend)

Send these JSON payloads over the connection to trigger backend lifecycle events or report violations.

#### Login & Setup
```json
{
  "event_type":"Interview_login",
  "Interview_status": "CONNECTED"
}
```

#### Start Interview
```json
{
  "event_type":"Interview_started",
  "Interview_status": "LIVE"
}
```

#### Candidate disconnected
```json
{
  "event_type":"Interview_disconnected",
  "Interview_status": "DISCONNECTED"
}
```

#### Finish / Submit Interview
```json
{
  "event_type":"Interview_finished",
  "Interview_status": "COMPLETED"
}
```

#### Interview Suspended
Sent when the candidate exceeds the maximum allowed warnings. The frontend should forcibly close the interview UI.
```json
{
  "event_type": "Interview_suspended",
  "Interview_status": "SUSPENDED", // also change the related field in schema
}
```

#### Proctoring Violations
Used to report ML-based vision detections (e.g., multiple faces, no face, mobile phone detected) or browser events (e.g., tab switches).
```json
{
  "event_type": "Proctoring_violation",
  "violation_type": "tab_switch", // e.g., "tab_switch", "multiple_faces", "mobile_phone", "no_face"
}
```

---

## 2. Global Admin Dashboard WebSocket

Used on the Admin overview dashboard to receive real-time updates for **all active interviews created by the connected admin**.

* **Endpoint**: `wss://<api-domain>/api/admin/dashboard/ws?token=<admin_jwt>`
* **Role Required**: `ADMIN` or `SUPER_ADMIN`.
* **Security Filter**: `ADMIN` users will only receive broadcasts for interview sessions where `session.admin_id == user.id`. `SUPER_ADMIN` receives all broadcasts.

### Events Received (Backend -> Frontend)

All events follow the same enriched payload structure containing candidate metadata, session status, and metrics.

#### Candidate Lifecycle Events
* `Interview_login`
* `Interview_started`
* `Interview_disconnected`
* `Interview_finished`
* `Proctoring_violation`

**Example Payload Structure**:
```json
{
  "event_type": "Interview_login", // `Interview_login``Interview_started``Interview_disconnected``Interview_finished``Proctoring_violation`
  "data": {
    "interview_id": 123,
    "session_admin_id": 45, // ID of the admin who created the interview
    "interview_status": "CONNECTED", // LIVE, DISCONNECTED, COMPLETED, SUSPENDED
    "candidate": {
      "candidate_id": 101,
      "candidate_name": "John Doe",
      "candidate_email": "john.doe@example.com"
    },
    "proctoring_events": {
      "id": 123,
      "tab_switch_count": 0,
      "warning_count": 0
    },
    "dashboard_data": {
      "live": 5,
      "proctoring_activity": "10.00%",
      "failed_today": 1,
      "passed_today": 4
    },
    "timestamp": "2026-06-10T10:30:00.000Z" // Added to most events
  }
}
```


*(Note: Proctoring violation events no longer appear on the global dashboard stream directly to prevent clutter, but `interview_suspended` will be triggered if the violations exceed thresholds).*

---

#### Tab Return Event(remove)
Sent when the candidate returns to the interview tab after switching away.
```json
{"violation_type": "tab_switch", // e.g., "tab_switch", "multiple_faces", "mobile_phone", "no_face"
  "event_type": "proctoring_violation",
  "violation_type": "tab_return"
}
```

### 1.2 Events Received BY the Candidate (Backend -> Frontend) (remove)

The backend will asynchronously send these events to the candidate connection when enforcement thresholds are reached.

#### Warning Issued
```json
{
  "event_type": "proctoring_violation",
  "data": {
    "violation_type": "String", // e.g., "tab_switch", "multiple_faces", "mobile_phone", "no_face"
    "tab_switch_count": "number",
    "warnings_count": "number",
  }
}
```

## 3. Per-Interview Admin Dashboard WebSocket (remove)

Used when an Admin opens a **specific candidate's live interview details page** to monitor them individually.

* **Endpoint**: `wss://<api-domain>/ws/api/dashboard/{interview_id}?token=<admin_jwt>`
* **Role Required**: `ADMIN` or `SUPER_ADMIN`.

### Events Received (Backend -> Frontend)
Receives the exact same JSON payloads and event types as the Global Admin Dashboard WebSocket, but strictly filtered for the specified `interview_id`.