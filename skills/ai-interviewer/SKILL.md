---
name: AI Interviewer
description: Conducts AI-driven interviews and manages candidate data using the Interview Backend API.
requirements:
  binaries:
    - curl
    - jq
  environment_variables:
    - INTERVIEW_API_URL
    - CANDIDATE_AUTH_TOKEN
---

# AI Interviewer Skill

This skill allows the OpenClaw agent to interact with the AI Interviewer Backend.

## Workflow

### 1. View Interview History
To see your past interviews and scores:
```bash
curl -X GET "$INTERVIEW_API_URL/api/candidate/history" \
     -H "Authorization: Bearer $CANDIDATE_AUTH_TOKEN" | jq .
```

### 2. Access an Interview
To validate an interview link and check if it's ready:
```bash
curl -X GET "$INTERVIEW_API_URL/api/interview/access/<access_token>" | jq .
```

### 3. Start an Interview Session
Once accessed, start the session (set status to LIVE):
```bash
curl -X POST "$INTERVIEW_API_URL/api/interview/start-session/<interview_id>" \
     -H "Content-Type: multipart/form-data" | jq .
```

### 4. Conduct the Interview
Cycle through questions until finished:

**Get Next Question:**
```bash
curl -X GET "$INTERVIEW_API_URL/api/interview/next-question/<interview_id>" | jq .
```

**Submit Text Answer:**
```bash
curl -X POST "$INTERVIEW_API_URL/api/interview/submit-answer-text" \
     -F "interview_id=<interview_id>" \
     -F "question_id=<question_id>" \
     -F "answer_text=<your_answer>" | jq .
```

### 5. Finish and Process
After all questions are answered, trigger background evaluation:
```bash
curl -X POST "$INTERVIEW_API_URL/api/interview/finish/<interview_id>" | jq .
```

## Tips
- Always check the `status` field in the response.
- If a question returns `audio_url`, you can download it using `curl -O`.
- The `finish` endpoint triggers an asynchronous process; check `history` later for the final score.
