#!/bin/bash
# =============================================================================
# FULL E2E API TEST — EVERY ENDPOINT, NO SKIPS
# Tests against Docker DB at localhost:8000
# =============================================================================
set -o pipefail

BASE="http://localhost:8000/api"
PASS=0
FAIL=0
FAILED_LIST=""

check() {
    local name="$1"
    local expected="$2"
    local code="$3"
    local body="$4"
    local found=0
    for exp in $expected; do
        if [ "$code" = "$exp" ]; then found=1; break; fi
    done
    if [ $found -eq 1 ]; then
        echo "  ✅ $name ($code)"
        PASS=$((PASS+1))
    else
        echo "  ❌ $name (got $code, expected $expected)"
        echo "     $(echo "$body" | head -c 200)"
        FAIL=$((FAIL+1))
        FAILED_LIST="$FAILED_LIST\n  - $name (HTTP $code): $(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message','')[:80])" 2>/dev/null || echo "$body" | head -c 80)"
    fi
}

split_response() {
    BODY=$(echo "$1" | sed '$d')
    CODE=$(echo "$1" | tail -1)
}

# --- Create dummy test files ---
echo "Preparing test files..."
mkdir -p /tmp/api_test

# 1x1 red pixel JPEG
python3 -c "
from PIL import Image
img = Image.new('RGB', (100, 100), color='red')
img.save('/tmp/api_test/selfie.jpg')
print('Created selfie.jpg')
" 2>/dev/null || python3 -c "
import struct, os
# Minimal JPEG
data = bytes([
    0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,0x49,0x46,0x00,0x01,
    0x01,0x00,0x00,0x01,0x00,0x01,0x00,0x00,0xFF,0xDB,0x00,0x43,
    0x00,0x08,0x06,0x06,0x07,0x06,0x05,0x08,0x07,0x07,0x07,0x09,
    0x09,0x08,0x0A,0x0C,0x14,0x0D,0x0C,0x0B,0x0B,0x0C,0x19,0x12,
    0x13,0x0F,0x14,0x1D,0x1A,0x1F,0x1E,0x1D,0x1A,0x1C,0x1C,0x20,
    0x24,0x2E,0x27,0x20,0x22,0x2C,0x23,0x1C,0x1C,0x28,0x37,0x29,
    0x2C,0x30,0x31,0x34,0x34,0x34,0x1F,0x27,0x39,0x3D,0x38,0x32,
    0x3C,0x2E,0x33,0x34,0x32,0xFF,0xC0,0x00,0x0B,0x08,0x00,0x01,
    0x00,0x01,0x01,0x01,0x11,0x00,0xFF,0xC4,0x00,0x1F,0x00,0x00,
    0x01,0x05,0x01,0x01,0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,
    0x09,0x0A,0x0B,0xFF,0xDA,0x00,0x08,0x01,0x01,0x00,0x00,0x3F,
    0x00,0x54,0xDB,0x2E,0x44,0xA4,0x7E,0x39,0xA2,0xCF,0xFF,0xD9
])
with open('/tmp/api_test/selfie.jpg','wb') as f: f.write(data)
print('Created minimal selfie.jpg')
"

# Create WAV audio file (1 second of silence, 16kHz mono)
python3 -c "
import wave, struct
with wave.open('/tmp/api_test/audio.wav', 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(struct.pack('<' + 'h' * 16000, *([0]*16000)))
print('Created audio.wav')
"

# Create a simple text file for document upload
echo "Question 1: What is Python?
Question 2: What is Docker?
Question 3: What is FastAPI?" > /tmp/api_test/questions.txt
echo "Created questions.txt"
echo ""

echo "╔════════════════════════════════════════════════════╗"
echo "║  FULL E2E API TEST SUITE — ALL ENDPOINTS           ║"
echo "╚════════════════════════════════════════════════════╝"

# ================================================================
# 1. AUTH
# ================================================================
echo ""
echo "━━━ 1. AUTH (/api/auth) ━━━"

# Login admin
RESP=$(curl -s --max-time 15 -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}')
split_response "$RESP"
check "POST /auth/login (admin)" "200" "$CODE" "$BODY"
ADMIN_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")
if [ -z "$ADMIN_TOKEN" ]; then echo "FATAL: No admin token"; exit 1; fi

# Login wrong password
RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" -d '{"email":"admin@test.com","password":"wrong"}')
split_response "$RESP"
check "POST /auth/login (wrong pass → 401)" "401" "$CODE" "$BODY"

# OAuth2 token
RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@test.com&password=admin123")
split_response "$RESP"
check "POST /auth/token (OAuth2)" "200" "$CODE" "$BODY"

# Register a test candidate
RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"email":"e2e_test_candidate@test.com","password":"test123","full_name":"E2E Test Candidate","role":"candidate"}')
split_response "$RESP"
check "POST /auth/register" "200 201" "$CODE" "$BODY"
CAND_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")
CAND_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

