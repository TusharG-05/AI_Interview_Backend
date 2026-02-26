#!/bin/bash
# =============================================================================
# E2E API TEST — EVERY ENDPOINT
# Users: admin@test.com & tushar@chicmicstudios.in
# =============================================================================
set -o pipefail

BASE="http://localhost:8001/api"
PASS=0
FAIL=0
FAILED_LIST=""
DB_URL="postgresql://postgres:Tush%234184@localhost:5432/interview_db"

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
        local msg=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message','')[:80])" 2>/dev/null || echo "$body" | head -c 80)
        FAILED_LIST="$FAILED_LIST\n  - $name (HTTP $code): $msg"
    fi
}

split_response() {
    BODY=$(echo "$1" | sed '$d')
    CODE=$(echo "$1" | tail -1)
}

# --- 0. PRE-REQUISITES & TEST FILES ---
echo "Preparing test files..."
mkdir -p /tmp/api_test

# Minimal JPEG
python3 -c "
data = bytes([0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,0x49,0x46,0x00,0x01,0x01,0x00,0x00,0x01,0x00,0x01,0x00,0x00,0xFF,0xDB,0x00,0x43,0x00,0x08,0x06,0x06,0x07,0x06,0x05,0x08,0x07,0x07,0x07,0x09,0x09,0x08,0x0A,0x0C,0x14,0x0D,0x0C,0x0B,0x0B,0x0C,0x19,0x12,0x13,0x0F,0x14,0x1D,0x1A,0x1F,0x1E,0x1D,0x1A,0x1C,0x1C,0x20,0x24,0x2E,0x27,0x20,0x22,0x2C,0x23,0x1C,0x1C,0x28,0x37,0x29,0x2C,0x30,0x31,0x34,0x34,0x34,0x1F,0x27,0x39,0x3D,0x38,0x32,0x3C,0x2E,0x33,0x34,0x32,0xFF,0xC0,0x00,0x0B,0x08,0x00,0x01,0x00,0x01,0x01,0x01,0x11,0x00,0xFF,0xC4,0x00,0x1F,0x00,0x00,0x01,0x05,0x01,0x01,0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0xFF,0xDA,0x00,0x08,0x01,0x01,0x00,0x00,0x3F,0x00,0x54,0xDB,0x2E,0x44,0xA4,0x7E,0x39,0xA2,0xCF,0xFF,0xD9])
with open('/tmp/api_test/selfie.jpg','wb') as f: f.write(data)
"
# Empty audio
python3 -c "
import wave, struct
with wave.open('/tmp/api_test/audio.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    w.writeframes(struct.pack('<' + 'h'*16000, *([0]*16000)))
"
echo "Questions" > /tmp/api_test/questions.txt

TUSHAR_ID=$(psql "$DB_URL" -tAc "SELECT id FROM public.\"user\" WHERE email='tushar@chicmicstudios.in' LIMIT 1;" 2>/dev/null)
if [ -z "$TUSHAR_ID" ]; then echo "FATAL: Could not find Tushar in DB"; exit 1; fi

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  FULL E2E API TEST SUITE                           ║"
echo "╚════════════════════════════════════════════════════╝"

# ================================================================
# 1. AUTH (ADMIN & CANDIDATE)
# ================================================================
echo ""
echo "━━━ 1. AUTH & SETUP ━━━"

# Admin Login
RESP=$(curl -s --max-time 15 -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" -d '{"email":"admin@test.com","password":"admin123"}')
split_response "$RESP"
check "POST /auth/login (admin)" "200" "$CODE" "$BODY"
ADMIN_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token',''))" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ]; then echo "FATAL: No admin token"; exit 1; fi

# Create Paper for Interview
RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/admin/papers" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Tushar Test Paper","description":"Tushars interview test"}')
split_response "$RESP"
PAPER_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)

if [ -z "$PAPER_ID" ]; then
    PAPER_ID=$(psql "$DB_URL" -tAc "SELECT id FROM public.questionpaper LIMIT 1;")
    echo "  Fallback Paper ID: $PAPER_ID"
fi

# Add a Question
RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X POST "$BASE/admin/papers/$PAPER_ID/questions" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"content":"What is Python?","question_text":"What is Python?","topic":"Programming","difficulty":"Easy","marks":10,"response_type":"text"}')
split_response "$RESP"
Q_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)

# Schedule Interview for Tushar
SCHED_TIME=$(date -u -d "+1 minute" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%SZ)
RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/admin/interviews/schedule" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"candidate_id\":$TUSHAR_ID,\"paper_id\":$PAPER_ID,\"schedule_time\":\"$SCHED_TIME\",\"duration_minutes\":120,\"max_questions\":1}")
split_response "$RESP"
check "POST /admin/interviews/schedule" "201" "$CODE" "$BODY"
INT_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('interview',{}).get('id',''))" 2>/dev/null)
ACCESS_TK=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token',''))" 2>/dev/null)

# Candidate Login
RESP=$(curl -s --max-time 15 -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"tushar@chicmicstudios.in\",\"password\":\"tushar\",\"access_token\":\"$ACCESS_TK\"}")
split_response "$RESP"
check "POST /auth/login (candidate: tushar)" "200" "$CODE" "$BODY"
CAND_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token',''))" 2>/dev/null)

# Ensure me works
RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/auth/me" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /auth/me (admin)" "200" "$CODE" "$BODY"

RESP=$(curl -s --max-time 10 -w "\n%{http_code}" "$BASE/auth/me" -H "Authorization: Bearer $CAND_TOKEN")
split_response "$RESP"
check "GET /auth/me (candidate)" "200" "$CODE" "$BODY"

