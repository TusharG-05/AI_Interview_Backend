# WebSocket Request/Response Guide

Complete protocol documentation for both WebSocket endpoints with real request/response examples, triggers, and use cases.

---

## 📋 Overview

| Endpoint | Purpose | Audience | Events Received |
|----------|---------|----------|-----------------|
| `/ws/api/interview/{interview_id}` | Candidate violation stream | Candidate (in browser) | `ViolationEvent` only |
| `/ws/api/dashboard/{interview_id}` | Admin monitoring stream | Admin/Proctor (dashboard) | `ViolationEvent` + Status Changes |

---

## 1️⃣ CANDIDATE VIOLATION STREAM

### Connection Request

**Endpoint:** `GET /ws/api/interview/{interview_id}?token=<candidate_access_token>`

**URL Example:**
```
ws://127.0.0.1:8000/ws/api/interview/42?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**cURL Example (WebSocket):**
```bash
# Note: cURL doesn't natively support WebSocket, use websocat or wscat instead
wscat -c "ws://127.0.0.1:8000/ws/api/interview/42?token=YOUR_CANDIDATE_TOKEN"
```

**Python Client Example:**
```python
import asyncio
import websockets
import json

async def connect_candidate_stream(interview_id: int, token: str):
    url = f"ws://127.0.0.1:8000/ws/api/interview/{interview_id}?token={token}"
    
    try:
        async with websockets.connect(url) as websocket:
            print(f"✓ Connected to candidate stream for interview {interview_id}")
            
            # Listen for violation events
            while True:
                message = await websocket.recv()
                event = json.loads(message)
                print(f"Received violation event: {event}")
                
    except Exception as e:
        print(f"Connection failed: {e}")

# Usage
asyncio.run(connect_candidate_stream(interview_id=42, token="your_token_here"))
```

**JavaScript/TypeScript Example:**
```typescript
function connectCandidateStream(interviewId: number, token: string) {
    const url = `ws://127.0.0.1:8000/ws/api/interview/${interviewId}?token=${token}`;
    
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
        console.log(`✓ Connected to candidate violation stream`);
    };
    
    ws.onmessage = (event) => {
        const violation = JSON.parse(event.data);
        console.log("Violation detected:", violation);
        
        // Show notification to candidate
        showViolationNotification(violation);
    };
    
    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
    
    ws.onclose = () => {
        console.log("Disconnected from violation stream");
    };
}