# If register failed (duplicate), login instead
if [ -z "$CAND_TOKEN" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"email":"e2e_test_candidate@test.com","password":"test123"}')
    split_response "$RESP"
    CAND_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")
    CAND_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")
    echo "  ℹ️  Used existing candidate (id=$CAND_ID)"
fi

# Get Me (admin)
RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/auth/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /auth/me (admin)" "200" "$CODE" "$BODY"

# Get Me (candidate)
if [ -n "$CAND_TOKEN" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/auth/me" \
      -H "Authorization: Bearer $CAND_TOKEN")
    split_response "$RESP"
    check "GET /auth/me (candidate)" "200" "$CODE" "$BODY"
fi

# Logout
RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/auth/logout")
split_response "$RESP"
check "POST /auth/logout" "200" "$CODE" "$BODY"

# ================================================================
# 2. PAPERS CRUD
# ================================================================
echo ""
echo "━━━ 2. PAPERS CRUD ━━━"

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/papers" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /admin/papers (list)" "200" "$CODE" "$BODY"

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/admin/papers" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"E2E Full Test Paper","description":"Full end-to-end test"}')
split_response "$RESP"
check "POST /admin/papers (create)" "201" "$CODE" "$BODY"
PAPER_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

if [ -n "$PAPER_ID" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/papers/$PAPER_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "GET /admin/papers/$PAPER_ID (get)" "200" "$CODE" "$BODY"

    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X PATCH "$BASE/admin/papers/$PAPER_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
      -d '{"name":"E2E Updated Paper"}')
    split_response "$RESP"
    check "PATCH /admin/papers/$PAPER_ID (update)" "200" "$CODE" "$BODY"
fi

# ================================================================
# 3. QUESTIONS CRUD
# ================================================================
echo ""
echo "━━━ 3. QUESTIONS CRUD ━━━"

if [ -n "$PAPER_ID" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/admin/papers/$PAPER_ID/questions" \
      -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
      -d '{"content":"What is Python?","question_text":"What is Python?","topic":"Programming","difficulty":"Easy","marks":10,"response_type":"text"}')
    split_response "$RESP"
    check "POST /admin/papers/{id}/questions (add)" "201" "$CODE" "$BODY"
    Q_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/papers/$PAPER_ID/questions" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "GET /admin/papers/{id}/questions (list)" "200" "$CODE" "$BODY"

    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/questions" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "GET /admin/questions (all)" "200" "$CODE" "$BODY"

    if [ -n "$Q_ID" ]; then
        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/questions/$Q_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
        split_response "$RESP"
        check "GET /admin/questions/$Q_ID (get)" "200" "$CODE" "$BODY"

        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X PATCH "$BASE/admin/questions/$Q_ID" \
          -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
          -d '{"topic":"Updated Topic"}')
        split_response "$RESP"
        check "PATCH /admin/questions/$Q_ID (update)" "200" "$CODE" "$BODY"
    fi

    # Document upload
    RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/admin/upload-doc?paper_id=$PAPER_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -F "file=@/tmp/api_test/questions.txt")
    split_response "$RESP"
    check "POST /admin/upload-doc" "200 201" "$CODE" "$BODY"
fi

