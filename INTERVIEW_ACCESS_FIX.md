# Fix: Interview Access Endpoint 500 Error

## Issue
POST `/api/admin/interviews/schedule` works ✓  
GET `/api/interview/access/{token}` returns **500 Internal Server Error** ❌

## Root Cause
**AttributeError:** Trying to access non-existent field `company_name` on User object.

Code was trying to do:
```python
admin_data = {
    "id": session.admin.id,
    "email": session.admin.email,
    "full_name": session.admin.full_name,
    "company_name": session.admin.company_name  # ❌ FIELD DOESN'T EXIST
}
```

But User model only has: `id`, `email`, `full_name`, `password_hash`, `role`, etc.

## Fix Applied

**File:** [app/routers/interview.py](app/routers/interview.py#L60-L64)

**Removed non-existent field:**
```python
# BEFORE (broken):
admin_data = {
    "id": session.admin.id,
    "email": session.admin.email,
    "full_name": session.admin.full_name,
    "company_name": session.admin.company_name  # ❌ Deleted
}

# AFTER (fixed):
admin_data = {
    "id": session.admin.id,
    "email": session.admin.email,
    "full_name": session.admin.full_name
}
```

**Also removed debug statement:**
```python
# BEFORE:
).first()

print(session)  # ❌ Debug print - removed

if not session:

# AFTER:
).first()

if not session:
```

## Result
✅ `/api/interview/access/{token}` now returns 200 OK  
✅ Returns valid InterviewAccessResponse  
✅ Candidate can access interview link  

## Testing

**Test endpoint with curl:**
```bash
curl -X 'GET' \
  'https://ichigo253-ai-interview-backend.hf.space/api/interview/access/838272f8b4784fb2b7d82014f839e2ad' \
  -H 'accept: application/json'
```

**Expected response (200 OK):**
```json
{
  "status_code": 200,
  "data": {
    "interview_id": 59,
    "candidate": {...},
    "admin": {...},
    "paper": {...},
    "invite_link": "...",
    "message": "START or WAIT",
    ...
  },
  "success": true
}
```

---

*Fixed: Feb 24, 2026*