// Usage
connectCandidateStream(42, token);
```

---

### ✅ Success Response (Connection Accepted)

**HTTP Status:** 101 Switching Protocols

**Connection Established - Ready to receive events**

No initial response body. Connection will remain open and stream events as they occur.

---

### ❌ Error Response (Missing/Invalid Token)

**Request:**
```
GET /ws/api/interview/42
(no token parameter)
```

**Response:** 403 Forbidden or Connection Rejected

The server will close the connection immediately if token is not provided or invalid.

---

### 📤 Outgoing Events (Server → Client)

#### 1️⃣ Interview Finished Confirmation

**When:** Candidate successfully finishes the interview via WebSocket.

**Response Body:**

```json
{
    "type": "interview_finished_confirmation",
    "status": "success",
    "message": "Interview finished. Results are being processed."
}
```

---

### 📤 Violation Event - Candidate Receives

**When:** Candidate violates proctoring rules (tab switch, wrong face, etc.)

**Response Body (Server → Client):**

#### Example 1: Tab Switch Violation

```json
{
    "event_type": "violation_detected",
    "interview_id": 42,
    "data": {
        "violation_type": "tab_switch",
        "violation_count": 1,
        "timestamp": "2026-05-05T13:20:15.123456Z",
        "details": "Candidate switched to another tab"
    }
}
```

#### Example 2: Multiple Faces Detected

```json
{
    "event_type": "violation_detected",
    "interview_id": 42,
    "data": {
        "violation_type": "multiple_faces",
        "violation_count": 1,
        "timestamp": "2026-05-05T13:20:20.654321Z",
        "details": "Multiple faces detected in frame"
    }
}
```

#### Example 3: No Face Detected

```json
{
    "event_type": "violation_detected",
    "interview_id": 42,
    "data": {
        "violation_type": "no_face",
        "violation_count": 2,
        "timestamp": "2026-05-05T13:20:25.987654Z",
        "details": "No face detected in video feed"
    }
}
```

#### Example 4: Wrong Candidate/Unauthorized Person

```json
{
    "event_type": "violation_detected",
    "interview_id": 42,
    "data": {
        "violation_type": "wrong_candidate",
        "violation_count": 1,
        "timestamp": "2026-05-05T13:20:30.111111Z",
        "details": "Face recognition failed or unauthorized person detected"
    }
}
```

---

### 🚫 Suspension Event - Candidate Receives (When Threshold Exceeded)

**When:** Candidate accumulates too many violations (default: 3+ warnings)

**Response Body:**

```json
{
    "event_type": "interview_suspended",
    "interview_id": 42,
    "data": {
        "reason": "max_warnings_exceeded",
        "warning_count": 3,
        "max_warnings": 3,
        "last_violation": "tab_switch",
        "suspended_at": "2026-05-05T13:21:00.000000Z"
    }
}
```

---

### 🔄 Client → Server (Messages)

**1. Keep-Alive Heartbeat** (optional):
```json
{
    "type": "ping"
}
```

**2. Candidate Login Notification** (required for dashboard tracking):
The frontend should send this message immediately after the WebSocket connection is established to notify the admin of the candidate's active presence.

```json
{
    "type": "login",
    "email": "candidate@example.com"
}
```

**3. Tab Switch Notification**:
Sent by the frontend when the candidate leaves the interview tab.

```json
{
    "type": "tab_switch",
    "interview_id": 42
}
```

**4. Tab Return Notification**:
Sent by the frontend when the candidate returns to the interview tab.

```json
{
    "type": "tab_return",
    "interview_id": 42
}
```

**5. Finish Interview Notification**:
Sent by the frontend when the candidate manually clicks "Finish Interview". This triggers result processing and notifies the admin.

```json
{
    "type": "finish_interview",
    "interview_id": 42
}
```

---

### 📊 Candidate Stream - Use Case Scenarios

#### Scenario 1: Single Tab Switch Violation
```
Timeline:
  13:20:15 → Candidate switches tabs
  13:20:15 → Server sends: violation_detected (tab_switch, count: 1)
  13:20:15 → Client: Show warning: "Please keep interview in focus"
  
  (Candidate returns to interview tab after 5 seconds)
  
  (No additional events sent - connection remains open)
```

#### Scenario 2: Multiple Violations Leading to Suspension
```
Timeline:
  13:20:15 → Tab switch violation
  13:20:15 → Server sends: violation_detected (tab_switch, count: 1)
  13:20:15 → Client: Show warning #1
  
  13:20:25 → Multiple faces detected
  13:20:25 → Server sends: violation_detected (multiple_faces, count: 2)
  13:20:25 → Client: Show warning #2
  
  13:20:35 → No face detected
  13:20:35 → Server sends: violation_detected (no_face, count: 3)
  13:20:35 → Client: Show warning #3
  
  13:21:00 → Max warnings exceeded (threshold = 3)
  13:21:00 → Server sends: interview_suspended (warning_count: 3)
  13:21:00 → Client: 
    - Lock interface
    - Show: "Interview suspended due to policy violations"
    - Redirect to results page
    - Close WebSocket connection
```

#### Scenario 3: Clean Interview (No Violations)
```
Timeline:
  13:15:00 → Candidate connects
  13:15:00 → Connection established, waiting for events
  
  (Interview progresses, no violations occur)
  
  13:45:00 → Interview complete (not via WebSocket)
  13:45:00 → Connection closes gracefully
```

---

## 2️⃣ ADMIN DASHBOARD STREAM

### Connection Request

**Endpoint:** `GET /ws/api/dashboard/{interview_id}?token=<admin_access_token>`

**URL Example:**
```
ws://127.0.0.1:8000/ws/api/dashboard/42?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**cURL Example:**
```bash
wscat -c "ws://127.0.0.1:8000/ws/api/dashboard/42?token=YOUR_ADMIN_TOKEN"
```