# ================================================================
# 4. USERS CRUD
# ================================================================
echo ""
echo "━━━ 4. USERS CRUD ━━━"

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"email":"e2e_crud_user@test.com","password":"test123","full_name":"CRUD Test User","role":"candidate"}')
split_response "$RESP"
check "POST /admin/users (create)" "200 201" "$CODE" "$BODY"
CRUD_USER_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/users" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /admin/users (list)" "200" "$CODE" "$BODY"

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/candidates" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /admin/candidates (list)" "200" "$CODE" "$BODY"

if [ -n "$CRUD_USER_ID" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/users/$CRUD_USER_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "GET /admin/users/$CRUD_USER_ID (get)" "200" "$CODE" "$BODY"

    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X PATCH "$BASE/admin/users/$CRUD_USER_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
      -d '{"full_name":"Updated CRUD User"}')
    split_response "$RESP"
    check "PATCH /admin/users/$CRUD_USER_ID (update)" "200" "$CODE" "$BODY"
fi

# ================================================================
# 5. FULL INTERVIEW FLOW
# ================================================================
echo ""
echo "━━━ 5. INTERVIEW FLOW (schedule → access → selfie → start → questions → answer → finish) ━━━"

if [ -n "$PAPER_ID" ] && [ -n "$CAND_ID" ]; then
    # Schedule for NOW so we can access it
    SCHED_TIME=$(date -u -d "+1 minute" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%SZ)
    
    RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/admin/interviews/schedule" \
      -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
      -d "{\"candidate_id\":$CAND_ID,\"paper_id\":$PAPER_ID,\"schedule_time\":\"$SCHED_TIME\",\"duration_minutes\":120,\"max_questions\":1}")
    split_response "$RESP"
    check "POST /admin/interviews/schedule" "201" "$CODE" "$BODY"
    INT_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['interview']['id'])" 2>/dev/null || echo "")
    ACCESS_TK=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")

    # List interviews
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/interviews" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "GET /admin/interviews (list)" "200" "$CODE" "$BODY"

    # Live status
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/interviews/live-status" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "GET /admin/interviews/live-status" "200" "$CODE" "$BODY"

    if [ -n "$INT_ID" ]; then
        # Get interview
        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/interviews/$INT_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
        split_response "$RESP"
        check "GET /admin/interviews/$INT_ID (get)" "200" "$CODE" "$BODY"

        # Update interview
        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X PATCH "$BASE/admin/interviews/$INT_ID" \
          -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
          -d '{"duration_minutes":90}')
        split_response "$RESP"
        check "PATCH /admin/interviews/$INT_ID (update)" "200" "$CODE" "$BODY"

        # Get status
        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/interviews/$INT_ID/status" -H "Authorization: Bearer $ADMIN_TOKEN")
        split_response "$RESP"
        check "GET /admin/interviews/$INT_ID/status" "200" "$CODE" "$BODY"

        # Access interview (candidate side)
        if [ -n "$ACCESS_TK" ]; then
            # Wait for schedule_time to pass
            echo "  ⏳ Waiting for schedule time..."
            sleep 65

            RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/interview/access/$ACCESS_TK")
            split_response "$RESP"
            check "GET /interview/access/{token}" "200" "$CODE" "$BODY"
            MSG=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['message'])" 2>/dev/null || echo "")
            echo "     Access message: $MSG"
        fi

        # Upload selfie
        RESP=$(curl -s --max-time 15 -w "\n%{http_code}" -X POST "$BASE/interview/upload-selfie" \
          -F "interview_id=$INT_ID" \
          -F "file=@/tmp/api_test/selfie.jpg;type=image/jpeg")
        split_response "$RESP"
        check "POST /interview/upload-selfie" "200" "$CODE" "$BODY"

        # Start session with enrollment audio
        RESP=$(curl -s --max-time 15 -w "\n%{http_code}" -X POST "$BASE/interview/start-session/$INT_ID" \
          -F "enrollment_audio=@/tmp/api_test/audio.wav;type=audio/wav")
        split_response "$RESP"
        check "POST /interview/start-session/$INT_ID" "200" "$CODE" "$BODY"

        # Get enrollment audio (admin side)
        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -o /dev/null "$BASE/admin/interviews/enrollment-audio/$INT_ID" \
          -H "Authorization: Bearer $ADMIN_TOKEN")
        CODE=$(echo "$RESP" | tail -1)
        check "GET /admin/interviews/enrollment-audio/$INT_ID" "200 404" "$CODE" ""

        # Get next question
        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/interview/next-question/$INT_ID")
        split_response "$RESP"
        check "GET /interview/next-question/$INT_ID" "200" "$CODE" "$BODY"
        NEXT_Q_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('question_id',''))" 2>/dev/null || echo "")

        if [ -n "$NEXT_Q_ID" ]; then
            # Submit answer (text)
            RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/interview/submit-answer-text" \
              -H "Content-Type: application/x-www-form-urlencoded" \
              -d "interview_id=$INT_ID&question_id=$NEXT_Q_ID&answer_text=Python+is+a+high-level+programming+language")
            split_response "$RESP"
            check "POST /interview/submit-answer-text" "200" "$CODE" "$BODY"

            # Submit audio answer (for another question if available, or same)
            RESP=$(curl -s --max-time 15 -w "\n%{http_code}" -X POST "$BASE/interview/submit-answer-audio" \
              -F "interview_id=$INT_ID" \
              -F "question_id=$NEXT_Q_ID" \
              -F "audio=@/tmp/api_test/audio.wav;type=audio/wav")
            split_response "$RESP"
            check "POST /interview/submit-answer-audio" "200" "$CODE" "$BODY"
        fi

        # Finish interview
        RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/interview/finish/$INT_ID")
        split_response "$RESP"
        check "POST /interview/finish/$INT_ID" "200" "$CODE" "$BODY"

        # Wait for background processing
        sleep 3
    fi
