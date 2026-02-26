#!/bin/bash
BASE_URL="https://ichigo253-ai-interview-backend.hf.space/api"
TOKEN=$(cat .admin_token)

echo "--- VERIFYING HF API ---"

# 1. List Papers
echo "Step 1: Listing Papers..."
PAPERS=$(curl -s -X GET "$BASE_URL/admin/papers" -H "Authorization: Bearer $TOKEN")
if [[ $PAPERS == *"["* ]]; then
    echo "✅ Successfully listed papers."
    # Get first paper ID
    PAPER_ID=$(echo $PAPERS | grep -oP '"id":\K[0-9]+' | head -1)
    echo "Paper ID: $PAPER_ID"
else
    echo "❌ Failed to list papers."
    echo "Response: $PAPERS"
    exit 1
fi

# 2. List Candidates
echo "Step 2: Listing Candidates..."
CANDIDATES=$(curl -s -X GET "$BASE_URL/admin/candidates" -H "Authorization: Bearer $TOKEN")
if [[ $CANDIDATES == *"["* ]]; then
    echo "✅ Successfully listed candidates."
    # Get first candidate ID
    CANDIDATE_ID=$(echo $CANDIDATES | grep -oP '"id":\K[0-9]+' | head -1)
    echo "Candidate ID: $CANDIDATE_ID"
else
    echo "❌ Failed to list candidates."
    echo "Response: $CANDIDATES"
    exit 1
fi

# 3. Schedule Interview
echo "Step 3: Scheduling Interview..."
SCHEDULE_DATA="{\"paper_id\": $PAPER_ID, \"candidate_id\": $CANDIDATE_ID, \"schedule_time\": \"2026-12-31T23:59:59Z\", \"duration_minutes\": 60}"
echo "Sending data: $SCHEDULE_DATA"
SCHEDULE_RES=$(curl -s -X POST "$BASE_URL/admin/interviews/schedule" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$SCHEDULE_DATA")

echo "Schedule Response: $SCHEDULE_RES"

if [[ $SCHEDULE_RES == *"access_token"* ]]; then
    echo "✅ SCHEDULE INTERVIEW SUCCESSFUL!"
    TOKEN=$(echo $SCHEDULE_RES | grep -oP '"access_token":"\K[^"]+' | head -n 1)
    echo "Interview Token: $TOKEN"
else
    echo "❌ SCHEDULE INTERVIEW FAILED!"
fi
