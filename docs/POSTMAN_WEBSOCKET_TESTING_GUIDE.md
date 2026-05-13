# Postman WebSocket Testing Guide - Step by Step

## Prerequisites
- Postman installed (download from https://www.postman.com/downloads/)
- Backend server running on `http://127.0.0.1:8000`
- Admin user created (email: `admin@test.com`, password: `admin123`)
- Candidate user created (email: `candidate@test.com`, password: `candidate123`)

---

## STEP 1: Get JWT Token (HTTP Request)

### 1.1 Open Postman
- Launch Postman application
- Click **"+"** button to create a new request tab

### 1.2 Set Up Login Request
In the new tab:

**Method:** Change from GET to `POST`

**URL:** Copy this exactly:
```
http://127.0.0.1:8000/api/auth/login
```

**Body:** Click **Body** tab → Select **form-data** radio button

**For Admin:**
- email: `admin@test.com`
- password: `admin123`

**For Candidate:**
- email: `candidate@test.com`
- password: `candidate123`

### 1.3 Send Request & Copy Token
- Click **Send**
- Copy the `access_token` value from the response.

---

## STEP 2: Test Admin Dashboard WebSocket (Listener)

### 2.1 Create New WebSocket Request
- Click **"+"** button → Select **WebSocket**

### 2.2 Enter URL with Token
**URL:**
```
ws://127.0.0.1:8000/api/admin/dashboard/ws?token=YOUR_ADMIN_TOKEN
```

### 2.3 Connect
- Click **Connect**
- Keep this tab open to see real-time events from candidates.

---

## STEP 3: Test Candidate WebSocket (Lifecycle Events)

### 3.1 Create New WebSocket Request
- Click **"+"** button → Select **WebSocket**

### 3.2 Enter URL with Token
**URL:**
```
ws://127.0.0.1:8000/ws/api/interview/YOUR_INTERVIEW_ID?token=YOUR_CANDIDATE_TOKEN
```
*(Replace `YOUR_INTERVIEW_ID` with a valid ID from your database)*

### 3.3 Connect
- Click **Connect**
- **Watch Admin Tab:** You should see `candidate_connected` event.

---

## STEP 4: Send Candidate Events

While connected as a candidate (from Step 3):

### 4.1 Login Message
In the **Message** box, set type to **JSON** and send:
```json
{
  "type": "login",
  "email": "candidate@test.com"
}
```
- **Watch Admin Tab:** You should see `candidate_logged_in` with candidate details.

### 4.2 Tab Switch Event
Send:
```json
{
  "type": "tab_switch",
  "interview_id": YOUR_INTERVIEW_ID
}
```
- **Watch Admin Tab:** You should see `violation_detected` with `violation_type: "tab_switch"`.

### 4.3 Tab Return Event
Send:
```json
{
  "type": "tab_return",
  "interview_id": YOUR_INTERVIEW_ID
}
```

### 4.4 Finish Interview
Send:
```json
{
  "type": "finish_interview",
  "interview_id": YOUR_INTERVIEW_ID
}
```
- **Candidate Tab:** You will receive `interview_finished_confirmation`.
- **Admin Tab:** You should see `interview_completed` event.

---

## Quick Reference - URLs & Payloads

| Test | URL |
|------|-----|
| **Login** (POST HTTP) | `http://127.0.0.1:8000/api/auth/login` |
| **Admin Dashboard WS** | `ws://127.0.0.1:8000/api/admin/dashboard/ws?token=TOKEN` |
| **Candidate WS** | `ws://127.0.0.1:8000/ws/api/interview/ID?token=TOKEN` |

### Candidate Payloads (JSON)

**Login:**
```json
{ "type": "login", "email": "candidate@test.com" }
```

**Tab Switch:**
```json
{ "type": "tab_switch", "interview_id": 123 }
```

**Finish Interview:**
```json
{ "type": "finish_interview", "interview_id": 123 }
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "404 Not Found" | Check if you included `/api/admin` or `/ws` prefix correctly |
| "Token missing" | Ensure `?token=` is at the end of the URL |
| No events in Admin | Make sure you are using the SAME `interview_id` in both tabs |
| Handshake fails | Check server logs; token might be expired or user role is wrong |

---

## Pro Tips
1. **Open two Postman windows** or side-by-side tabs to watch Admin and Candidate simultaneously.
2. **Check Server Logs:** Look for 🔍✅❌👋 emojis in the terminal for quick status checks.
3. **Save your requests** in a Postman Collection named "AI Interview WebSockets".
 Success
- ❌ = Error
- 👋 = Disconnect