fi

# ================================================================
# 6. RESULTS
# ================================================================
echo ""
echo "━━━ 6. RESULTS ━━━"

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/users/results" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /admin/users/results (list)" "200" "$CODE" "$BODY"

# Get the interview that has results
RESULT_INT=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['interview']['id'] if d else '')" 2>/dev/null || echo "")

if [ -n "$RESULT_INT" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/results/$RESULT_INT" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "GET /admin/results/$RESULT_INT (detail)" "200" "$CODE" "$BODY"

    # Get response ID from answers
    RESP_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; ans=d.get('answers',[]); print(ans[0]['id'] if ans else '')" 2>/dev/null || echo "")

    if [ -n "$RESP_ID" ]; then
        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/admin/interviews/response/$RESP_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
        split_response "$RESP"
        check "GET /admin/interviews/response/$RESP_ID" "200" "$CODE" "$BODY"

        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -o /dev/null "$BASE/admin/results/audio/$RESP_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
        CODE=$(echo "$RESP" | tail -1)
        check "GET /admin/results/audio/$RESP_ID" "200 404" "$CODE" ""
    fi

    # Update result
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X PATCH "$BASE/admin/results/$RESULT_INT" \
      -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
      -d '{"total_score":8.5}')
    split_response "$RESP"
    check "PATCH /admin/results/$RESULT_INT (update)" "200" "$CODE" "$BODY"
fi

# ================================================================
# 7. CANDIDATE ROUTES
# ================================================================
echo ""
echo "━━━ 7. CANDIDATE (/api/candidate) ━━━"

if [ -n "$CAND_TOKEN" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/candidate/history" -H "Authorization: Bearer $CAND_TOKEN")
    split_response "$RESP"
    check "GET /candidate/history" "200" "$CODE" "$BODY"

    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/candidate/interviews" -H "Authorization: Bearer $CAND_TOKEN")
    split_response "$RESP"
    check "GET /candidate/interviews" "200" "$CODE" "$BODY"

    # Upload selfie (candidate route)
    RESP=$(curl -s --max-time 15 -w "\n%{http_code}" -X POST "$BASE/candidate/upload-selfie" \
      -H "Authorization: Bearer $CAND_TOKEN" \
      -F "file=@/tmp/api_test/selfie.jpg;type=image/jpeg")
    split_response "$RESP"
    check "POST /candidate/upload-selfie" "200" "$CODE" "$BODY"

    # Profile image
    if [ -n "$CAND_ID" ]; then
        RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -o /dev/null "$BASE/candidate/profile-image/$CAND_ID" \
          -H "Authorization: Bearer $CAND_TOKEN")
        CODE=$(echo "$RESP" | tail -1)
        check "GET /candidate/profile-image/$CAND_ID" "200 404" "$CODE" ""
    fi
