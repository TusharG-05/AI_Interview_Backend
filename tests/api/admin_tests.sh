#!/bin/bash

# Configuration
BASE_URL=${1:-"https://ichigo253-ai-interview-backend.hf.space/api"}
TOKEN_FILE=".admin_token"

if [ ! -f "$TOKEN_FILE" ]; then
  echo "❌ Error: .admin_token not found. Run auth_tests.sh first."
  exit 1
fi

TOKEN=$(cat $TOKEN_FILE)

echo "--- ADMIN API TESTS ---"

# 1. List Papers
echo "Testing List Papers..."
PAPERS_RES=$(curl -s -X GET "$BASE_URL/admin/papers" -H "Authorization: Bearer $TOKEN")
if [[ $PAPERS_RES == *"\"success\":true"* ]]; then
  echo "✅ List Papers Successful"
else
  echo "❌ List Papers Failed"
  echo "Response: $PAPERS_RES"
fi

# 2. List Interviews
echo "Testing List Interviews..."
INTERVIEWS_RES=$(curl -s -X GET "$BASE_URL/admin/interviews" -H "Authorization: Bearer $TOKEN")
if [[ $INTERVIEWS_RES == *"\"success\":true"* ]]; then
  echo "✅ List Interviews Successful"
else
  echo "❌ List Interviews Failed"
  echo "Response: $INTERVIEWS_RES"
fi

# 3. List User Results (The one that was breaking)
echo "Testing User Results..."
RESULTS_RES=$(curl -s -X GET "$BASE_URL/admin/users/results" -H "Authorization: Bearer $TOKEN")
if [[ $RESULTS_RES == *"\"success\":true"* ]]; then
  echo "✅ User Results Successful"
else
  echo "❌ User Results Failed (Still Breaking?)"
  echo "Response: $RESULTS_RES"
fi

# 4. List Candidates
echo "Testing List Candidates..."
CANDIDATES_RES=$(curl -s -X GET "$BASE_URL/admin/candidates" -H "Authorization: Bearer $TOKEN")
if [[ $CANDIDATES_RES == *"\"success\":true"* ]]; then
  echo "✅ List Candidates Successful"
else
  echo "❌ List Candidates Failed"
  echo "Response: $CANDIDATES_RES"
fi

# 5. List Questions
echo "Testing List Questions..."
QUESTIONS_RES=$(curl -s -X GET "$BASE_URL/admin/questions" -H "Authorization: Bearer $TOKEN")
if [[ $QUESTIONS_RES == *"\"success\":true"* ]]; then
  echo "✅ List Questions Successful"
else
  echo "❌ List Questions Failed"
  echo "Response: $QUESTIONS_RES"
fi

# 6. Schedule Interview (Example)
echo "Testing Schedule Interview..."
# We need a Paper ID and Candidate ID. Let's try to find them or use defaults.
PAPER_ID=$(echo $PAPERS_RES | grep -oP '"id":\K[0-9]+' | head -1)
CANDIDATE_ID=$(echo $CANDIDATES_RES | grep -oP '"id":\K[0-9]+' | head -1)

if [ -n "$PAPER_ID" ] && [ -n "$CANDIDATE_ID" ]; then
  SCHEDULE_DATA="{\"paper_id\": $PAPER_ID, \"candidate_id\": $CANDIDATE_ID, \"schedule_time\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"duration_minutes\": 60}"
  SCHEDULE_RES=$(curl -s -X POST "$BASE_URL/admin/interviews/schedule" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$SCHEDULE_DATA")
  
  INTERVIEW_TOKEN=$(echo $SCHEDULE_RES | grep -oP '"access_token":"\K[^"]+' | head -n 1)
  
  if [ -n "$INTERVIEW_TOKEN" ]; then
    echo "✅ Schedule Interview Successful (Token: $INTERVIEW_TOKEN)"
    echo $INTERVIEW_TOKEN > .interview_token
  else
    echo "❌ Schedule Interview Failed"
    echo "Response: $SCHEDULE_RES"
  fi
else
  echo "⚠️ Skipping Schedule Interview (No Paper or Candidate found)"
fi
