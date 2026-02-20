"""
Endpoint Scanner - Tests all non-agent endpoints with real credentials
Run: python tests/scan_endpoints.py
Server must be running on http://localhost:8000
"""

import requests
import json
import sys
import uuid as _uuid
from datetime import datetime, timedelta, timezone

BASE = "http://localhost:8000/api"
RESULTS = []
PASS = 0
FAIL = 0
WARN = 0

ADMIN_EMAIL    = "admin@test.com"
ADMIN_PASSWORD = "password123"
CANDIDATE_EMAIL    = "candidate@test.com"
CANDIDATE_PASSWORD = "password123"

# ──────────────────────────────────────────────────────────────
def _fmt(status, method, path, code, note=""):
    symbol = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️ "}.get(status, "?")
    print(f"  {symbol} [{code}] {method:6s} {path:<55} {note}")

def check(label, method, path, *, expected, headers=None, json_body=None,
          files=None, params=None, data_form=None, note=""):
    global PASS, FAIL, WARN
    url = BASE + path
    try:
        kwargs = {"timeout": 15}
        if headers: kwargs["headers"] = headers
        if json_body: kwargs["json"] = json_body
        if files: kwargs["files"] = files
        if params: kwargs["params"] = params
        if data_form: kwargs["data"] = data_form
        resp = getattr(requests, method.lower())(url, **kwargs)
        code = resp.status_code
        if code in expected:
            _fmt("PASS", method, path, code, note)
            PASS += 1
            RESULTS.append({"status": "PASS", "method": method, "path": path, "code": code, "note": note})
        else:
            try:
                detail = resp.json().get("detail", resp.text[:200])
            except Exception:
                detail = resp.text[:200]
            _fmt("FAIL", method, path, code, f"expected {expected} — {detail}")
            FAIL += 1
            RESULTS.append({"status": "FAIL", "method": method, "path": path, "code": code, "detail": detail})
        return resp
    except Exception as e:
        _fmt("FAIL", method, path, 0, f"CONNECTION ERROR: {e}")
        FAIL += 1
        RESULTS.append({"status": "FAIL", "method": method, "path": path, "code": 0, "detail": str(e)})
        return None

def section(name):
    print(f"\n{'━'*70}")
    print(f"  {name}")
    print(f"{'━'*70}")

# ──────────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────────
section("AUTH  /api/auth/")

