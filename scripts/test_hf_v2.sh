# =============================================================================
# FULL E2E API TEST — REMOTE HUGGING FACE (v2)
# Tests against https://ichigo253-ai-interview-backend-v2.hf.space/api
# =============================================================================
set -o pipefail

BASE="https://ichigo253-ai-interview-backend-v2.hf.space/api"
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
" 2>/dev/null

# Create WAV audio file
python3 -c "
import wave, struct
with wave.open('/tmp/api_test/audio.wav', 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(struct.pack('<' + 'h' * 16000, *([0]*16000)))
print('Created audio.wav')
"

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  v2 E2E API TEST SUITE — REMOTE HUGGING FACE       ║"
echo "╚════════════════════════════════════════════════════╝"

# ================================================================
# 1. AUTH
# ================================================================
echo ""
echo "━━━ 1. AUTH ━━━"

# Login super admin
RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}')
split_response "$RESP"
check "POST /auth/login (admin)" "200" "$CODE" "$BODY"
ADMIN_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")

# Register candidate
UNIQUE_EMAIL="v2_cand_$(date +%s)@test.com"
RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d "{\"email\":\"$UNIQUE_EMAIL\",\"password\":\"test123\",\"full_name\":\"HF v2 Candidate\",\"role\":\"CANDIDATE\"}")
split_response "$RESP"
check "POST /auth/register" "201" "$CODE" "$BODY"
CAND_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")
CAND_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

# ================================================================
# 2. TEAMS (v2 NEW)
# ================================================================
echo ""
echo "━━━ 2. TEAMS ━━━"

RESP=$(curl -s --max-time 30 -w "\n%{http_code}" "$BASE/super-admin/teams" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
split_response "$RESP"
check "GET /super-admin/teams (list)" "200" "$CODE" "$BODY"
TEAM_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['id'] if d else '')" 2>/dev/null || echo "")

# ================================================================
# 3. PAPERS
# ================================================================
echo ""
echo "━━━ 3. PAPERS ━━━"

RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/admin/papers" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d "{\"name\":\"HF v2 Paper\",\"description\":\"Remote Test\",\"team_id\":$TEAM_ID}")
split_response "$RESP"
check "POST /admin/papers" "201" "$CODE" "$BODY"
PAPER_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

if [ -n "$PAPER_ID" ]; then
    curl -s -X POST "$BASE/admin/papers/$PAPER_ID/questions" \
      -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
      -d '{"question_text":"What is FastAPI?","marks":10,"response_type":"text"}' > /dev/null
fi

# ================================================================
# 4. INTERVIEW FLOW
# ================================================================
echo ""
echo "━━━ 4. INTERVIEW ━━━"

if [ -n "$PAPER_ID" ] && [ -n "$CAND_ID" ] && [ -n "$TEAM_ID" ]; then
    SCHED_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    RESP=$(curl -s --max-time 30 -w "\n%{http_code}" -X POST "$BASE/admin/interviews/schedule" \
      -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
      -d "{\"candidate_id\":$CAND_ID,\"paper_id\":$PAPER_ID,\"team_id\":$TEAM_ID,\"interview_round\":\"ROUND_1\",\"schedule_time\":\"$SCHED_TIME\"}")
    split_response "$RESP"
    check "POST /admin/interviews/schedule" "201" "$CODE" "$BODY"
    INT_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['interview']['id'])" 2>/dev/null || echo "")
fi

# ================================================================
# 5. STATUS
# ================================================================
echo ""
echo "━━━ 5. SYSTEM ━━━"

RESP=$(curl -s --max-time 30 -w "\n%{http_code}" "$BASE/status/")
split_response "$RESP"
check "GET /status/" "200" "$CODE" "$BODY"

# ================================================================
# SUMMARY
# ================================================================
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  HF v2 LIVE RESULTS                                ║"
echo "╠════════════════════════════════════════════════════╣"
printf "║  ✅ Passed:  %-4d                                   ║\n" $PASS
printf "║  ❌ Failed:  %-4d                                   ║\n" $FAIL
echo "╚════════════════════════════════════════════════════╝"
rm -rf /tmp/api_test
