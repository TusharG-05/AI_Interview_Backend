# WebSocket Architecture - Real-Time Interview Monitoring

## Overview

The WebSocket implementation provides real-time streaming of interview events to both candidates and admin dashboards using an event-driven architecture.

## Architecture Components

### 1. WebSocket Manager ([app/services/websocket_manager.py](app/services/websocket_manager.py))

Centralized connection management with two separate connection pools:

```python
class WebSocketManager:
    candidate_connections: Dict[int, List[WebSocket]]      # Per-interview candidate streams
    admin_dashboard_connections: Dict[int, List[WebSocket]]  # Per-interview admin monitoring
```

**Key Methods:**
- `connect_candidate(websocket, interview_id)` - Register candidate connection
- `disconnect_candidate(websocket, interview_id)` - Clean up candidate connection
- `connect_admin_dashboard(websocket, interview_id)` - Register admin connection
- `disconnect_admin_dashboard(websocket, interview_id)` - Clean up admin connection
- `broadcast_to_candidate(interview_id, event)` - Send to specific interview's candidates
- `broadcast_to_admin_dashboard(interview_id, event)` - Send to specific interview's admins

### 2. WebSocket Endpoints ([app/routers/websocket.py](app/routers/websocket.py))

#### Candidate Violation Stream
```
GET /ws/api/interview/{interview_id}?token=<access_token>
```

**Purpose:** Real-time violation alerts for candidates

**Events Sent:**
- `ViolationEvent`: Tab switch, face detection, wrong candidate alerts
- `AdminDashboardEvent (interview_suspended)`: When suspension threshold reached

**Example:**
```json
{
  "event_type": "violation",
  "interview_id": 123,
  "violation_type": "tab_switch",
  "timestamp": "2025-04-22T10:30:00Z",
  "details": "Tab switch detected"
}
```

#### Admin Dashboard Stream
```
GET /ws/api/dashboard/{interview_id}?token=<admin_token>
```

**Purpose:** Real-time monitoring of interview activity

**Events Sent:**
- `ViolationEvent`: All violations with real-time updates
- `AdminDashboardEvent`:
  - `interview_started`: Interview transitioned to LIVE
  - `interview_suspended`: Violation threshold exceeded
  - `interview_completed`: Interview finished with result
  - `interview_expired`: Interview time expired

**Examples:**

Interview Started:
```json
{
  "event_type": "interview_started",
  "interview_id": 123,
  "data": {},
  "timestamp": "2025-04-22T10:15:00Z"
}
```

Violation:
```json
{
  "event_type": "violation",
  "interview_id": 123,
  "violation_type": "multiple_faces",
  "timestamp": "2025-04-22T10:25:00Z",
  "details": "Multiple faces detected in frame"
}
```

Interview Suspended:
```json
{
  "event_type": "interview_suspended",
  "interview_id": 123,
  "data": {
    "interview_procetering_event": "tab_switch",
    "tab_switch_count": 5
  },
  "timestamp": "2025-04-22T10:30:00Z"
}
```

Interview Completed:
```json
{
  "event_type": "interview_completed",
  "interview_id": 123,
  "data": {
    "result_status": "Pass"
  },
  "timestamp": "2025-04-22T11:30:00Z"
}
```

### 3. Event Schemas ([app/schemas/websocket/events.py](app/schemas/websocket/events.py))

#### ViolationEvent
Represents any proctoring violation (candidates + admin dashboards)

```python
class ViolationEvent(BaseModel):
    event_type: str = "violation"
    interview_id: int
    violation_type: str  # tab_switch, multiple_faces, no_face, wrong_candidate
    details: Optional[str]
    timestamp: datetime
```

#### AdminDashboardEvent
Major interview lifecycle events (admin dashboards only)

```python
class AdminDashboardEvent(BaseModel):
    event_type: Literal["interview_started", "interview_suspended", 
                       "interview_completed", "interview_expired"]
    interview_id: int
    data: Dict[str, Any]  # Event-specific data
    timestamp: Optional[datetime]
```