# Login admin
r = check("auth:login_admin", "POST", "/auth/login", expected=[200],
          json_body={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
ADMIN_TOKEN = None
if r and r.status_code == 200:
    try:
        ADMIN_TOKEN = r.json()["data"]["access_token"]
        print(f"       🔑 Admin token acquired")
    except Exception as e:
        print(f"       ❌ Could not extract admin token: {e}")
ADMIN_AUTH = {"Authorization": f"Bearer {ADMIN_TOKEN}"} if ADMIN_TOKEN else {}

# Login candidate
r = check("auth:login_candidate", "POST", "/auth/login", expected=[200],
          json_body={"email": CANDIDATE_EMAIL, "password": CANDIDATE_PASSWORD})
CAND_TOKEN = None
if r and r.status_code == 200:
    try:
        CAND_TOKEN = r.json()["data"]["access_token"]
        print(f"       🔑 Candidate token acquired")
    except Exception: pass
CAND_AUTH = {"Authorization": f"Bearer {CAND_TOKEN}"} if CAND_TOKEN else {}

# OAuth2 /token (uses form data with 'username' field)
check("auth:oauth2_token", "POST", "/auth/token", expected=[200],
      data_form={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
      note="OAuth2 form-encoded")

# /me for both roles
check("auth:me_admin",     "GET", "/auth/me", expected=[200], headers=ADMIN_AUTH)
check("auth:me_candidate", "GET", "/auth/me", expected=[200], headers=CAND_AUTH)

# Logout (no auth needed)
check("auth:logout", "POST", "/auth/logout", expected=[200])

# Register with no auth (should be 403 — users exist)
check("auth:register_blocked", "POST", "/auth/register", expected=[403],
      json_body={"email": "new@test.com", "password": "Test1234!", "full_name": "X", "role": "candidate"},
      note="blocked — non-first user, no auth")

# Register new user as admin (use unique email each run to avoid duplicate)
_unique_email = f"newcand_{_uuid.uuid4().hex[:6]}@test.com"
check("auth:register_as_admin", "POST", "/auth/register", expected=[200, 201],
      headers=ADMIN_AUTH,
      json_body={"email": _unique_email, "password": "Test1234!", "full_name": "New Cand", "role": "candidate"},
      note="admin-assisted registration")

# ──────────────────────────────────────────────────────────────
# ADMIN — Papers
# ──────────────────────────────────────────────────────────────
section("ADMIN  /api/admin/  (Papers & Questions)")

check("admin:list_papers", "GET", "/admin/papers", expected=[200], headers=ADMIN_AUTH)

r_paper = check("admin:create_paper", "POST", "/admin/papers", expected=[200, 201],
                headers=ADMIN_AUTH,
                json_body={"name": "Scanner Paper", "description": "Auto-generated"})
PAPER_ID = None
if r_paper and r_paper.status_code in (200, 201):
    try:
        PAPER_ID = r_paper.json()["data"]["id"]
        print(f"       📄 Paper ID: {PAPER_ID}")
    except Exception as e:
        print(f"       ⚠️  Paper created but no ID: {e} — resp: {r_paper.text[:200]}")

if PAPER_ID:
    check("admin:get_paper",    "GET",   f"/admin/papers/{PAPER_ID}", expected=[200], headers=ADMIN_AUTH)
    check("admin:update_paper", "PATCH", f"/admin/papers/{PAPER_ID}", expected=[200],
          headers=ADMIN_AUTH, json_body={"description": "Updated"})

# Questions
Q_ID = None
if PAPER_ID:
    r_q = check("admin:add_question", "POST", f"/admin/papers/{PAPER_ID}/questions", expected=[200, 201],
                headers=ADMIN_AUTH,
                json_body={"content": "Explain inheritance.", "question_text": "Explain inheritance.",
                           "topic": "OOP", "difficulty": "Medium", "marks": 5, "response_type": "text"})
    if r_q and r_q.status_code in (200, 201):
        try:
            Q_ID = r_q.json()["data"]["id"]
            print(f"       ❓ Question ID: {Q_ID}")
        except Exception: pass

check("admin:list_questions", "GET", "/admin/questions", expected=[200], headers=ADMIN_AUTH)

if Q_ID:
    check("admin:get_question",    "GET",   f"/admin/questions/{Q_ID}", expected=[200], headers=ADMIN_AUTH)
    check("admin:update_question", "PATCH", f"/admin/questions/{Q_ID}", expected=[200],
          headers=ADMIN_AUTH, json_body={"difficulty": "Hard"})
    check("admin:list_paper_questions", "GET", f"/admin/papers/{PAPER_ID}/questions", expected=[200], headers=ADMIN_AUTH)

# ──────────────────────────────────────────────────────────────
# ADMIN — Interviews
# ──────────────────────────────────────────────────────────────
section("ADMIN  /api/admin/  (Interviews)")

check("admin:list_interviews",    "GET", "/admin/interviews",         expected=[200], headers=ADMIN_AUTH)
check("admin:live_dashboard",     "GET", "/admin/interviews/live-status", expected=[200], headers=ADMIN_AUTH)

SCHEDULE_TIME = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
SESSION_ID = None
ACCESS_TOKEN = None
# Resolve candidate_id from email
CANDIDATE_ID = None
try:
    r_cands = requests.get(f"{BASE}/admin/candidates", headers=ADMIN_AUTH, timeout=5)
    for c in r_cands.json().get("data", []):
        if c.get("email") == CANDIDATE_EMAIL or (c.get("candidate") or {}).get("email") == CANDIDATE_EMAIL:
            CANDIDATE_ID = c.get("id") or (c.get("candidate") or {}).get("id")
            break
    if CANDIDATE_ID: print(f"       👤 Candidate ID: {CANDIDATE_ID}")
except Exception as e:
    print(f"       ⚠️  Could not resolve candidate_id: {e}")
if PAPER_ID and CANDIDATE_ID:
    r_sched = check("admin:schedule_interview", "POST", "/admin/interviews/schedule", expected=[200, 201],
                    headers=ADMIN_AUTH,
                    json_body={
                        "candidate_id": CANDIDATE_ID,
                        "paper_id": PAPER_ID,
                        "schedule_time": SCHEDULE_TIME,
                        "duration_minutes": 60,
                        "max_questions": 1
                    })
else:
    r_sched = None
    print("  ⚠️  Skipping schedule — could not resolve candidate_id")
    if r_sched and r_sched.status_code in (200, 201):
        try:
            data = r_sched.json().get("data", {})
            # Handle various response structures
            SESSION_ID = (data.get("id") or
                          data.get("interview_id") or
                          (data.get("interview") or {}).get("id"))
            ACCESS_TOKEN = (data.get("access_token") or
                            (data.get("interview") or {}).get("access_token"))
            print(f"       📋 Session ID: {SESSION_ID}  |  Token: {ACCESS_TOKEN}")
        except Exception as e:
            print(f"       ⚠️  Schedule resp parse error: {e} — {r_sched.text[:300]}")

if SESSION_ID:
    check("admin:get_interview",    "GET",   f"/admin/interviews/{SESSION_ID}", expected=[200], headers=ADMIN_AUTH)
    check("admin:update_interview", "PATCH", f"/admin/interviews/{SESSION_ID}", expected=[200, 400],
          headers=ADMIN_AUTH, json_body={"duration_minutes": 90},
          note="400 if LIVE/COMPLETED")

# ──────────────────────────────────────────────────────────────
# ADMIN — Users & Candidates
# ──────────────────────────────────────────────────────────────
section("ADMIN  /api/admin/  (Users & Results)")

check("admin:list_users",      "GET", "/admin/users",      expected=[200], headers=ADMIN_AUTH)
check("admin:list_candidates", "GET", "/admin/candidates", expected=[200], headers=ADMIN_AUTH)

# Get user by ID (admin's own ID = 1 or we can skip)
r_me = requests.get(f"{BASE}/auth/me", headers=ADMIN_AUTH, timeout=5)
ADMIN_ID = None
if r_me.ok:
    try:
        raw = r_me.json().get("data", {})
        # Handle nested {admin: {...}} format
        if "admin" in raw:
            ADMIN_ID = raw["admin"].get("id")
        else:
            ADMIN_ID = raw.get("id")
    except Exception: pass

if ADMIN_ID:
    check("admin:get_user", "GET", f"/admin/users/{ADMIN_ID}", expected=[200], headers=ADMIN_AUTH)

# Results
check("admin:get_all_results", "GET", "/admin/users/results", expected=[200], headers=ADMIN_AUTH)

if SESSION_ID:
    check("admin:get_result", "GET", f"/admin/results/{SESSION_ID}", expected=[200, 404],
          headers=ADMIN_AUTH, note="404 OK — result not generated yet")

# Candidate status
if SESSION_ID:
    check("admin:candidate_status", "GET", f"/admin/interviews/{SESSION_ID}/candidate-status",
          expected=[200, 404], headers=ADMIN_AUTH)

# ──────────────────────────────────────────────────────────────
# INTERVIEW (candidate-facing)
# ──────────────────────────────────────────────────────────────
section("INTERVIEW  /api/interview/")

if ACCESS_TOKEN:
    check("interview:access", "GET", f"/interview/access/{ACCESS_TOKEN}", expected=[200],
          note="may return WAIT if future-scheduled")
else:
    print("  ⚠️  No access token — skipping interview/access")

# TTS (GET with ?text=)
check("interview:tts", "GET", "/interview/tts", expected=[200],
      params={"text": "Hello candidate, please begin."})

# STT (no file → 422)
check("interview:stt_nofile", "POST", "/interview/tools/speech-to-text", expected=[422],
      note="no file → validation error expected")

# ──────────────────────────────────────────────────────────────
# CANDIDATE
# ──────────────────────────────────────────────────────────────
section("CANDIDATE  /api/candidate/")

check("candidate:history",      "GET", "/candidate/history",             expected=[200], headers=CAND_AUTH)
check("candidate:profile_image","GET", "/candidate/profile-image/1",     expected=[200, 404], headers=CAND_AUTH,
      note="404 if no image")

# Candidate cannot access admin endpoints
check("candidate:admin_block",  "GET", "/admin/users", expected=[401, 403], headers=CAND_AUTH,
      note="must be blocked for candidate role")

# ──────────────────────────────────────────────────────────────
# SYSTEM STATUS
# ──────────────────────────────────────────────────────────────
section("SYSTEM  /api/status/")

check("status:health", "GET", "/status/", expected=[200], params={"interview_id": 1})

# ──────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────
total = PASS + FAIL + WARN
print(f"\n{'═'*70}")
print(f"  SCAN COMPLETE: {total} endpoints tested")
print(f"  ✅ PASS: {PASS}  ❌ FAIL: {FAIL}  ⚠️  WARN: {WARN}")
print(f"{'═'*70}")

if FAIL > 0:
    print("\n🔴 FAILURES:")
    for r in RESULTS:
        if r["status"] == "FAIL":
            print(f"   {r['method']:6s} {r['path']:<50} [{r['code']}] {r.get('detail','')[:120]}")

report_path = "tests/scan_report.json"
with open(report_path, "w") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "results": RESULTS,
        "summary": {"pass": PASS, "fail": FAIL, "warn": WARN, "total": total}
    }, f, indent=2)
print(f"\n  📄 Report: {report_path}")
sys.exit(1 if FAIL > 0 else 0)