**Python Client Example:**
```python
import asyncio
import websockets
import json
from datetime import datetime

async def connect_admin_dashboard(interview_id: int, token: str):
    url = f"ws://127.0.0.1:8000/ws/api/dashboard/{interview_id}?token={token}"
    
    try:
        async with websockets.connect(url) as websocket:
            print(f"✓ Admin connected to interview {interview_id} dashboard")
            
            # Listen for all events (violations + status changes)
            while True:
                message = await websocket.recv()
                event = json.loads(message)
                
                timestamp = datetime.now().isoformat()
                print(f"[{timestamp}] Admin Event: {event['event_type']}")
                print(f"  Details: {event['data']}")
                
                # Update dashboard UI based on event type
                handle_dashboard_event(event)
                
    except Exception as e:
        print(f"Admin connection failed: {e}")

def handle_dashboard_event(event):
    """Route event to appropriate handler"""
    handlers = {
        "violation_detected": handle_violation,
        "interview_started": handle_interview_started,
        "interview_suspended": handle_interview_suspended,
        "interview_completed": handle_interview_completed,
        "interview_expired": handle_interview_expired,
    }
    
    handler = handlers.get(event["event_type"])
    if handler:
        handler(event)

def handle_violation(event):
    print(f"  → Update violation counter on dashboard")
    print(f"  → Highlight candidate card in red")

def handle_interview_started(event):
    print(f"  → Mark interview as LIVE")
    print(f"  → Start timer")

def handle_interview_suspended(event):
    print(f"  → Mark interview as SUSPENDED")
    print(f"  → Show suspension reason")
    print(f"  → Alert admin proctor")

def handle_interview_completed(event):
    print(f"  → Mark interview as COMPLETED")
    print(f"  → Show result: {event['data'].get('result_status')}")
    print(f"  → Stop monitoring")

def handle_interview_expired(event):
    print(f"  → Mark interview as EXPIRED")
    print(f"  → Stop monitoring")

# Usage
asyncio.run(connect_admin_dashboard(interview_id=42, token="admin_token_here"))
```

**JavaScript/React Example:**
```typescript
import { useEffect, useRef } from 'react';

function AdminDashboard({ interviewId, adminToken }) {
    const wsRef = useRef<WebSocket | null>(null);
    
    useEffect(() => {
        const url = `ws://api.example.com/ws/api/dashboard/${interviewId}?token=${adminToken}`;
        
        const ws = new WebSocket(url);
        wsRef.current = ws;
        
        ws.onopen = () => {
            console.log('✓ Connected to interview dashboard');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.event_type) {
                case 'violation_detected':
                    updateViolationCounter(data);
                    playViolationAlert();
                    break;
                    
                case 'interview_started':
                    markAsLive(data);
                    startTimer();
                    break;
                    
                case 'interview_suspended':
                    markAsSuspended(data);
                    showSuspensionReason(data.data);
                    notifyProctor(data);
                    break;
                    
                case 'interview_completed':
                    markAsCompleted(data);
                    showResult(data.data.result_status);
                    break;
                    
                case 'interview_expired':
                    markAsExpired(data);
                    break;
            }
        };
        
        ws.onerror = (error) => {
            console.error('Dashboard WebSocket error:', error);
        };
        
        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [interviewId, adminToken]);
    
    return (
        <div className="dashboard">
            {/* Dashboard UI components */}
        </div>
    );
}

