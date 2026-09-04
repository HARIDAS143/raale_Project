"""
test_phase4.py — Automated verification script for Phase 4 API endpoints.
"""

import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def post(path, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def test_all():
    print("==================================================")
    print("  PHASE 4 AUTOMATED API VERIFICATION SUITE")
    print("==================================================")
    
    # 1. Health check
    st, data = get("/health")
    print(f"1. GET /health                     [Status: {st}] -> {data.get('status')}")
    assert st == 200 and data.get("status") == "ok"

    # 2. Dashboard Stats
    st, data = get("/dashboard/stats")
    print(f"2. GET /dashboard/stats            [Status: {st}] -> Users: {data.get('total_users')}, Accounts: {data.get('total_shared_accounts')}, Active Sessions: {data.get('active_sessions')}")
    assert st == 200 and data.get("total_users") == 20

    # 3. Users List
    st, data = get("/users/")
    print(f"3. GET /users/                     [Status: {st}] -> Loaded {len(data)} synthetic users")
    assert st == 200 and len(data) == 20

    # 4. Shared Accounts List
    st, data = get("/shared-accounts/")
    print(f"4. GET /shared-accounts/           [Status: {st}] -> Loaded {len(data)} shared accounts")
    assert st == 200 and len(data) == 8

    # 5. Permission Check Failure Test (User L1 vs Shared Account HIGH risk)
    print("\n--- Testing Permission Check (Denial Case) ---")
    denial_payload = {
        "user_id": "USER001",  # Level L1
        "shared_account_id": "SACC001",  # Level HIGH
        "justification": "Low permission user requesting high risk account"
    }
    st, den_res = post("/sessions/request", denial_payload)
    print(f"5a. POST /sessions/request (L1 -> HIGH) [Status: {st}] -> Permission Granted: {den_res.get('permission_granted')} ({den_res.get('status')})")
    assert st == 201
    assert den_res.get("permission_granted") is False

    # 5b. Permission Check Success Test (User L4 vs Shared Account HIGH risk)
    print("\n--- Testing Delegation Request & Session Creation (Success Case) ---")
    grant_payload = {
        "user_id": "USER012",  # Level L4 Security Admin
        "shared_account_id": "SACC001",  # Level HIGH
        "justification": "Review 1 Live Demonstration Test Session"
    }
    st, del_res = post("/sessions/request", grant_payload)
    print(f"5b. POST /sessions/request (L4 -> HIGH) [Status: {st}] -> Permission Granted: {del_res.get('permission_granted')}")
    assert st == 201
    assert del_res.get("permission_granted") is True
    session_id = del_res.get("session", {}).get("session_id")
    token = del_res.get("session", {}).get("delegation_token")
    print(f"   Session Created: {session_id} | Token: {token}")

    # 6. Active Sessions
    st, data = get("/sessions/active")
    print(f"\n6. GET /sessions/active            [Status: {st}] -> Active sessions count: {len(data)}")
    assert st == 200 and len(data) >= 1

    # 7. Perform Privileged Action (Step 6-9 Workflow)
    print("\n--- Testing Workflow Steps 6-9: Perform Action & Attribute ---")
    action_payload = {
        "session_id": session_id,
        "action": "Modify configuration",
        "sensitivity": "HIGH",
        "justification": "Review 1 Automated Workflow Verification"
    }
    st, act_res = post("/actions/perform", action_payload)
    print(f"7. POST /actions/perform           [Status: {st}] -> Action: {act_res.get('action_id')} | User: {act_res.get('user_id')} | Status: {act_res.get('attribution_status')}")
    assert st == 201
    assert act_res.get("attribution_status") == "ATTRIBUTED"
    assert act_res.get("user_id") == "USER012"

    # 8. Unattributed Action Baseline Test
    unattr_payload = {
        "session_id": None,
        "shared_account_id": "SACC002",
        "action": "Export report",
        "sensitivity": "MEDIUM",
        "justification": "Direct shared account access test without session"
    }
    st, unattr_res = post("/actions/perform", unattr_payload)
    print(f"8. POST /actions/perform (No Sess) [Status: {st}] -> User: {unattr_res.get('user_id')} | Status: {unattr_res.get('attribution_status')}")
    assert st == 201
    assert unattr_res.get("attribution_status") == "UNATTRIBUTED"

    # 9. Audit Log
    st, audit_data = get("/audit-log")
    print(f"\n9. GET /audit-log                  [Status: {st}] -> Audit Trail entries: {len(audit_data)}")
    assert st == 200 and len(audit_data) >= 2

    print("\n==================================================")
    print("  ALL VERIFICATION TESTS PASSED SUCCESSFULLY!  ")
    print("==================================================")

if __name__ == "__main__":
    time.sleep(1)
    test_all()