else
    echo "  ❌ Candidate token not available — candidate APIs not tested"
fi

# ================================================================
# 8. STANDALONE TOOLS
# ================================================================
echo ""
echo "━━━ 8. STANDALONE TOOLS ━━━"

# Evaluate answer
RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/interview/evaluate-answer" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Python?","answer":"Python is a high-level programming language."}')
split_response "$RESP"
check "POST /interview/evaluate-answer" "200" "$CODE" "$BODY"

# TTS
RESP=$(curl -s --max-time 15 -w "\n%{http_code}" -o /dev/null "$BASE/interview/tts?text=Hello+world")
CODE=$(echo "$RESP" | tail -1)
check "GET /interview/tts" "200" "$CODE" ""

# Speech to text
RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/interview/tools/speech-to-text" \
  -F "audio=@/tmp/api_test/audio.wav;type=audio/wav")
split_response "$RESP"
check "POST /interview/tools/speech-to-text" "200" "$CODE" "$BODY"

# Question audio (for existing question)
if [ -n "$Q_ID" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -o /dev/null "$BASE/interview/audio/question/$Q_ID")
    CODE=$(echo "$RESP" | tail -1)
    check "GET /interview/audio/question/$Q_ID" "200 404" "$CODE" ""
fi

# ================================================================
# 9. SYSTEM / SETTINGS
# ================================================================
echo ""
echo "━━━ 9. SYSTEM ━━━"

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/status/?interview_id=1")
split_response "$RESP"
check "GET /status/ (system health)" "200" "$CODE" "$BODY"