export default AdminDashboard;
```

---

### ✅ Success Response (Connection Accepted)

**HTTP Status:** 101 Switching Protocols

No initial response. Connection open and ready to receive events.

---

### ❌ Error Response (Invalid Credentials)

**Response:** 403 Forbidden

Connection rejected if token is missing, invalid, or user is not an admin.

---

### 📤 Event Types - Admin Receives

#### 1️⃣ VIOLATION DETECTED EVENT

**When:** Any violation occurs during interview

**Response Body:**

```json
{
    "event_type": "violation_detected",
    "data": {
        "interview_id": 42,
        "interview_status": "LIVE",
        "candidate": {
            "candidate_id": 123,
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com"
        },
        "proctoring_events": {
            "tab_switch_count": 1
        },
        "violation_type": "tab_switch",
        "details": "Candidate switched to another tab",
        "timestamp": "2026-05-05T13:20:15.123456Z",
        "severity": "warning",
        "dashboard_data": {
            "live": 1,
            "proctoring_activity": "5.00%",
            "failed_today": 0,
            "passed_today": 0
        }
    }
}
```

**Violation Types Admin Can Receive:**
- `tab_switch` - Candidate switched to different browser tab
- `multiple_faces` - More than one face in frame
- `no_face` - No face detected in video
- `wrong_candidate` - Face recognition failed or unauthorized person
- `gaze_away` - Candidate not looking at screen (if eye-tracking enabled)
- `connection_unstable` - Network issues or device unstable
- `unauthorized_device` - External input device detected

**Severity Levels:**
- `"info"` - Informational (connection unstable, low audio)
- `"warning"` - Accumulate toward suspension (tab switch, face issues)
- `"critical"` - Immediate suspension (security alerts, unauthorized persons)

---

#### 2️⃣ INTERVIEW STARTED EVENT

**When:** Candidate starts the interview (SCHEDULED → LIVE transition)

**Response Body:**

```json
{
    "event_type": "interview_started",
    "data": {
        "interview_id": 42,
        "interview_status": "LIVE",
        "candidate": {
            "candidate_id": 123,
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com"
        },
        "proctoring_events": {
            "tab_switch_count": 0
        },
        "started_at": "2026-05-05T13:15:00.000000Z",
        "dashboard_data": {
            "live": 1,
            "proctoring_activity": "0.00%",
            "failed_today": 0,
            "passed_today": 0
        }
    }
}
```

---

#### 3️⃣ INTERVIEW SUSPENDED EVENT

**When:** Violation threshold exceeded OR admin manually suspends

**Response Body:**

```json
{
    "event_type": "interview_suspended",
    "data": {
        "interview_id": 42,
        "interview_status": "SUSPENDED",
        "candidate": {
            "candidate_id": 123,
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com"
        },
        "proctoring_events": {
            "tab_switch_count": 3
        },
        "reason": "max_warnings_exceeded",
        "warning_count": 3,
        "max_warnings": 3,
        "last_violation": "tab_switch",
        "suspension_metadata": {
            "auto_suspended": true,
            "suspended_at": "2026-05-05T13:21:00.000000Z"
        },
        "dashboard_data": {
            "live": 0,
            "proctoring_activity": "100.00%",
            "failed_today": 1,
            "passed_today": 0
        }
    }
}
```

**Possible Suspension Reasons:**
- `"max_warnings_exceeded"` - Accumulated too many violations
- `"critical_violation"` - Single critical violation occurred
- `"manual_suspension"` - Admin manually suspended the interview
- `"security_breach"` - Unauthorized person or device detected

---

#### 4️⃣ INTERVIEW COMPLETED EVENT

**When:** Interview finishes (time expires, candidate submits, etc.)

**Response Body:**

```json
{
    "event_type": "interview_completed",
    "data": {
        "interview_id": 42,
        "interview_status": "COMPLETED",
        "candidate": {
            "candidate_id": 123,
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com"
        },
        "proctoring_events": {
            "tab_switch_count": 0
        },
        "result_status": "Pass",
        "completed_at": "2026-05-05T13:45:00.000000Z",
        "dashboard_data": {
            "live": 0,
            "proctoring_activity": "0.00%",
            "failed_today": 0,
            "passed_today": 1
        }
    }
}
```

**Result Status Values:**
- `"Pass"` - Candidate passed evaluation
- `"Fail"` - Candidate failed evaluation
- `"Suspended"` - Candidate was suspended (policy violations)
- `"Incomplete"` - Candidate did not complete

---

#### 5️⃣ INTERVIEW EXPIRED EVENT

**When:** Interview time limit exceeded

**Response Body:**

```json
{
    "event_type": "interview_expired",
    "data": {
        "interview_id": 42,
        "interview_status": "EXPIRED",
        "candidate": {
            "candidate_id": 123,
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com"
        },
        "proctoring_events": {
            "tab_switch_count": 0
        },
        "scheduled_duration_minutes": 30,
        "actual_duration_minutes": 30.5,
        "expired_at": "2026-05-05T13:45:30.000000Z",
        "reason": "duration_timeout",
        "dashboard_data": {
            "live": 0,
            "proctoring_activity": "0.00%",
            "failed_today": 0,
            "passed_today": 1
        }
    }
}
```

---

#### 6️⃣ CANDIDATE CONNECTION EVENTS

**When:** Candidate connects or disconnects from their proctoring stream.

**Candidate Logged In:**
This event is triggered when the candidate sends a `{"type": "login"}` message over the WebSocket.
```json
{
    "event_type": "candidate_logged_in",
    "data": {
        "interview_id": 42,
        "interview_status": "LIVE",
        "candidate": {
            "candidate_id": 123,
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com"
        },
        "proctoring_events": {
            "tab_switch_count": 0
        },
        "timestamp": "2026-05-05T13:15:00.000000Z",
        "dashboard_data": {
            "live": 1,
            "proctoring_activity": "0.00%",
            "failed_today": 0,
            "passed_today": 0
        }
    }
}
```

**Connection Established:**
```json
{
    "event_type": "candidate_connected",
    "interview_id": 42,
    "data": {
        "timestamp": "2026-05-05T13:15:00.000000Z",
        "dashboard_data": {
            "live": 1,
            "proctoring_activity": "0.00%",
            "failed_today": 0,
            "passed_today": 0
        }
    }
}
```

**Connection Lost:**
```json
{
    "event_type": "candidate_disconnected",
    "interview_id": 42,
    "data": {
        "timestamp": "2026-05-05T13:45:00.000000Z",
        "dashboard_data": {
            "live": 0,
            "proctoring_activity": "0.00%",
            "failed_today": 0,
            "passed_today": 1
        }
    }
}
```

---

### 📊 Admin Dashboard - Use Case Scenarios

#### Scenario 1: Real-Time Monitoring During Interview

```
Timeline:

