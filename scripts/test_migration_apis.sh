#!/bin/bash
# Comprehensive API test script for migration verification
set -e

BASE="http://localhost:8000/api"
PASS=0
FAIL=0

check() {
    local name="$1"
    local code="$2"
    local body="$3"
    
    if echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('status_code',0) in [200,201] or d.get('access_token') else 1)" 2>/dev/null; then
        echo "✅ $name (HTTP $code)"
        PASS=$((PASS+1))
    else
        echo "❌ $name (HTTP $code)"
        echo "   Response: $(echo "$body" | head -c 200)"
        FAIL=$((FAIL+1))
    fi
}

echo "=== 1. AUTH: Login ==="
RESP=$(curl -s -w "\n%{http_code}" --max-time 10 -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}')
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "POST /auth/login" "$CODE" "$BODY"

TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")
if [ -z "$TOKEN" ]; then
    echo "FATAL: Cannot get auth token. Aborting."
    exit 1
fi
AUTH="Authorization: Bearer $TOKEN"

echo ""
echo "=== 2. AUTH: Get Me ==="
RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/auth/me" -H "$AUTH")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "GET /auth/me" "$CODE" "$BODY"

echo ""
echo "=== 3. PAPERS: List ==="
RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/admin/papers" -H "$AUTH")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "GET /admin/papers" "$CODE" "$BODY"
PAPER_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['id'] if d else '')" 2>/dev/null || echo "")

echo ""
echo "=== 4. PAPERS: Create ==="
RESP=$(curl -s -w "\n%{http_code}" --max-time 10 -X POST "$BASE/admin/papers" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"name":"Migration Test Paper","description":"Testing after migration"}')
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "POST /admin/papers" "$CODE" "$BODY"
NEW_PAPER_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

if [ -n "$NEW_PAPER_ID" ]; then
    echo ""
    echo "=== 5. PAPERS: Get by ID ==="
    RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/admin/papers/$NEW_PAPER_ID" -H "$AUTH")
    CODE=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')
    check "GET /admin/papers/$NEW_PAPER_ID" "$CODE" "$BODY"
    
    echo ""
    echo "=== 6. QUESTIONS: Add to paper ==="
    RESP=$(curl -s -w "\n%{http_code}" --max-time 10 -X POST "$BASE/admin/papers/$NEW_PAPER_ID/questions" \
      -H "$AUTH" -H "Content-Type: application/json" \
      -d '{"content":"What is Python?","topic":"Programming","difficulty":"Easy","marks":5,"response_type":"text"}')
    CODE=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')
    check "POST /admin/papers/$NEW_PAPER_ID/questions" "$CODE" "$BODY"
fi

echo ""
echo "=== 7. INTERVIEWS: List ==="
RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/admin/interviews" -H "$AUTH")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "GET /admin/interviews" "$CODE" "$BODY"

echo ""
echo "=== 8. INTERVIEWS: Live Status ==="
RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/admin/interviews/live-status" -H "$AUTH")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "GET /admin/interviews/live-status" "$CODE" "$BODY"

# Schedule interview if we have a paper with questions
if [ -n "$NEW_PAPER_ID" ]; then
    echo ""
    echo "=== 9. INTERVIEWS: Schedule ==="
    RESP=$(curl -s -w "\n%{http_code}" --max-time 30 -X POST "$BASE/admin/interviews/schedule" \
      -H "$AUTH" -H "Content-Type: application/json" \
      -d "{\"candidate_id\":4,\"paper_id\":$NEW_PAPER_ID,\"schedule_time\":\"2026-02-27T10:00:00Z\",\"duration_minutes\":60,\"max_questions\":1}")
    CODE=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')
    check "POST /admin/interviews/schedule" "$CODE" "$BODY"
    
    INTERVIEW_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['interview']['id'])" 2>/dev/null || echo "")
    ACCESS_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")
    
    # Check response does NOT contain candidate_name or admin_name
    if echo "$BODY" | grep -q '"candidate_name"'; then
        echo "   ⚠️  WARNING: Response still contains candidate_name!"
    else
        echo "   ✓ Response correctly excludes candidate_name"
    fi
    if echo "$BODY" | grep -q '"admin_name"'; then
        echo "   ⚠️  WARNING: Response still contains admin_name!"
    else
        echo "   ✓ Response correctly excludes admin_name"
    fi
    
    if [ -n "$INTERVIEW_ID" ]; then
        echo ""
        echo "=== 10. INTERVIEWS: Get by ID ==="
        RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/admin/interviews/$INTERVIEW_ID" -H "$AUTH")
        CODE=$(echo "$RESP" | tail -1)
        BODY=$(echo "$RESP" | sed '$d')
        check "GET /admin/interviews/$INTERVIEW_ID" "$CODE" "$BODY"
    fi
    
    if [ -n "$ACCESS_TOKEN" ]; then
        echo ""
        echo "=== 11. INTERVIEW ACCESS: Candidate side ==="
        RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/interview/access/$ACCESS_TOKEN")
        CODE=$(echo "$RESP" | tail -1)
        BODY=$(echo "$RESP" | sed '$d')
        check "GET /interview/access/$ACCESS_TOKEN" "$CODE" "$BODY"
    fi
fi

echo ""
echo "=== 12. RESULTS: List All ==="
RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/admin/results" -H "$AUTH")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "GET /admin/results" "$CODE" "$BODY"

# Get a result ID if any exist
RESULT_INTERVIEW_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['interview']['id'] if d else '')" 2>/dev/null || echo "")
if [ -n "$RESULT_INTERVIEW_ID" ]; then
    echo ""
    echo "=== 13. RESULTS: Get by Interview ID ==="
    RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/admin/results/$RESULT_INTERVIEW_ID" -H "$AUTH")
    CODE=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')
    check "GET /admin/results/$RESULT_INTERVIEW_ID" "$CODE" "$BODY"
fi

echo ""
echo "=== 14. CANDIDATES: List ==="
RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/admin/candidates" -H "$AUTH")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "GET /admin/candidates" "$CODE" "$BODY"

echo ""
echo "=== 15. USERS: List ==="
RESP=$(curl -s -w "\n%{http_code}" --max-time 10 "$BASE/admin/users" -H "$AUTH")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "GET /admin/users" "$CODE" "$BODY"

echo ""
echo "================================="
echo "RESULTS: $PASS passed, $FAIL failed"
echo "================================="