## Broadcasting Flow

### Event-Driven Model (Option B)

Broadcasts are triggered only when database state changes or violations occur:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Status Manager                               │
│                  (app/services/status_manager.py)               │
└─────────────────────────────────────────────────────────────────┘
              ↓              ↓              ↓              ↓
         Violation      Interview       Completion      Expiration
         Detection       Started        Detection       Detection
              ↓              ↓              ↓              ↓
    ┌─────────────────────────────────────────────────────────────┐
    │           WebSocket Manager (manager.py)                    │
    │         (Connection tracking & broadcasting)                │
    └─────────────────────────────────────────────────────────────┘
         ↙ broadcast_to_candidate          ↙ broadcast_to_admin_dashboard
    ┌──────────────────────┐          ┌──────────────────────┐
    │   Candidate Stream   │          │  Admin Dashboard     │
    │  /ws/api/interview/  │          │  /ws/api/dashboard/  │
    └──────────────────────┘          └──────────────────────┘
```

### Violation Reporting (Option A - Individual Events)

Each violation triggers an immediate broadcast:

```
1. Violation detected in status_manager.add_violation()
   ↓
2. Event saved to ProctoringEvent table
   ↓
3. _broadcast_violation_event(interview_id, event_type, details)
   ├─ Candidate WebSocket: Sends real-time alert
   └─ Admin Dashboard: Sends violation with context
   ↓
4. Check if warning threshold exceeded
   ↓
5. If suspended: _broadcast_interview_suspended_event()
   └─ Admin Dashboard: Sends suspension with violation count
```

## Integration Points

### 1. Violation Broadcasting

**File:** [app/services/status_manager.py](app/services/status_manager.py#L122)

When `add_violation()` is called:
```python
# Broadcast violation to candidate and admin
_fire_async_broadcast(
    _broadcast_violation_event(
        interview_session.id,
        event_type,
        details,
        tab_switch_count=...
    )
)

# Broadcast suspension if threshold exceeded
if interview_session.is_suspended and event.triggered_warning:
    _fire_async_broadcast(
        _broadcast_interview_suspended_event(
            interview_session.id,
            event_type,
            interview_session.warning_count
        )
    )
```

### 2. Interview Started Broadcast

**File:** [app/routers/interview.py](app/routers/interview.py#L792)

When interview transitions from SCHEDULED to LIVE:
```python
if session.status == InterviewStatus.SCHEDULED:
    session.status = InterviewStatus.LIVE
    session.start_time = datetime.now(timezone.utc)
    
    # Broadcast interview started event to admin dashboard
    _fire_async_broadcast(_broadcast_interview_started_event(interview_id))
```

### 3. Completion/Expiration Broadcasting

**File:** [app/services/status_manager.py](app/services/status_manager.py#L80)

In `record_status_change()`:
```python
# Broadcast to Admin Dashboard for major status changes
if new_status == CandidateStatus.INTERVIEW_COMPLETED:
    result_status = "Pass" if interview_session.result else "Fail"
    _fire_async_broadcast(
        _broadcast_interview_completed_event(interview_session.id, result_status)
    )
elif new_status == CandidateStatus.INTERVIEW_EXPIRED:
    _fire_async_broadcast(
        _broadcast_interview_expired_event(interview_session.id)
    )