13:15:00 → Admin opens dashboard
  ↓
  GET ws://api/dashboard/42?token=ADMIN_TOKEN
  ↓
  Connection: 101 Switching Protocols ✓
  
13:15:05 → INTERVIEW STARTED EVENT received
  {
    "event_type": "interview_started",
    "data": {
      "status": "LIVE",
      "started_at": "2026-05-05T13:15:00Z"
    }
  }
  → Admin Dashboard: Shows interview in LIVE status, starts timer

13:20:15 → VIOLATION DETECTED EVENT received
  {
    "event_type": "violation_detected",
    "data": {
      "violation_type": "tab_switch",
      "violation_count": 1
    }
  }
  → Admin Dashboard: 
    - Updates violation counter: 1
    - Highlights candidate card (yellow)
    - Shows notification: "Tab switch detected"

13:20:25 → VIOLATION DETECTED EVENT received
  {
    "event_type": "violation_detected",
    "data": {
      "violation_type": "multiple_faces",
      "violation_count": 2
    }
  }
  → Admin Dashboard: Violation counter = 2

13:20:35 → VIOLATION DETECTED EVENT received
  {
    "event_type": "violation_detected",
    "data": {
      "violation_type": "no_face",
      "violation_count": 3
    }
  }
  → Admin Dashboard: Violation counter = 3

13:21:00 → INTERVIEW SUSPENDED EVENT received
  {
    "event_type": "interview_suspended",
    "data": {
      "reason": "max_warnings_exceeded",
      "warning_count": 3
    }
  }
  → Admin Dashboard:
    - Changes status to SUSPENDED (red)
    - Shows: "Interview suspended due to 3 policy violations"
    - Alert/sound notification
    - Admin can now manually review candidate
    - Option to resume or mark as failed
```

#### Scenario 2: Multi-Interview Monitoring (Multiple Dashboards)

```
Admin has 5 browser tabs open, each monitoring different interview_id:

Tab 1: ws://api/dashboard/40?token=...  (Interview #40 - In Progress)
Tab 2: ws://api/dashboard/41?token=...  (Interview #41 - 1 violation)
Tab 3: ws://api/dashboard/42?token=...  (Interview #42 - 2 violations)
Tab 4: ws://api/dashboard/43?token=...  (Interview #43 - Just started)
Tab 5: ws://api/dashboard/44?token=...  (Interview #44 - Completed)

