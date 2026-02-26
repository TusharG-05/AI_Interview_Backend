#!/bin/bash

# Configuration
BASE_URL=${1:-"https://ichigo253-ai-interview-backend.hf.space/api"}

echo "#######################################"
echo "🚀 STARTING COMPREHENSIVE API AUDIT 🚀"
echo "Target: $BASE_URL"
echo "#######################################"

# 1. Auth Tests (Required for tokens)
bash auth_tests.sh "$BASE_URL"
if [ $? -ne 0 ]; then
  echo "❌ Auth tests failed. Aborting full audit."
  exit 1
fi

# 2. Admin Tests
bash admin_tests.sh "$BASE_URL"

# 3. Candidate Tests
bash candidate_tests.sh "$BASE_URL"

# 4. Interview Flow Tests
bash interview_flow.sh "$BASE_URL"

echo "#######################################"
echo "✅ API AUDIT COMPLETE"
echo "#######################################"
