#!/bin/bash

# Configuration
BASE_URL=${1:-"https://ichigo253-ai-interview-backend.hf.space/api"}
ADMIN_EMAIL="admin@test.com"
ADMIN_PASS="admin123"
TOKEN_FILE=".admin_token"

echo "--- AUTH API TESTS ---"

# 1. Login (Admin)
echo "Testing Admin Login..."
LOGIN_RES=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}")

TOKEN=$(echo $LOGIN_RES | grep -oP '"access_token":"\K[^"]+')

if [ -z "$TOKEN" ]; then
  echo "❌ Admin Login Failed"
else
  echo "✅ Admin Login Successful"
  echo $TOKEN > $TOKEN_FILE
fi

# 2. Login (Candidate)
echo "Testing Candidate Login..."
C_EMAIL="sakshamc1@test.com"
C_PASS="candidate123"
C_TOKEN_FILE=".candidate_token"

C_LOGIN_RES=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$C_EMAIL\",\"password\":\"$C_PASS\"}")

C_TOKEN=$(echo $C_LOGIN_RES | grep -oP '"access_token":"\K[^"]+')

if [ -z "$C_TOKEN" ]; then
  echo "❌ Candidate Login Failed"
else
  echo "✅ Candidate Login Successful"
  echo $C_TOKEN > $C_TOKEN_FILE
fi

# 2. Get Me
echo "Testing /auth/me..."
ME_RES=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN")

if [[ $ME_RES == *"\"email\":\"$ADMIN_EMAIL\""* ]]; then
  echo "✅ Auth Me Successful"
else
  echo "❌ Auth Me Failed"
  echo "Response: $ME_RES"
fi

# 3. Logout (Optional)
# echo "Testing Logout..."
# LOGOUT_RES=$(curl -s -X POST "$BASE_URL/auth/logout" -H "Authorization: Bearer $TOKEN")
# ...