Each tab maintains its own WebSocket connection and receives independent event streams.

Admin can:
  - See real-time status of all interviews simultaneously
  - Prioritize monitoring tabs with violations
  - Jump to any suspended interview for manual review
```

#### Scenario 3: Critical Security Violation

```
Timeline:

13:25:00 → CRITICAL VIOLATION - Unauthorized Person Detected

Admin receives:
{
    "event_type": "violation_detected",
    "interview_id": 42,
    "data": {
        "violation_type": "SECURITY ALERT: UNAUTHORIZED PERSON",
        "severity": "critical",
        "violation_count": 1,
        "timestamp": "2026-05-05T13:25:00Z"
    }
}

Immediately followed by:

{
    "event_type": "interview_suspended",
    "interview_id": 42,
    "data": {
        "reason": "critical_violation",
        "violation": "unauthorized_person_detected",
        "auto_suspended": true,
        "suspended_at": "2026-05-05T13:25:01Z"
    }
}

Admin Dashboard:
  - FLASHING RED alert
  - High-priority notification: "CRITICAL: Unauthorized person detected"
  - Auto-plays alert sound
  - Shows interview recording/screenshot
  - Options: Mark invalid, Disqualify candidate, etc.
```

---

## 📋 Quick Reference Matrix

| Event | Triggered By | Sent To | Payload Contains | Action Required |
|-------|-------------|---------|-----------------|-----------------|
| `violation_detected` | Any policy breach | Candidate + Admin | violation_type, count, details | Show warning (candidate), Log (admin) |
| `interview_started` | Candidate starts interview | Admin only | start_time, duration | Begin monitoring |
| `interview_suspended` | 3+ violations OR critical violation | Admin only | reason, count | Review candidate |
| `interview_completed` | Time expired OR candidate finishes | Admin only | result_status, total_violations | Record result |
| `interview_expired` | Time limit exceeded | Admin only | actual_duration | Auto-complete |

---

## 🔌 Connection Persistence

### Keep-Alive / Heartbeat

**Recommended:** Send a ping every 30 seconds to keep connection alive

**Client Code:**

```python
async def keep_alive(websocket):
    """Send periodic ping to maintain connection"""
    while True:
        try:
            await websocket.ping()
            await asyncio.sleep(30)
        except:
            break
```

**JavaScript:**

```javascript
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000);
```

---

## 🔐 Token Validation

**Token Format:** JWT (JSON Web Token)

**Token Sources:**
- **Candidate Token:** Obtained from `/api/auth/login` endpoint with candidate credentials
- **Admin Token:** Obtained from `/api/auth/login` endpoint with admin credentials

**Token Payload (typical):**
```json
{
    "sub": 7,              // user_id
    "email": "candidate@example.com",
    "role": "candidate",   // or "admin"
    "exp": 1651829500,    // expiration timestamp
    "iat": 1651743100     // issued at timestamp
}
```

**Token Validation Process:**
1. Client sends WebSocket connection with `?token=JWT`
2. Server decodes JWT and verifies signature
3. Server checks token expiration
4. Server verifies user role (candidate vs admin)
5. Server checks if user can access this interview_id
6. If all checks pass: `101 Switching Protocols` and connection accepted
7. If any check fails: `403 Forbidden` and connection rejected

---

## 🐛 Common Issues & Troubleshooting

### Issue 1: "WebSocket connection failed immediately"
**Causes:**
- Token missing or invalid
- Token expired
- Wrong token (admin token for candidate endpoint)
- User doesn't have access to this interview_id

**Solution:** Verify token is fresh and has correct role

### Issue 2: "Connection stays open but no events received"
**Causes:**
- No violations occurring
- Monitoring wrong interview_id
- Correct, just no events yet

**Solution:** This is normal. Events only send when violations occur or status changes.

### Issue 3: "Receiving old/stale events"
**Causes:**
- Each connection is independent; it doesn't replay historical events
- Only NEW events after connection are sent

**Solution:** If you need history, query `/api/interview/{id}/violations` endpoint for historical data

### Issue 4: "Connection drops unexpectedly"
**Causes:**
- Network interruption
- Interview completed or suspended
- Admin forcefully closed interview
- Server restart

**Solution:** Implement reconnection logic with exponential backoff

---

## 📝 Example Full Integration

**Real-world candidate experience:**

```javascript
class InterviewCandidate {
    constructor(interviewId, token) {
        this.interviewId = interviewId;
        this.token = token;
        this.violationCount = 0;
        this.maxWarnings = 3;
    }
    
