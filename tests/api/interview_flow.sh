#!/bin/bash

# Configuration
BASE_URL=${1:-"https://ichigo253-ai-interview-backend.hf.space/api"}
TOKEN_FILE=".interview_token"

if [ ! -f "$TOKEN_FILE" ]; then
  echo "❌ Error: .interview_token not found. Run admin_tests.sh with scheduling enabled."
  exit 1
fi

TOKEN=$(cat $TOKEN_FILE)

echo "--- INTERVIEW FLOW TESTS ---"

# 1. Access Interview
echo "Testing Access Interview..."
ACCESS_RES=$(curl -s -X GET "$BASE_URL/interview/access/$TOKEN")
if [[ $ACCESS_RES == *"\"success\":true"* ]]; then
  echo "✅ Access Interview Successful"
  INTERVIEW_ID=$(echo $ACCESS_RES | grep -oP '"interview_id":\K[0-9]+')
else
  echo "❌ Access Interview Failed"
  echo "Response: $ACCESS_RES"
  exit 1
fi

# 2. Get Next Question
echo "Testing Next Question..."
NEXT_Q_RES=$(curl -s -X GET "$BASE_URL/interview/next-question/$INTERVIEW_ID")
if [[ $NEXT_Q_RES == *"\"success\":true"* ]]; then
  echo "✅ Get Next Question Successful"
else
  echo "❌ Get Next Question Failed"
  echo "Response: $NEXT_Q_RES"
fi

# 3. Evaluate (Small Mock)
echo "Testing Evaluate Answer (Mock)..."
EVAL_DATA="{\"question\": \"What is your experience?\", \"answer\": \"I have 5 years of experience.\"}"
EVAL_RES=$(curl -s -X POST "$BASE_URL/interview/evaluate-answer" \
  -H "Content-Type: application/json" \
  -d "$EVAL_DATA")
if [[ $EVAL_RES == *"\"success\":true"* ]]; then
  echo "✅ Evaluate Answer Successful"
else
  echo "❌ Evaluate Answer Failed"
  echo "Response: $EVAL_RES"
fi
