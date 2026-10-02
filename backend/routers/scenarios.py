"""
routers/scenarios.py — Demonstration triggers for Review 2 failure cases and edge cases.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, SharedAccount, DelegationSession
from schemas import PerformActionRequest
from services.delegation_service import create_delegation_session
from services.attribution_service import process_privileged_action

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.post("/trigger/{scenario_key}")
def trigger_scenario(scenario_key: str, db: Session = Depends(get_db)):
    """
    Triggers one of the predefined failure or edge case scenarios for demonstration:
    - missing_delegation: Edge Case 1
    - insufficient_permission: Edge Case 2
    - expired_session: Edge Case 3
    - invalid_session: Edge Case 4
    - conflicting_evidence: Edge Case 5
    - external_partner_restriction: Multi-Org External Partner restriction
    - normal_success: Legitimate accountable privileged action
    """
    key = scenario_key.lower().strip()

    if key == "missing_delegation":
        req = PerformActionRequest(
            session_id=None,
            shared_account_id="SACC001",
            action="Modify configuration",
            sensitivity="CRITICAL",
            justification="Simulation: Attempting action without delegation session token",
            force_scenario="missing_delegation"
        )
        return {
            "scenario": "Edge Case 1 — Missing Delegation",
            "description": "User attempts to perform a sensitive action without a valid delegation session.",
            "expected_outcome": "Action: BLOCKED, Attribution: UNATTRIBUTED, Reason: No active delegation",
            "execution_trace": process_privileged_action(db, req)
        }

    elif key == "insufficient_permission":
        # Create a valid session for L1 user on a medium account, but user attempts L4 action
        user = db.query(User).filter(User.permission_level == "L1").first()
        account = db.query(SharedAccount).filter(SharedAccount.risk_level == "LOW").first()
        if not account:
            account = db.query(SharedAccount).first()

        _, session, _, _ = create_delegation_session(
            db, user, account, duration_minutes=30,
            justification="Demo session for permission boundary testing"
        )

        req = PerformActionRequest(
            session_id=session.session_id,
            action="Modify configuration", # requires L4
            sensitivity="CRITICAL",
            required_permission="L4",
            justification="Simulation: L1 user attempting high-risk L4 configuration modification",
            force_scenario="insufficient_permission"
        )
        return {
            "scenario": "Edge Case 2 — Insufficient Permission",
            "description": "A low-level user (L1) attempts to perform a high-risk administrative action (L4).",
            "expected_outcome": "Access: DENIED, Reason: Insufficient permission",
            "execution_trace": process_privileged_action(db, req)
        }

    elif key == "expired_session":
        # Create a session and set end_time in the past
        user = db.query(User).filter(User.permission_level.in_(["L3", "L4"])).first()
        account = db.query(SharedAccount).filter(SharedAccount.risk_level != "CRITICAL").first()
        _, session, _, _ = create_delegation_session(
            db, user, account, duration_minutes=1,
            justification="Demo session to test time-bound expiration"
        )
        # Mark expired in past
        session.start_time = "2026-01-01T10:00:00Z"
        session.end_time = "2026-01-01T10:15:00Z"
        session.status = "expired"
        db.commit()

        req = PerformActionRequest(
            session_id=session.session_id,
            action="Export report",
            sensitivity="HIGH",
            justification="Simulation: Action attempted against an expired delegation session",
            force_scenario="expired_session"
        )
        return {
            "scenario": "Edge Case 3 — Expired Session",
            "description": "A valid session expires before the sensitive action is executed.",
            "expected_outcome": "Action: BLOCKED, Attribution: UNATTRIBUTED, Reason: Session expired",
            "execution_trace": process_privileged_action(db, req)
        }

    elif key == "invalid_session":
        req = PerformActionRequest(
            session_id="SES-FAKE-9999",
            shared_account_id="SACC001",
            action="Change access configuration",
            sensitivity="HIGH",
            justification="Simulation: Action attempted with forged or unregistered session ID",
            force_scenario="invalid_session"
        )
        return {
            "scenario": "Edge Case 4 — Invalid Session",
            "description": "A request contains an unknown or forged session ID.",
            "expected_outcome": "Action: REJECTED, Reason: Invalid session",
            "execution_trace": process_privileged_action(db, req)
        }

    elif key == "conflicting_evidence":
        # Create a valid session for USER007, but supply conflicting evidence for USER009
        user = db.query(User).filter(User.user_id == "USER007").first()
        if not user:
            user = db.query(User).first()
        account = db.query(SharedAccount).filter(SharedAccount.risk_level == "MEDIUM").first()
        _, session, _, _ = create_delegation_session(
            db, user, account, duration_minutes=30,
            justification="Demo session for forensic conflict demonstration"
        )

        req = PerformActionRequest(
            session_id=session.session_id,
            action="Approve transaction",
            sensitivity="HIGH",
            justification="Simulation: Session belongs to USER007, but concurrent log evidence claims USER009",
            conflicting_user_id="USER009",
            force_scenario="conflicting_evidence"
        )
        return {
            "scenario": "Edge Case 5 — Conflicting Identity Evidence",
            "description": "Session belongs to USER007, but log/device evidence points to USER009. System refuses to blindly guess.",
            "expected_outcome": "Attribution: UNCERTAIN, Fallback: Routed to Human Review Queue",
            "execution_trace": process_privileged_action(db, req)
        }

    elif key == "external_partner_restriction":
        partner = db.query(User).filter(User.user_type == "external_partner").first()
        if not partner:
            partner = db.query(User).filter(User.organisation_id.in_(["ORG005", "ORG006"])).first()
        account = db.query(SharedAccount).filter(SharedAccount.risk_level == "LOW").first()
        _, session, _, _ = create_delegation_session(
            db, partner, account, duration_minutes=30,
            justification="Technical vendor maintenance delegation session"
        )

        req = PerformActionRequest(
            session_id=session.session_id,
            action="Modify configuration",
            sensitivity="CRITICAL",
            required_permission="L4",
            justification="Simulation: External vendor contractor attempting L4 system modification",
            force_scenario="external_partner"
        )
        return {
            "scenario": "Multi-Organisation — External Partner Restriction",
            "description": "External partner contractor attempts to execute administrative L4 operation.",
            "expected_outcome": "Access: DENIED, Reason: External technical partner privileges restricted to max L2",
            "execution_trace": process_privileged_action(db, req)
        }

    elif key == "normal_success":
        admin = db.query(User).filter(User.permission_level == "L4").first()
        account = db.query(SharedAccount).filter(SharedAccount.risk_level.in_(["HIGH", "CRITICAL"])).first()
        _, session, _, _ = create_delegation_session(
            db, admin, account, duration_minutes=45,
            justification="Legitimate routine security administration maintenance"
        )

        req = PerformActionRequest(
            session_id=session.session_id,
            action="Modify configuration",
            sensitivity="HIGH",
            justification="Authorized administrative system patch application"
        )
        return {
            "scenario": "Legitimate Privileged Operation (Success)",
            "description": "Authenticated L4 security administrator performs authorized configuration modification under active delegation session.",
            "expected_outcome": "Attribution: ATTRIBUTED (100%), Explanation: Structured forensic evidence generated",
            "execution_trace": process_privileged_action(db, req)
        }

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario key '{scenario_key}'. Choose from: missing_delegation, insufficient_permission, expired_session, invalid_session, conflicting_evidence, external_partner_restriction, normal_success"
        )
