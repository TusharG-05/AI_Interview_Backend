#!/bin/bash
# test_hf_final.sh - Complete Remote API Verification
set -o pipefail
BASE="https://ichigo253-ai-interview-backend.hf.space/api"
PASS=0; FAIL=0; FAILED_LIST=""

check() {
    local name="$1"; local expected="$2"; local code="$3"; local body="$4"
    local found=0
    for exp in $expected; do if [ "$code" = "$exp" ]; then found=1; break; fi; done
    if [ $found -eq 1 ]; then echo "  ✅ $name ($code)"; PASS=$((PASS+1))
    else echo "  ❌ $name (got $code, expected $expected)"; echo "     $(echo "$body" | head -c 200)"; FAIL=$((FAIL+1))
         msg=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message','')[:80])" 2>/dev/null || echo "$body" | head -c 80)
         FAILED_LIST="$FAILED_LIST\n  - $name (HTTP $code): $msg"
    fi
}
split_response() { BODY=$(echo "$1" | sed '$d'); CODE=$(echo "$1" | tail -1); }

echo "Preparing test files..."
mkdir -p /tmp/hf_test
python3 -c "import wave, struct; w=wave.open('/tmp/hf_test/audio.wav','w'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(struct.pack('<'+'h'*16000,*([0]*16000))); w.close()"
python3 -c "data = bytes([0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,0x49,0x46,0x00,0x01,0x01,0x00,0x00,0x01,0x00,0x01,0x00,0x00,0xFF,0xDB,0x00,0x43,0x00,0x08,0x06,0x06,0x07,0x06,0x05,0x08,0x07,0x07,0x07,0x09,0x09,0x08,0x0A,0x0C,0x14,0x0D,0x0C,0x0B,0x0B,0x0C,0x19,0x12,0x13,0x0F,0x14,0x1D,0x1A,0x1F,0x1E,0x1D,0x1A,0x1C,0x1C,0x20,0x24,0x2E,0x27,0x20,0x22,0x2C,0x23,0x1C,0x1C,0x28,0x37,0x29,0x2C,0x30,0x31,0x34,0x34,0x34,0x1F,0x27,0x39,0x3D,0x38,0x32,0x3C,0x2E,0x33,0x34,0x32,0xFF,0xC0,0x00,0x0B,0x08,0x00,0x01,0x00,0x01,0x01,0x01,0x11,0x00,0xFF,0xC4,0x00,0x1F,0x00,0x00,0x01,0x05,0x01,0x01,0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0xFF,0xDA,0x00,0x08,0x01,0x01,0x00,0x00,0x3F,0x00,0x54,0xDB,0x2E,0x44,0xA4,0x7E,0x39,0xA2,0xCF,0xFF,0xD9]); open('/tmp/hf_test/selfie.jpg','wb').write(data)"

echo "━━━ 1. AUTH & SETUP (HF) ━━━"
RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/auth/login" -H "Content-Type: application/json" -d '{"email":"admin@test.com","password":"admin123"}')
split_response "$RESP"
check "Admin Login" "200" "$CODE" "$BODY"
ADMIN_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null)

echo "Searching for Tushar's account..."
TUSHAR_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$BASE/admin/users" | python3 -c "import sys,json; d=json.load(sys.stdin); print(next((u['id'] for u in d['data'] if u['email'].lower() == 'tushar@chicmicstudios.in'), ''))" 2>/dev/null)
echo "Using Tushar ID: $TUSHAR_ID"

echo "Searching for ReactJS paper..."
PAPER_ID=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$BASE/admin/papers" | python3 -c "import sys,json; d=json.load(sys.stdin); print(next((p['id'] for p in d['data'] if 'reactjs' in p['name'].lower() or 'react' in p['name'].lower()), d['data'][0]['id'] if d['data'] else ''))" 2>/dev/null)
echo "Using Paper ID: $PAPER_ID"

