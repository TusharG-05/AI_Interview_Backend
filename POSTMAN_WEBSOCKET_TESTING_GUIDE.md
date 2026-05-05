# Postman WebSocket Testing Guide - Step by Step

## Prerequisites
- Postman installed (download from https://www.postman.com/downloads/)
- Backend server running on `http://127.0.0.1:8000`
- Admin user created (email: `admin@test.com`, password: `admin123`)

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

In the form-data table, add these fields:

| Key | Value |
|-----|-------|
| email | admin@test.com |
| password | admin123 |

### 1.3 Send Request
- Click **Send** button
- Look at response (bottom panel)
- Find the line that says:
```json
"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImV4cCI6..."
```

### 1.4 Copy Token
- **Click and select** the entire token value (everything between the quotes after `"access_token": "`)
- **Ctrl+C** to copy
- **Paste it somewhere temporarily** (Notepad) to keep it safe

**Example token (yours will be different):**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImV4cCI6MTc3ODA2NzM5N30.d3ZiMDgMB4hf3ttm2j5cnLbsBRLlfLTXYLIDfgo-0CE
```

---

## STEP 2: Test Minimal WebSocket (No Auth - For Verification)

### 2.1 Create New WebSocket Request
- Click **"+"** button again for new tab
- **Method:** Change to `WebSocket`
  - Click where it says "GET" → scroll down → select **WebSocket**

### 2.2 Enter URL
**URL:** Copy this exactly:
```
ws://127.0.0.1:8000/api/test-ws
```

### 2.3 Connect
- Click **Connect** button (bottom right)
- You should see **"WebSocket connected"** message
- Status indicator changes to green
- You'll receive message:
```json
{"status": "connected", "message": "Test WS working!"}
```

✅ **If you see this, WebSockets are working!**

### 2.4 Disconnect
- Click **Disconnect** button
- Tab closes connection

---

## STEP 3: Test Admin Dashboard WebSocket (With Authentication)

### 3.1 Create New WebSocket Request
- Click **"+"** button for another new tab
- **Method:** Select **WebSocket**

### 3.2 Enter URL with Token
**URL structure:**
```
ws://127.0.0.1:8000/api/dashboard/ws?token=YOUR_TOKEN_HERE
```

**Example with actual token:**
```
ws://127.0.0.1:8000/api/dashboard/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkB0ZXN0LmNvbSIsImV4cCI6MTc3ODA2NzM5N30.d3ZiMDgMB4hf3ttm2j5cnLbsBRLlfLTXYLIDfgo-0CE
```

**How to build your URL:**
1. Start with: `ws://127.0.0.1:8000/api/dashboard/ws?token=`
2. At the end, paste your token from Step 1.4

### 3.3 Connect
- Click **Connect** button
- Status shows **"WebSocket connected"** in green
- Connection remains open, waiting for events

✅ **If you see green "connected" status, authentication is working!**

### 3.4 Keep Connection Open
- Leave this tab open
- This is your admin dashboard listening for real-time events
- Any events from the system will appear here (violations, interview status changes, etc.)

---

## STEP 4: Trigger Test Events (Optional - To See Real Data)

While the admin WebSocket is connected and open (from Step 3.3):

### 4.1 Start an Interview (Creates Events)
- Open new tab
- **Method:** POST
- **URL:**
```
http://localhost:8000/api/admin/interviews/schedule
```

- **Headers:** Click **Headers** tab
  - Key: `Authorization`
  - Value: `Bearer YOUR_TOKEN_HERE`
  
  Replace `YOUR_TOKEN_HERE` with your actual token from Step 1.4

- **Body:** Click **Body** → **raw** → **JSON**
  
Copy and paste:
```json
{
  "candidate_id": 83,
  "team_id": 39,
  "paper_id": 53,
  "coding_paper_id": 32,
  "interview_round": "ROUND_1",
  "schedule_time": "2026-05-06T18:00:00Z",
  "duration_minutes": 30,
  "max_questions": 2,
  "allow_copy_paste": false,
  "allow_question_navigate": true,
  "allow_proctoring": true
}
```

- Click **Send**

### 4.2 Watch Admin Dashboard
- Click back on the **admin dashboard WebSocket tab** (Step 3)
- In the message area, you should see events appearing like:
```json
{
  "event_type": "interview_started",
  "interview_id": 123,
  "data": {
    "candidate_email": "candidate@test.com",
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

## STEP 5: Test Event Broadcasting (Advanced)

### 5.1 Open Two Admin Connections
1. Create **Tab A**: WebSocket connection (Step 3)
2. Create **Tab B**: Another WebSocket connection with same URL
3. Both show "connected"

### 5.2 Trigger Event from Another Tab
- Create **Tab C**: POST request to start interview (Step 4.1)
- Send the POST request

### 5.3 Observe Both Tabs
- **Tab A** and **Tab B** both receive the same event
- Proves broadcasting is working to multiple admins

---

## STEP 6: Test with Invalid Token

### 6.1 Create Bad Token URL
- New WebSocket tab
- **URL:**
```
ws://127.0.0.1:8000/api/dashboard/ws?token=invalid_token_12345
```

### 6.2 Connect
- Click **Connect**
- Connection is **rejected immediately**
- Error message appears in red
- This confirms authentication is working

---

## STEP 7: Test Without Token

### 7.1 Create URL Without Token
- New WebSocket tab
- **URL:**
```
ws://127.0.0.1:8000/api/dashboard/ws
```
(Notice: no `?token=` at end)

### 7.2 Connect
- Click **Connect**
- Connection **rejected**
- Error: "Token missing"
- ✅ Proves token is required

---

## Quick Reference - URLs to Copy

| Test | URL |
|------|-----|
| **Login** (POST HTTP) | `http://127.0.0.1:8000/api/auth/login` |
| **Test WS** (No Auth) | `ws://127.0.0.1:8000/api/test-ws` |
| **Admin Dashboard WS** | `ws://127.0.0.1:8000/api/dashboard/ws?token=YOUR_TOKEN` |
| **Invalid Token Test** | `ws://127.0.0.1:8000/api/dashboard/ws?token=invalid` |
| **No Token Test** | `ws://127.0.0.1:8000/api/dashboard/ws` |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Check if server is running on port 8000 |
| "Token missing" error | Make sure you added `?token=YOUR_TOKEN` to URL |
| "Invalid token" error | Token expired or incorrect - get new one from login |
| Connection closes immediately | Token is invalid or user is not admin role |
| Can't change method to WebSocket | Make sure Postman version supports WebSocket (v10.0+) |

---

## Expected Responses

### Test WS Response (Step 2.3)
```json
{
  "status": "connected",
  "message": "Test WS working!"
}
```

### Admin Dashboard Events (Step 4.2)
```json
{
  "event_type": "interview_started",
  "interview_id": 123,
  "data": {
    "candidate_email": "candidate@test.com",
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

## Pro Tips

1. **Copy URL to Notepad First**: If complex URL, paste in Notepad to verify before copying to Postman
2. **Save Requests**: After creating requests, click **Save** button - name them for reuse
3. **Create Collection**: Group all WebSocket tests in a Collection for organized testing
4. **Check Server Logs**: Look at server terminal to see debug messages with emojis (🔍✅❌👋)
5. **Keep Token Tab Open**: After login, don't close the tab - easy to get token again if needed

---

## Full Workflow Example

```
1. POST http://127.0.0.1:8000/api/auth/login
   → Get token

2. WebSocket ws://127.0.0.1:8000/api/test-ws
   → Verify basic connectivity

3. WebSocket ws://127.0.0.1:8000/api/dashboard/ws?token=ABC123...
   → Connect admin dashboard (keep open)

4. POST http://127.0.0.1:8000/api/admin/interviews
   → Create interview event

5. Watch Step 3 tab
   → See events appear in real-time
```

---

## Questions?

Check server logs in terminal for detailed debug information. All WebSocket auth flows log with emoji indicators:
- 🔍 = Checking something
- ✅ = Success
- ❌ = Error
- 👋 = Disconnect
