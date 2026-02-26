#!/bin/bash

# Configuration
API_BASE="https://ichigo253-ai-interview-backend.hf.space/api"
ADMIN_EMAIL="admin@test.com"
ADMIN_PASS="admin123"
CANDIDATE_EMAIL="tushar@chicmicstudios.in"
CANDIDATE_PASS="tushar"

echo "======================================================"
echo " Testing HF Schedule API with $CANDIDATE_EMAIL "
echo "======================================================"

# 1. Login Admin
echo -n "1. Admin Login... "
ADMIN_LOGIN_RES=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}")

ADMIN_TOKEN=$(echo $ADMIN_LOGIN_RES | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Failed to get admin token."
    echo $ADMIN_LOGIN_RES
    exit 1
fi
echo "✅ OK (Token: ${ADMIN_TOKEN:0:10}...)"

# 2. Get/Create Question Paper
echo -n "2. Create Test Paper... "
PAPER_RES=$(curl -s -X POST "$API_BASE/admin/papers" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "HF Schedule Test Paper", "duration": 30, "description": "Test paper for scheduling"}')
PAPER_ID=$(echo $PAPER_RES | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$PAPER_ID" ]; then
    echo "❌ Failed to create paper."
    echo $PAPER_RES
    exit 1
fi
echo "✅ OK (ID: $PAPER_ID)"

# Add a question
curl -s -X POST "$API_BASE/admin/papers/$PAPER_ID/questions" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Is Hugging Face working?","type": "GENERAL","marks": 10}' > /dev/null

# 3. Get/Create Candidate
echo -n "3. Create/Get Candidate $CANDIDATE_EMAIL... "
CAND_RES=$(curl -s -X POST "$API_BASE/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$CANDIDATE_EMAIL\",\"password\":\"$CANDIDATE_PASS\",\"full_name\":\"Tushar\",\"role\":\"CANDIDATE\"}")

# If email already registered, it fails with 400. Let's just lookup candidate list.
CAND_LIST=$(curl -s -X GET "$API_BASE/admin/candidates" -H "Authorization: Bearer $ADMIN_TOKEN")
CANDIDATE_ID=$(echo $CAND_LIST | grep -o "\"id\":[0-9]*,\"email\":\"$CANDIDATE_EMAIL\"" | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -z "$CANDIDATE_ID" ]; then
    echo "❌ Failed to find/create candidate."
    echo "Create Res: $CAND_RES"
    exit 1
fi
echo "✅ OK (ID: $CANDIDATE_ID)"

# 4. Schedule Interview
echo "4. Scheduling Interview... (This should trigger the email)"
SCHEDULE_TIME=$(date -u -d "+1 day" +"%Y-%m-%dT%H:00:00Z" 2>/dev/null || date -v+1d -u +"%Y-%m-%dT%H:00:00Z" 2>/dev/null || echo "2026-12-01T10:00:00Z")

SCHEDULE_RES=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_BASE/admin/interviews/schedule" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"candidate_id\":$CANDIDATE_ID,\"paper_id\":$PAPER_ID,\"schedule_time\":\"$SCHEDULE_TIME\",\"max_questions\":1}")

HTTP_STATUS=$(echo "$SCHEDULE_RES" | grep "HTTP_STATUS" | cut -d':' -f2)
BODY=$(echo "$SCHEDULE_RES" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" == "201" ]; then
    echo "✅ SUCCESS! Interview Scheduled."
    echo "$BODY" | grep -o '"invite_link":"[^"]*"' | head -1
else
    echo "❌ FAILED (HTTP $HTTP_STATUS)"
    echo "$BODY"
    exit 1
fi

echo "======================================================"
echo "Done."
