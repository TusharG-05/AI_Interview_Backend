#!/bin/bash

# Configuration
BASE_URL=${1:-"https://ichigo253-ai-interview-backend.hf.space/api"}
TOKEN_FILE=".candidate_token"

if [ ! -f "$TOKEN_FILE" ]; then
  echo "❌ Error: .candidate_token not found. Run auth_tests.sh first."
  exit 1
fi

TOKEN=$(cat $TOKEN_FILE)

echo "--- CANDIDATE API TESTS ---"

# 1. History
echo "Testing History..."
HISTORY_RES=$(curl -s -X GET "$BASE_URL/candidate/history" -H "Authorization: Bearer $TOKEN")
if [[ $HISTORY_RES == *"\"success\":true"* ]]; then
  echo "✅ Candidate History Successful"
else
  echo "❌ Candidate History Failed"
  echo "Response: $HISTORY_RES"
fi

# 2. Interviews
echo "Testing Interviews..."
INTERVIEWS_RES=$(curl -s -X GET "$BASE_URL/candidate/interviews" -H "Authorization: Bearer $TOKEN")
if [[ $INTERVIEWS_RES == *"\"success\":true"* ]]; then
  echo "✅ Candidate Interviews Successful"
else
  echo "❌ Candidate Interviews Failed"
  echo "Response: $INTERVIEWS_RES"
fi