echo "Scheduling Interview..."
SCHED_TIME=$(date -u -d "-5 minutes" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%SZ)
RESP=$(curl -s --max-time 60 -w "\n%{http_code}" -X POST "$BASE/admin/interviews/schedule" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"candidate_id\":$TUSHAR_ID,\"paper_id\":$PAPER_ID,\"schedule_time\":\"$SCHED_TIME\",\"duration_minutes\":120,\"max_questions\":1}")
split_response "$RESP"
check "Schedule Interview" "201" "$CODE" "$BODY"
INT_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['interview']['id'])" 2>/dev/null)
ACCESS_TK=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['access_token'])" 2>/dev/null)

echo "Logging in Candidate (Tushar) with Access Token..."
RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/auth/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"tushar@chicmicstudios.in\",\"password\":\"tushar\",\"access_token\":\"$ACCESS_TK\"}")
split_response "$RESP"
check "Candidate Login" "200" "$CODE" "$BODY"
CAND_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null)

echo "━━━ 2. INTERVIEW FLOW ━━━"
if [ -n "$ACCESS_TK" ]; then
    RESP=$(curl -s --max-time 30 -w "\n%{http_code}" "$BASE/interview/access/$ACCESS_TK" -H "Authorization: Bearer $CAND_TOKEN")
    split_response "$RESP"; check "Interview Access" "200" "$CODE" "$BODY"

    RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/interview/upload-selfie" \
      -H "Authorization: Bearer $CAND_TOKEN" -F "interview_id=$INT_ID" -F "file=@/tmp/hf_test/selfie.jpg;type=image/jpeg")
    split_response "$RESP"; check "Selfie Upload" "200" "$CODE" "$BODY"

    RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/interview/start-session/$INT_ID" \
      -H "Authorization: Bearer $CAND_TOKEN" -F "enrollment_audio=@/tmp/hf_test/audio.wav;type=audio/wav")
    split_response "$RESP"; check "Start Session" "200" "$CODE" "$BODY"

    RESP=$(curl -s --max-time 30 -w "\n%{http_code}" "$BASE/interview/next-question/$INT_ID" -H "Authorization: Bearer $CAND_TOKEN")
    split_response "$RESP"; check "Next Question" "200" "$CODE" "$BODY"
    NEXT_Q_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('question_id',''))" 2>/dev/null)

    if [ -n "$NEXT_Q_ID" ]; then
        RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/interview/submit-answer-text" \
          -H "Authorization: Bearer $CAND_TOKEN" -H "Content-Type: application/x-www-form-urlencoded" \
          -d "interview_id=$INT_ID&question_id=$NEXT_Q_ID&answer_text=Remote+HF+Verified")
        split_response "$RESP"; check "Submit Answer" "200" "$CODE" "$BODY"
    fi

    RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/interview/finish/$INT_ID" -H "Authorization: Bearer $CAND_TOKEN")
    split_response "$RESP"; check "Finish Interview" "200" "$CODE" "$BODY"

    # PATCH Test (Now after session is finished and result record exists)
    RESP=$(curl -s --max-time 10 -w "\n%{http_code}" -X PATCH "$BASE/admin/results/$INT_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
      -d '{"total_score":10.0}')
    split_response "$RESP"; check "PATCH /admin/results/$INT_ID (Fixed API)" "200" "$CODE" "$BODY"
fi

echo "━━━ 3. STANDALONE TOOLS & SYSTEM ━━━"
RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/interview/evaluate-answer" \
  -H "Authorization: Bearer $CAND_TOKEN" -H "Content-Type: application/json" \
  -d '{"question":"What is React?","answer":"A JavaScript library for building UI."}')
split_response "$RESP"; check "POST /evaluate-answer" "200" "$CODE" "$BODY"

RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/interview/tools/speech-to-text" \
  -H "Authorization: Bearer $CAND_TOKEN" -F "audio=@/tmp/hf_test/audio.wav;type=audio/wav")
split_response "$RESP"; check "POST /speech-to-text" "200" "$CODE" "$BODY"

RESP=$(curl -s --max-time 30 -w "\n%{http_code}" "$BASE/status/?interview_id=1")
split_response "$RESP"; check "GET /status/" "200" "$CODE" "$BODY"

echo ""
echo "━━━ SUMMARY ━━━"
echo "✅ Passed: $PASS, ❌ Failed: $FAIL"
[ $FAIL -gt 0 ] && echo -e "Failures: $FAILED_LIST"
rm -rf /tmp/hf_test
