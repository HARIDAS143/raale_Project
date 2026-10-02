"""
test_review2.py — Automated Verification Suite for Review 2 (70% Completion).
Tests all 10+ core capabilities:
 1. Valid delegation
 2. Invalid delegation
 3. Permission denial (L1 vs L4)
 4. Session expiration enforcement
 5. Session revocation
 6. Revoked session rejection
 7. Invalid session rejection
 8. Missing delegation (unattributed)
 9. Successful individual attribution & Explanation Layer
10. Conflicting identity evidence -> Human Review Queue
11. Human review decision submission & resolution
12. External partner restriction policy
13. Dynamic evaluation benchmark calculation
14. Audit log search and filtering
"""

import sys
from fastapi.testclient import TestClient
from main import app
from seed import seed

client = TestClient(app)

passed_count = 0
failed_count = 0
total_tests = 0


def record_result(name: str, passed: bool, detail: str = ""):
    global passed_count, failed_count, total_tests
    total_tests += 1
    if passed:
        passed_count += 1
        print(f"  [PASS] Test {total_tests:02d}: {name} {detail}")
    else:
        failed_count += 1
        print(f"  [FAIL] Test {total_tests:02d}: {name} -> {detail}")


def run_all_tests():
    global passed_count, failed_count, total_tests
    passed_count = 0
    failed_count = 0
    total_tests = 0

    print("======================================================================")
    print("  REVIEW 2 AUTOMATED VERIFICATION SUITE — 70% COMPLETION MILESTONE   ")
    print("======================================================================")

    # Re-seed database to ensure clean state
    seed()

    # -------------------------------------------------------------------------
    # Test 1: Valid Delegation
    # -------------------------------------------------------------------------
    try:
        resp = client.post("/sessions/request", json={
            "user_id": "USER012",       # L4 Security Admin
            "shared_account_id": "SACC001", # HIGH risk LegacyERP
            "duration_minutes": 30,
            "justification": "Review 2 Automated Test Valid Delegation"
        })
        data = resp.json()
        valid = (
            resp.status_code == 201 and
            data.get("permission_granted") is True and
            "session" in data and
            data["session"]["status"] == "active" and
            data["session"]["delegation_token"].startswith("TOK-DEL-")
        )
        test1_session_id = data.get("session", {}).get("session_id")
        record_result("Valid Delegation Request", valid, f"Session: {test1_session_id}")
    except Exception as e:
        record_result("Valid Delegation Request", False, str(e))

    # -------------------------------------------------------------------------
    # Test 2: Invalid Delegation (Non-existent user)
    # -------------------------------------------------------------------------
    try:
        resp = client.post("/sessions/request", json={
            "user_id": "USER_DOES_NOT_EXIST",
            "shared_account_id": "SACC001",
            "justification": "Invalid identity test"
        })
        valid = resp.status_code == 404
        record_result("Invalid Delegation (Unknown Identity)", valid, f"HTTP {resp.status_code}")
    except Exception as e:
        record_result("Invalid Delegation (Unknown Identity)", False, str(e))

    # -------------------------------------------------------------------------
    # Test 3: Permission Denial (L1 User vs HIGH Risk Account)
    # -------------------------------------------------------------------------
    try:
        resp = client.post("/sessions/request", json={
            "user_id": "USER001",       # L1 Policy Analyst
            "shared_account_id": "SACC001", # HIGH risk LegacyERP
            "justification": "Low permission user requesting high risk account"
        })
        data = resp.json()
        valid = (
            resp.status_code == 201 and
            data.get("permission_granted") is False and
            data.get("status") == "PERMISSION_DENIED"
        )
        record_result("Permission Denial (L1 vs HIGH Account)", valid, f"Status: {data.get('status')}")
    except Exception as e:
        record_result("Permission Denial (L1 vs HIGH Account)", False, str(e))

    # -------------------------------------------------------------------------
    # Test 4: External Technical Partner Restriction Policy
    # -------------------------------------------------------------------------
    try:
        resp = client.post("/sessions/request", json={
            "user_id": "USER018",       # External Partner (ORG005)
            "shared_account_id": "SACC005", # CRITICAL risk CoreDatabase
            "justification": "Partner contractor requesting core database access"
        })
        data = resp.json()
        valid = (
            resp.status_code == 201 and
            data.get("permission_granted") is False and
            "External Technical Partner" in data.get("message", "")
        )
        record_result("External Partner Policy Restriction", valid, "Blocked from CRITICAL database")
    except Exception as e:
        record_result("External Partner Policy Restriction", False, str(e))

    # -------------------------------------------------------------------------
    # Test 5: Session Revocation
    # -------------------------------------------------------------------------
    try:
        resp = client.post(f"/sessions/{test1_session_id}/revoke", json={
            "reason": "Routine security revocation test",
            "revoked_by": "SECURITY_ADMIN_01"
        })
        data = resp.json()
        valid = (
            resp.status_code == 200 and
            data.get("status") == "SUCCESS" and
            data.get("session", {}).get("status") == "revoked"
        )
        record_result("Session Revocation", valid, f"Session {test1_session_id} revoked")
    except Exception as e:
        record_result("Session Revocation", False, str(e))

    # -------------------------------------------------------------------------
    # Test 6: Revoked Session Rejection (Action Blocked)
    # -------------------------------------------------------------------------
    try:
        resp = client.post("/actions/perform", json={
            "session_id": test1_session_id,
            "action": "Modify configuration",
            "sensitivity": "HIGH"
        })
        data = resp.json()
        valid = (
            resp.status_code == 201 and
            data.get("status") == "BLOCKED" and
            data.get("attribution_status") == "BLOCKED"
        )
        record_result("Revoked Session Action Blocked", valid, f"Action status: {data.get('status')}")
    except Exception as e:
        record_result("Revoked Session Action Blocked", False, str(e))

    # -------------------------------------------------------------------------
    # Test 7: Expired Session Rejection
    # -------------------------------------------------------------------------
    try:
        # Create fresh session then trigger with expired_session flag
        create_resp = client.post("/sessions/request", json={
            "user_id": "USER012",
            "shared_account_id": "SACC001",
            "duration_minutes": 30
        })
        fresh_sess_id = create_resp.json().get("session", {}).get("session_id")

        resp = client.post("/actions/perform", json={
            "session_id": fresh_sess_id,
            "action": "Approve transaction",
            "sensitivity": "HIGH",
            "force_scenario": "expired_session"
        })
        data = resp.json()
        valid = (
            resp.status_code == 201 and
            data.get("status") == "BLOCKED" and
            data.get("attribution_status") == "BLOCKED"
        )
        record_result("Expired Session Action Blocked", valid, f"Reason: {data.get('reason')}")
    except Exception as e:
        record_result("Expired Session Action Blocked", False, str(e))

    # -------------------------------------------------------------------------
    # Test 8: Invalid Session Rejection
    # -------------------------------------------------------------------------
    try:
        resp = client.post("/actions/perform", json={
            "session_id": "SES-NONEXISTENT-9999",
            "action": "View sensitive record",
            "sensitivity": "MEDIUM",
            "force_scenario": "invalid_session"
        })
        data = resp.json()
        valid = (
            resp.status_code == 201 and
            data.get("status") == "REJECTED" and
            data.get("attribution_status") == "BLOCKED"
        )
        record_result("Invalid Session Rejection", valid, f"Status: {data.get('status')}")
    except Exception as e:
        record_result("Invalid Session Rejection", False, str(e))

    # -------------------------------------------------------------------------
    # Test 9: Missing Delegation (Unattributed Baseline Action)
    # -------------------------------------------------------------------------
    try:
        resp = client.post("/actions/perform", json={
            "session_id": None,
            "shared_account_id": "SACC002",
            "action": "Export report",
            "sensitivity": "MEDIUM",
            "force_scenario": "missing_delegation"
        })
        data = resp.json()
        valid = (
            resp.status_code == 201 and
            data.get("status") == "BLOCKED" and
            data.get("attribution_status") == "UNATTRIBUTED" and
            data.get("user_id") == "UNATTRIBUTED"
        )
        record_result("Missing Delegation (Unattributed)", valid, f"Attribution: {data.get('attribution_status')}")
    except Exception as e:
        record_result("Missing Delegation (Unattributed)", False, str(e))

    # -------------------------------------------------------------------------
    # Test 10: Successful Individual Attribution & Explanation Layer
    # -------------------------------------------------------------------------
    try:
        # Create active valid session for USER012
        sess_resp = client.post("/sessions/request", json={
            "user_id": "USER012",
            "shared_account_id": "SACC001",
            "duration_minutes": 60,
            "justification": "Production change window execution"
        })
        active_sess_id = sess_resp.json().get("session", {}).get("session_id")

        resp = client.post("/actions/perform", json={
            "session_id": active_sess_id,
            "action": "Modify configuration",
            "sensitivity": "HIGH",
            "justification": "Routine server patch"
        })
        data = resp.json()
        exp = data.get("explanation", {})

        # Verify all 6 mandatory explanation questions
        has_6_answers = (
            exp.get("attributed_user") == "USER012" and
            exp.get("session_id") == active_sess_id and
            "shared_account" in exp and
            "permission_evaluation" in exp and
            len(exp.get("evidence_checklist", [])) >= 5 and
            "outcome_summary" in exp
        )

        valid = (
            resp.status_code == 201 and
            data.get("attribution_status") == "ATTRIBUTED" and
            data.get("user_id") == "USER012" and
            has_6_answers
        )
        test10_action_id = data.get("action_id")
        record_result("Individual Attribution & Explanation Layer", valid, f"Action: {test10_action_id}")
    except Exception as e:
        record_result("Individual Attribution & Explanation Layer", False, str(e))

    # -------------------------------------------------------------------------
    # Test 11: Conflicting Identity Evidence -> Human Review Queue
    # -------------------------------------------------------------------------
    try:
        resp = client.post("/actions/perform", json={
            "session_id": active_sess_id,
            "action": "Approve transaction",
            "sensitivity": "HIGH",
            "conflicting_user_id": "USER009",
            "force_scenario": "conflicting_evidence"
        })
        data = resp.json()
        valid = (
            resp.status_code == 201 and
            data.get("status") == "UNCERTAIN" and
            data.get("attribution_status") == "UNCERTAIN" and
            "review_id" in data
        )
        conflict_review_id = data.get("review_id")
        record_result("Conflicting Identity Evidence -> Human Review Queue", valid, f"Review ID: {conflict_review_id}")
    except Exception as e:
        record_result("Conflicting Identity Evidence -> Human Review Queue", False, str(e))

    # -------------------------------------------------------------------------
    # Test 12: Human Review Decision Workflow
    # -------------------------------------------------------------------------
    try:
        resp = client.post(f"/reviews/{conflict_review_id}/decide", json={
            "reviewer_id": "AUDITOR003",
            "decision": "CONFIRMED",
            "reason": "Corroborated by dual-custody audit log and supervisor approval ticket"
        })
        data = resp.json()
        valid = (
            resp.status_code == 200 and
            data.get("status") == "SUCCESS" and
            data.get("review", {}).get("review_status") == "CONFIRMED" and
            data.get("review", {}).get("reviewer_id") == "AUDITOR003"
        )
        record_result("Human Review Decision Workflow (CONFIRMED)", valid, "Review resolved by AUDITOR003")
    except Exception as e:
        record_result("Human Review Decision Workflow (CONFIRMED)", False, str(e))

    # -------------------------------------------------------------------------
    # Test 13: Dynamic Evaluation Benchmark Calculation
    # -------------------------------------------------------------------------
    try:
        resp = client.post("/evaluation/run")
        data = resp.json()
        metrics = data.get("metrics", {})
        summary = metrics.get("metrics_summary", {})
        proto_iar = summary.get("prototype_iar", 0.0)
        base_iar = summary.get("baseline_iar", 0.0)

        sensitive_iar = summary.get("sensitive_iar", 0.0)
        valid = (
            resp.status_code == 200 and
            base_iar == 0.0 and
            (proto_iar >= 75.0 or sensitive_iar >= 80.0) and
            "results_file" in data
        )
        record_result("Evaluation Benchmark Run & Persistence", valid, f"Baseline: {base_iar}% -> Prototype: {proto_iar}% (Sensitive IAR: {sensitive_iar}%)")
    except Exception as e:
        record_result("Evaluation Benchmark Run & Persistence", False, str(e))

    # -------------------------------------------------------------------------
    # Test 14: Comprehensive Audit Log Search & Filter
    # -------------------------------------------------------------------------
    try:
        resp = client.get("/actions/audit-log?attribution_status=ATTRIBUTED")
        data = resp.json()
        valid = resp.status_code == 200 and len(data) > 0 and all(r["attribution_status"] == "ATTRIBUTED" for r in data)
        record_result("Audit Log Filtering", valid, f"Found {len(data)} attributed audit records")
    except Exception as e:
        record_result("Audit Log Filtering", False, str(e))

    print("======================================================================")
    print(f"  VERIFICATION RESULTS:  Passed: {passed_count} / {total_tests}  |  Failed: {failed_count}")
    print("======================================================================")

    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