```

## Implementation Details

### Non-Blocking Broadcasting

All broadcasts use `_fire_async_broadcast()` to avoid blocking the main request thread:

```python
def _fire_async_broadcast(coro):
    """Fire and forget async broadcast (non-blocking)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule broadcast without waiting
            asyncio.run_coroutine_threadsafe(coro, loop)
        else:
            asyncio.run(coro)
    except Exception as e:
        logger.error(f"Failed to fire async broadcast: {e}")
```

### Connection Management

Connections are maintained in dictionaries keyed by interview_id:

```python
# For candidate violations
candidate_connections: Dict[int, List[WebSocket]]
# Multiple candidates can connect for same interview

# For admin dashboard
admin_dashboard_connections: Dict[int, List[WebSocket]]
# Multiple admins can monitor same interview
```

### Error Handling

Failed broadcasts are caught and logged without disrupting the application:

```python
async def broadcast_to_candidate(self, interview_id: int, event: dict):
    if interview_id not in self.candidate_connections:
        return
    
    for connection in self.candidate_connections[interview_id][:]:
        try:
            await connection.send_json(event)
        except Exception as e:
            logger.error(f"WS Error: {e}")
            # Automatically disconnect on error
            self.disconnect_candidate(connection, interview_id)
```

## Client Implementation Examples

### JavaScript - Candidate Client
```javascript
const ws = new WebSocket(
  `wss://api.example.com/ws/api/interview/123?token=candidate_token`
);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.event_type === 'violation') {
    showAlert(`⚠️ ${message.violation_type}: ${message.details}`);
  } else if (message.event_type === 'interview_suspended') {
    showAlert('❌ Interview suspended due to violation');
  }
};
```

### JavaScript - Admin Dashboard Client
```javascript
const ws = new WebSocket(
  `wss://api.example.com/ws/api/dashboard/123?token=admin_token`
);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.event_type) {
    case 'interview_started':
      updateStatus('🟢 LIVE');
      startTimer();
      break;
    case 'violation':
      addViolationLog(message);
      incrementViolationCount();
      break;
    case 'interview_suspended':
      updateStatus('🟠 SUSPENDED');
      markViolationReason(message.data.interview_procetering_event);
      break;
    case 'interview_completed':
      updateStatus(`✅ ${message.data.result_status}`);
      break;
  }
};
```

## Security Considerations

### Authentication (TODO)

Currently endpoints accept a `token` query parameter but don't validate it. Implement:

```python
# In websocket.py
async def validate_access_token(token: str) -> int:
    """Validate candidate token and return interview_id"""
    # Decode JWT, verify signature, return associated interview_id
    pass

async def validate_admin_token(token: str) -> int:
    """Validate admin token and return admin_id"""
    # Decode JWT, verify signature, verify admin permissions
    pass

# Then in endpoints:
candidate = await validate_access_token(token)
admin = await validate_admin_token(token)
```

### Connection Limits

Add rate limiting to prevent abuse:
- Max connections per interview: 5
- Max admin connections: 1 per admin
- Connection timeout: 30 minutes idle

### Data Privacy

Candidate WebSocket does NOT receive:
- Answer submission data
- Other candidates' information
- Result scores or evaluations

Admin WebSocket receives all events but should be authenticated.

## Monitoring & Debugging

### Connection Tracking
```python
# Check active connections
manager.has_admin_connections(interview_id)
manager.get_admin_connection_count(interview_id)
```

### Logging
All events are logged for debugging:
```
WS: Candidate connected to Interview 123
Event broadcast to admin dashboard for interview 123: violation
Violation event broadcast: tab_switch for interview 123
WS: Admin Dashboard disconnected from Interview 123
```

## Performance Notes

- **Scalability**: Connection manager uses in-memory dictionaries; for distributed systems, consider Redis
- **Throughput**: Each event is sent individually (per-violation); no batching
- **Latency**: Minimal - events sent immediately upon broadcast call
- **Resource Usage**: One WebSocket per connected client; 2 per monitoring interview

## Future Enhancements

1. **Reconnection Logic**: Auto-reconnect on network failure
2. **Message Queuing**: Queue events during client disconnection
3. **Event Filtering**: Allow clients to subscribe to specific event types
4. **Compression**: Compress large event payloads
5. **Rate Limiting**: Throttle high-frequency events
6. **Metrics**: Track broadcast latency, connection duration
7. **Redis Integration**: Support multiple server instances
8. **Heartbeat**: Periodic ping/pong to detect stale connections