    async start() {
        const url = `ws://${API_HOST}/ws/api/interview/${this.interviewId}?token=${this.token}`;
        
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => this.onConnected();
        this.ws.onmessage = (e) => this.onViolation(JSON.parse(e.data));
        this.ws.onerror = (e) => this.onError(e);
    }
    
    onConnected() {
        console.log('✓ Proctoring monitoring active');
        this.showNotification('Keep interview in focus. Stay in frame. No external help.');
    }
    
    onViolation(event) {
        if (event.event_type === 'violation_detected') {
            this.violationCount = event.data.violation_count;
            
            const remaining = this.maxWarnings - this.violationCount;
            this.showWarning(
                `⚠️ ${event.data.violation_type}: ${remaining} warnings remaining`
            );
        } 
        else if (event.event_type === 'interview_suspended') {
            this.showAlert('❌ Interview suspended due to policy violations');
            this.disableInterface();
            this.ws.close();
            setTimeout(() => window.location.href = '/interview/results', 2000);
        }
    }
    
    showWarning(message) {
        // Show yellow warning box at top of screen
        const box = document.createElement('div');
        box.className = 'warning-box';
        box.textContent = message;
        document.body.prepend(box);
        setTimeout(() => box.remove(), 5000);
    }
    
    showAlert(message) {
        // Show red alert and lock interface
        document.body.style.filter = 'blur(5px)';
        alert(message);
    }
}

// Usage
const candidate = new InterviewCandidate(42, candidateToken);
candidate.start();
```

**Real-world admin monitoring:**

```javascript
class AdminDashboard {
    constructor(token) {
        this.token = token;
        this.dashboards = new Map(); // interviewId -> DashboardCard
    }
    
    monitorInterview(interviewId) {
        const url = `ws://${API_HOST}/ws/api/dashboard/${interviewId}?token=${this.token}`;
        const ws = new WebSocket(url);
        
        ws.onmessage = (e) => {
            const event = JSON.parse(e.data);
            this.handleEvent(interviewId, event);
        };
        
        this.dashboards.set(interviewId, { ws, violations: 0, status: 'connecting' });
    }
    
    handleEvent(interviewId, event) {
        const card = this.dashboards.get(interviewId);
        
        switch (event.event_type) {
            case 'interview_started':
                card.status = 'live';
                card.element.classList.add('live');
                this.updateCard(interviewId);
                break;
                
            case 'violation_detected':
                card.violations++;
                card.element.querySelector('.violation-count').textContent = card.violations;
                
                if (card.violations >= 2) {
                    card.element.classList.add('warning');
                }
                
                this.playNotificationSound();
                break;
                
            case 'interview_suspended':
                card.status = 'suspended';
                card.element.classList.add('suspended');
                card.element.classList.add('flash');
                
                this.showAlert(`Interview #${interviewId} SUSPENDED`);
                break;
                
            case 'interview_completed':
                card.status = 'completed';
                card.result = event.data.result_status;
                break;
        }
        
        this.updateCard(interviewId);
    }
}

// Usage
const dashboard = new AdminDashboard(adminToken);

// Monitor multiple interviews
[40, 41, 42, 43, 44].forEach(id => dashboard.monitorInterview(id));
```

---

## ✅ Testing Checklist

- [ ] Candidate can connect with valid token
- [ ] Candidate connection rejected without token
- [ ] Admin can connect with valid admin token
- [ ] Admin connection rejected with candidate token
- [ ] Violation events received on both streams
- [ ] Suspension event terminates interview
- [ ] Completion event shows results
- [ ] Connections survive 5+ minute idle periods
- [ ] Multiple simultaneous connections work independently
- [ ] Connection cleanup on browser close/tab switch