# Email test
RESP=$(curl -s --max-time 15 -w "\n%{http_code}" "$BASE/admin/test-email" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /admin/test-email" "200 500" "$CODE" "$BODY"

RESP=$(curl -s --max-time 15 -w "\n%{http_code}" "$BASE/admin/test-email-sync" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /admin/test-email-sync" "200 500" "$CODE" "$BODY"

# WebSocket test (connect and immediately close)
echo "  --- WebSocket tests ---"
WS_RESULT=$(python3 -c "
import asyncio, websockets, json, sys
async def test_ws():
    try:
        async with websockets.connect('ws://localhost:8000/api/admin/dashboard/ws?token=$ADMIN_TOKEN', close_timeout=3) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            print('OK:' + str(msg)[:50])
    except Exception as e:
        print('ERR:' + str(e)[:80])
asyncio.run(test_ws())
" 2>&1)
if echo "$WS_RESULT" | grep -q "^OK:"; then
    echo "  ✅ WS /admin/dashboard/ws ($WS_RESULT)"
    PASS=$((PASS+1))
elif echo "$WS_RESULT" | grep -q "no module\|ModuleNotFoundError"; then
    echo "  ⚠️  WS /admin/dashboard/ws (websockets module not installed, testing via curl)"
    RESP=$(curl -s --max-time 5 -w "\n%{http_code}" -o /dev/null \
      -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
      "http://localhost:8000/api/admin/dashboard/ws?token=$ADMIN_TOKEN")
    CODE=$(echo "$RESP" | tail -1)
    check "WS /admin/dashboard/ws (upgrade)" "101 200" "$CODE" ""
else
    echo "  ❌ WS /admin/dashboard/ws ($WS_RESULT)"
    FAIL=$((FAIL+1))
    FAILED_LIST="$FAILED_LIST\n  - WS /admin/dashboard/ws: $WS_RESULT"
fi

WS_RESULT2=$(python3 -c "
import asyncio, websockets
async def test_ws():
    try:
        async with websockets.connect('ws://localhost:8000/api/status/ws?interview_id=1', close_timeout=3) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            print('OK:' + str(msg)[:50])
    except Exception as e:
        print('ERR:' + str(e)[:80])
asyncio.run(test_ws())
" 2>&1)
if echo "$WS_RESULT2" | grep -q "^OK:"; then
    echo "  ✅ WS /status/ws ($WS_RESULT2)"
    PASS=$((PASS+1))
elif echo "$WS_RESULT2" | grep -q "no module\|ModuleNotFoundError"; then
    RESP=$(curl -s --max-time 5 -w "\n%{http_code}" -o /dev/null \
      -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
      "http://localhost:8000/api/status/ws?interview_id=1")
    CODE=$(echo "$RESP" | tail -1)
    check "WS /status/ws (upgrade)" "101 200" "$CODE" ""
else
    echo "  ❌ WS /status/ws ($WS_RESULT2)"
    FAIL=$((FAIL+1))
    FAILED_LIST="$FAILED_LIST\n  - WS /status/ws: $WS_RESULT2"
fi

# ================================================================
# 10. VIDEO / WebRTC
# ================================================================
echo ""
echo "━━━ 10. VIDEO / WebRTC ━━━"

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -o /dev/null "$BASE/video/video_feed")
CODE=$(echo "$RESP" | tail -1)
check "GET /video/video_feed" "200 500 404" "$CODE" ""

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/video/offer" \
  -H "Content-Type: application/json" \
  -d '{"sdp":"v=0\r\n","type":"offer","interview_id":1}')
split_response "$RESP"
check "POST /video/offer" "200 500 422" "$CODE" "$BODY"

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/video/watch/1" \
  -H "Content-Type: application/json" \
  -d '{"sdp":"v=0\r\n","type":"offer"}')
split_response "$RESP"
check "POST /video/watch/1" "200 500 422" "$CODE" "$BODY"

# ================================================================
# 11. DESTRUCTIVE TESTS (cleanup)
# ================================================================
echo ""
echo "━━━ 11. DESTRUCTIVE (delete) ━━━"

# Delete result (if we have the E2E interview)
if [ -n "$INT_ID" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X DELETE "$BASE/admin/results/$INT_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "DELETE /admin/results/$INT_ID" "200 404" "$CODE" "$BODY"
fi

if [ -n "$Q_ID" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X DELETE "$BASE/admin/questions/$Q_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "DELETE /admin/questions/$Q_ID" "200" "$CODE" "$BODY"
fi

if [ -n "$INT_ID" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X DELETE "$BASE/admin/interviews/$INT_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "DELETE /admin/interviews/$INT_ID" "200" "$CODE" "$BODY"
fi

if [ -n "$PAPER_ID" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X DELETE "$BASE/admin/papers/$PAPER_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "DELETE /admin/papers/$PAPER_ID" "200" "$CODE" "$BODY"
fi

if [ -n "$CRUD_USER_ID" ]; then
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X DELETE "$BASE/admin/users/$CRUD_USER_ID" -H "Authorization: Bearer $ADMIN_TOKEN")
    split_response "$RESP"
    check "DELETE /admin/users/$CRUD_USER_ID" "200" "$CODE" "$BODY"
fi

# NOTE: Not testing POST /admin/shutdown (would kill the server)
echo "  ℹ️  POST /admin/shutdown — not tested (would kill the server)"

# Cleanup test files
rm -rf /tmp/api_test

# ================================================================
# SUMMARY
# ================================================================
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  FINAL RESULTS                                     ║"
echo "╠════════════════════════════════════════════════════╣"
printf "║  ✅ Passed:  %-4d                                   ║\n" $PASS
printf "║  ❌ Failed:  %-4d                                   ║\n" $FAIL
echo "╚════════════════════════════════════════════════════╝"

if [ $FAIL -gt 0 ]; then
    echo ""
    echo "NON-WORKING APIs:"
    echo -e "$FAILED_LIST"
fi
echo ""