# ================================================================
# 2. ADMIN CRUD (Papers, Questions, Users, Interviews)
# ================================================================
echo ""
echo "━━━ 2. ADMIN ENDPOINTS ━━━"

RESP=$(curl -s -w "\n%{http_code}" "$BASE/admin/papers" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"; check "GET /admin/papers" "200" "$CODE" "$BODY"

RESP=$(curl -s -w "\n%{http_code}" "$BASE/admin/questions" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"; check "GET /admin/questions" "200" "$CODE" "$BODY"

RESP=$(curl -s -w "\n%{http_code}" "$BASE/admin/users" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"; check "GET /admin/users" "200" "$CODE" "$BODY"

RESP=$(curl -s -w "\n%{http_code}" "$BASE/admin/interviews" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"; check "GET /admin/interviews" "200" "$CODE" "$BODY"

RESP=$(curl -s -w "\n%{http_code}" "$BASE/admin/interviews/live-status" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"; check "GET /admin/interviews/live-status" "200" "$CODE" "$BODY"

# ================================================================
# 3. INTERVIEW FLOW (Candidate Side)
# ================================================================
echo ""
echo "━━━ 3. CANDIDATE INTERVIEW WORKFLOW ━━━"

# Wait for schedule_time to pass
echo "  ⏳ Waiting 65s for interview schedule time..."
sleep 65

# Access
RESP=$(curl -s -w "\n%{http_code}" "$BASE/interview/access/$ACCESS_TK" -H "Authorization: Bearer $CAND_TOKEN")
split_response "$RESP"
check "GET /interview/access/{token}" "200" "$CODE" "$BODY"

# Upload selfie
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/interview/upload-selfie" \
  -H "Authorization: Bearer $CAND_TOKEN" -F "interview_id=$INT_ID" -F "file=@/tmp/api_test/selfie.jpg;type=image/jpeg")
split_response "$RESP"
check "POST /interview/upload-selfie" "200" "$CODE" "$BODY"

# Start Session
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/interview/start-session/$INT_ID" \
  -H "Authorization: Bearer $CAND_TOKEN" -F "enrollment_audio=@/tmp/api_test/audio.wav;type=audio/wav")
split_response "$RESP"
check "POST /interview/start-session/$INT_ID" "200" "$CODE" "$BODY"

# Next Question
RESP=$(curl -s -w "\n%{http_code}" "$BASE/interview/next-question/$INT_ID" -H "Authorization: Bearer $CAND_TOKEN")
split_response "$RESP"
check "GET /interview/next-question/$INT_ID" "200" "$CODE" "$BODY"
NEXT_Q_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('question_id',''))" 2>/dev/null)

if [ -n "$NEXT_Q_ID" ]; then
    # Submit Answer Text
    RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/interview/submit-answer-text" \
      -H "Authorization: Bearer $CAND_TOKEN" -H "Content-Type: application/x-www-form-urlencoded" \
      -d "interview_id=$INT_ID&question_id=$NEXT_Q_ID&answer_text=Python+is+a+high-level+programming+language")
    split_response "$RESP"
    check "POST /interview/submit-answer-text" "200" "$CODE" "$BODY"

    # Submit Answer Audio
    RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/interview/submit-answer-audio" \
      -H "Authorization: Bearer $CAND_TOKEN" -F "interview_id=$INT_ID" -F "question_id=$NEXT_Q_ID" -F "audio=@/tmp/api_test/audio.wav;type=audio/wav")
    split_response "$RESP"
    check "POST /interview/submit-answer-audio" "200" "$CODE" "$BODY"
fi

# Finish Interview
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/interview/finish/$INT_ID" -H "Authorization: Bearer $CAND_TOKEN")
split_response "$RESP"
check "POST /interview/finish/$INT_ID" "200" "$CODE" "$BODY"

sleep 3 # Wait for background task processing

# ================================================================
# 4. ADMIN RESULTS
# ================================================================
echo ""
echo "━━━ 4. ADMIN RESULTS ━━━"

RESP=$(curl -s -w "\n%{http_code}" "$BASE/admin/users/results" -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /admin/users/results" "200" "$CODE" "$BODY"

# ================================================================
# 5. STANDALONE & SYSTEM
# ================================================================
echo ""
echo "━━━ 5. STANDALONE & SYSTEM ━━━"

RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/interview/evaluate-answer" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"question":"What is Python?","answer":"Language"}')
split_response "$RESP"
check "POST /interview/evaluate-answer" "200" "$CODE" "$BODY"

RESP=$(curl -s -w "\n%{http_code}" -o /dev/null "$BASE/interview/tts?text=Test" -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "GET /interview/tts" "200" "$CODE" ""

RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/interview/tools/speech-to-text" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -F "audio=@/tmp/api_test/audio.wav;type=audio/wav")
split_response "$RESP"
check "POST /interview/tools/speech-to-text" "200" "$CODE" "$BODY"

RESP=$(curl -s -w "\n%{http_code}" "$BASE/status/?interview_id=1")
split_response "$RESP"
check "GET /status/" "200" "$CODE" "$BODY"

# WebSocket tests using curl Upgrade
echo "  --- WebSockets ---"
RESP=$(curl -s --max-time 5 -w "\n%{http_code}" -o /dev/null -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" "$BASE/admin/dashboard/ws?token=$ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "WS /admin/dashboard/ws" "101 200" "$CODE" ""

RESP=$(curl -s --max-time 5 -w "\n%{http_code}" -o /dev/null -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" "$BASE/status/ws?interview_id=$INT_ID")
CODE=$(echo "$RESP" | tail -1)
check "WS /status/ws" "101 200" "$CODE" ""

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

rm -rf /tmp/api_test
