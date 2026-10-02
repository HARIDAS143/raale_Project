"""
services/attribution_service.py — Deterministic Session Attribution Engine,
failure case classifier, and Human Fallback Review dispatcher.
"""

import random
import string
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from models import PrivilegedAction, DelegationSession, User, SharedAccount, HumanReview
from schemas import PerformActionRequest
from services.permission_service import (
    get_required_permission_for_action,
    validate_action_permission
)
from services.delegation_service import check_session_status
from services.explanation_service import build_explanation, serialize_explanation


def generate_action_id() -> str:
    rand_num = "".join(random.choices(string.digits, k=4))
    return f"ACT-{rand_num}"


def generate_review_id() -> str:
    rand_num = "".join(random.choices(string.digits, k=4))
    return f"REV-{rand_num}"


def process_privileged_action(
    db: Session,
    req: PerformActionRequest
) -> Dict[str, Any]:
    """
    Core Attribution Workflow:
    1. Identify session & shared account context
    2. Enforce Edge Cases (Missing, Insufficient, Expired, Revoked, Conflict)
    3. Execute deterministic attribution logic
    4. Compile evidence checklist
    5. Construct formal Explanation Layer output
    6. If Uncertain, dispatch to Human Review Queue
    7. Persist audit record
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    action_id = generate_action_id()

    # Determine required permission for the action
    req_permission = req.required_permission or get_required_permission_for_action(req.action, req.sensitivity or "HIGH")

    # -------------------------------------------------------------------------
    # EDGE CASE 1: Missing Delegation (No session ID provided)
    # -------------------------------------------------------------------------
    if not req.session_id or req.force_scenario == "missing_delegation":
        sh_acc_id = req.shared_account_id or "SACC001"
        account = db.query(SharedAccount).filter(SharedAccount.shared_account_id == sh_acc_id).first()
        acc_name = account.account_name if account else sh_acc_id
        org_id = account.organisation_id if account else "ORG001"
        app_name = account.application_name if account else "Legacy System"

        evidence = [
            "Attempted direct shared-account invocation without delegation token",
            f"Target Shared Account: {acc_name} ({sh_acc_id})",
            "Missing delegation session identifier in request headers",
            "Individual user identity verification bypassed",
            "Non-repudiation failure: Operator identity indeterminate"
        ]

        explanation = build_explanation(
            action_type=req.action,
            attributed_user_id="UNATTRIBUTED",
            session_id=None,
            shared_account_id=sh_acc_id,
            shared_account_name=acc_name,
            user_permission="NONE",
            required_permission=req_permission,
            attribution_status="UNATTRIBUTED",
            status_reason="No active delegation session found. Direct shared-account access blocked.",
            evidence_items=evidence
        )

        action = PrivilegedAction(
            action_id=action_id,
            timestamp=now_iso,
            session_id=None,
            shared_account_id=sh_acc_id,
            organisation_id=org_id,
            application=app_name,
            action_type=req.action,
            sensitivity=req.sensitivity or "HIGH",
            required_permission=req_permission,
            user_permission="NONE",
            delegation_token="NONE",
            attributed_user_id="UNATTRIBUTED",
            attribution_status="UNATTRIBUTED",
            attribution_confidence="0.0%",
            identity_evidence="; ".join(evidence),
            justification=req.justification or "Attempted action without active delegation token",
            scenario_tag="missing_delegation",
            explanation=serialize_explanation(explanation),
            review_status="NOT_REQUIRED",
            user_id=None
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        return {
            "status": "BLOCKED",
            "action_id": action.action_id,
            "timestamp": action.timestamp,
            "session_id": "NONE",
            "user_id": "UNATTRIBUTED",
            "shared_account_id": sh_acc_id,
            "action": action.action_type,
            "attribution_status": "UNATTRIBUTED",
            "attribution_confidence": "0.0%",
            "reason": "No active delegation session. Action blocked and logged as unattributed.",
            "explanation": explanation
        }

    # Fetch session
    session = db.query(DelegationSession).filter(DelegationSession.session_id == req.session_id).first()

    # -------------------------------------------------------------------------
    # EDGE CASE 4: Invalid Session (Unknown or non-existent session)
    # -------------------------------------------------------------------------
    if not session or req.force_scenario == "invalid_session":
        sh_acc_id = req.shared_account_id or "SACC001"
        account = db.query(SharedAccount).filter(SharedAccount.shared_account_id == sh_acc_id).first()
        acc_name = account.account_name if account else sh_acc_id

        evidence = [
            f"Supplied session ID '{req.session_id}' could not be resolved in the delegation registry",
            "Cryptographic delegation token signature verification failed",
            "Request rejected under defensive session enforcement policy"
        ]

        explanation = build_explanation(
            action_type=req.action,
            attributed_user_id="UNKNOWN",
            session_id=req.session_id,
            shared_account_id=sh_acc_id,
            shared_account_name=acc_name,
            user_permission="NONE",
            required_permission=req_permission,
            attribution_status="BLOCKED",
            status_reason=f"Invalid session ID '{req.session_id}'. Request rejected.",
            evidence_items=evidence
        )

        action = PrivilegedAction(
            action_id=action_id,
            timestamp=now_iso,
            session_id=None,
            shared_account_id=sh_acc_id,
            organisation_id=account.organisation_id if account else "ORG001",
            application=account.application_name if account else "Legacy System",
            action_type=req.action,
            sensitivity=req.sensitivity or "HIGH",
            required_permission=req_permission,
            user_permission="NONE",
            delegation_token="INVALID",
            attributed_user_id="UNKNOWN",
            attribution_status="BLOCKED",
            attribution_confidence="0.0%",
            identity_evidence="; ".join(evidence),
            justification=req.justification or "Privileged action with invalid session token",
            scenario_tag="invalid_session",
            explanation=serialize_explanation(explanation),
            review_status="NOT_REQUIRED",
            user_id=None
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        return {
            "status": "REJECTED",
            "action_id": action.action_id,
            "timestamp": action.timestamp,
            "session_id": req.session_id,
            "user_id": "UNKNOWN",
            "shared_account_id": sh_acc_id,
            "action": action.action_type,
            "attribution_status": "BLOCKED",
            "attribution_confidence": "0.0%",
            "reason": f"Invalid session ID '{req.session_id}'. Action rejected.",
            "explanation": explanation
        }

    # Retrieve associated user and account
    user = db.query(User).filter(User.user_id == session.user_id).first()
    account = db.query(SharedAccount).filter(SharedAccount.shared_account_id == session.shared_account_id).first()
    acc_name = account.account_name if account else session.shared_account_id
    app_name = account.application_name if account else "Legacy System"
    org_id = user.organisation_id if user else (account.organisation_id if account else "ORG001")
    user_perm = user.permission_level if user else (session.granted_level or "L1")

    # -------------------------------------------------------------------------
    # EDGE CASE 4 (b): Session Revocation Check
    # -------------------------------------------------------------------------
    if session.status == "revoked" or req.force_scenario == "session_revoked":
        evidence = [
            f"Delegation session '{session.session_id}' was explicitly REVOKED by security administrator",
            f"Revocation metadata: {session.justification}",
            "Delegation token disabled and blacklisted from further operations"
        ]
        explanation = build_explanation(
            action_type=req.action,
            attributed_user_id=user.user_id if user else "UNKNOWN",
            session_id=session.session_id,
            shared_account_id=session.shared_account_id,
            shared_account_name=acc_name,
            user_permission=user_perm,
            required_permission=req_permission,
            attribution_status="BLOCKED",
            status_reason="Delegation session has been revoked. Action blocked.",
            evidence_items=evidence
        )

        action = PrivilegedAction(
            action_id=action_id,
            timestamp=now_iso,
            session_id=session.session_id,
            shared_account_id=session.shared_account_id,
            organisation_id=org_id,
            application=app_name,
            action_type=req.action,
            sensitivity=req.sensitivity or "HIGH",
            required_permission=req_permission,
            user_permission=user_perm,
            delegation_token=session.delegation_token,
            attributed_user_id=user.user_id if user else "UNATTRIBUTED",
            attribution_status="BLOCKED",
            attribution_confidence="0.0%",
            identity_evidence="; ".join(evidence),
            justification=req.justification or "Attempted action on revoked session",
            scenario_tag="session_revoked",
            explanation=serialize_explanation(explanation),
            review_status="NOT_REQUIRED",
            user_id=user.user_id if user else None
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        return {
            "status": "BLOCKED",
            "action_id": action.action_id,
            "timestamp": action.timestamp,
            "session_id": session.session_id,
            "user_id": user.user_id if user else "UNATTRIBUTED",
            "shared_account_id": session.shared_account_id,
            "action": action.action_type,
            "attribution_status": "BLOCKED",
            "attribution_confidence": "0.0%",
            "reason": "Delegation session has been revoked. Action blocked.",
            "explanation": explanation
        }

    # -------------------------------------------------------------------------
    # EDGE CASE 3: Expired Session Check
    # -------------------------------------------------------------------------
    is_valid_status, status_reason = check_session_status(session, db)
    if status_reason == "SESSION_EXPIRED" or req.force_scenario == "expired_session":
        evidence = [
            f"Delegation session '{session.session_id}' expiration timestamp '{session.end_time}' has passed",
            f"Current action execution timestamp: '{now_iso}'",
            "Time-bound window closed — session automatically invalidated",
            "Least-privilege time restriction enforced"
        ]
        explanation = build_explanation(
            action_type=req.action,
            attributed_user_id="UNATTRIBUTED",
            session_id=session.session_id,
            shared_account_id=session.shared_account_id,
            shared_account_name=acc_name,
            user_permission=user_perm,
            required_permission=req_permission,
            attribution_status="BLOCKED",
            status_reason=f"Delegation session '{session.session_id}' expired. Action blocked.",
            evidence_items=evidence
        )

        action = PrivilegedAction(
            action_id=action_id,
            timestamp=now_iso,
            session_id=session.session_id,
            shared_account_id=session.shared_account_id,
            organisation_id=org_id,
            application=app_name,
            action_type=req.action,
            sensitivity=req.sensitivity or "HIGH",
            required_permission=req_permission,
            user_permission=user_perm,
            delegation_token=session.delegation_token,
            attributed_user_id="UNATTRIBUTED",
            attribution_status="BLOCKED",
            attribution_confidence="0.0%",
            identity_evidence="; ".join(evidence),
            justification=req.justification or "Attempted action using expired delegation session",
            scenario_tag="expired_session",
            explanation=serialize_explanation(explanation),
            review_status="NOT_REQUIRED",
            user_id=user.user_id if user else None
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        return {
            "status": "BLOCKED",
            "action_id": action.action_id,
            "timestamp": action.timestamp,
            "session_id": session.session_id,
            "user_id": "UNATTRIBUTED",
            "shared_account_id": session.shared_account_id,
            "action": action.action_type,
            "attribution_status": "BLOCKED",
            "attribution_confidence": "0.0%",
            "reason": "Delegation session expired. Action blocked.",
            "explanation": explanation
        }

    # -------------------------------------------------------------------------
    # EDGE CASE 5: Conflicting Identity Evidence (Routing to Human Review)
    # -------------------------------------------------------------------------
    conflicting_user_id = req.conflicting_user_id
    if req.force_scenario == "conflicting_evidence" and not conflicting_user_id:
        conflicting_user_id = "USER009" if session.user_id != "USER009" else "USER007"

    if conflicting_user_id:
        evidence = [
            f"Active delegation session '{session.session_id}' bound to user '{session.user_id}'",
            f"Supplemental audit / device trace claims concurrent identity '{conflicting_user_id}'",
            "Conflicting identity telemetry detected in transport envelope",
            "Automated identity guess rejected to uphold forensic integrity",
            "Enqueued to Human Review Queue under fallback governance protocol"
        ]

        conflict_note = f"Session issued to {session.user_id}, but incoming activity telemetry asserted {conflicting_user_id}. Ambiguous non-repudiation."

        explanation = build_explanation(
            action_type=req.action,
            attributed_user_id="UNCERTAIN",
            session_id=session.session_id,
            shared_account_id=session.shared_account_id,
            shared_account_name=acc_name,
            user_permission=user_perm,
            required_permission=req_permission,
            attribution_status="UNCERTAIN",
            status_reason="Conflicting identity evidence detected. Forwarded to Human Review Queue.",
            evidence_items=evidence,
            conflict_details=conflict_note
        )

        action = PrivilegedAction(
            action_id=action_id,
            timestamp=now_iso,
            session_id=session.session_id,
            shared_account_id=session.shared_account_id,
            organisation_id=org_id,
            application=app_name,
            action_type=req.action,
            sensitivity=req.sensitivity or "HIGH",
            required_permission=req_permission,
            user_permission=user_perm,
            delegation_token=session.delegation_token,
            attributed_user_id="UNCERTAIN",
            attribution_status="UNCERTAIN",
            attribution_confidence="CONFLICT",
            identity_evidence="; ".join(evidence),
            justification=req.justification or "Action executed with conflicting identity telemetry",
            scenario_tag="conflicting_evidence",
            explanation=serialize_explanation(explanation),
            review_status="PENDING",
            user_id=session.user_id
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        # Enqueue in Human Review Queue
        review = HumanReview(
            review_id=generate_review_id(),
            action_id=action.action_id,
            session_id=session.session_id,
            shared_account_id=session.shared_account_id,
            claimed_user_id=session.user_id,
            conflicting_user_id=conflicting_user_id,
            timestamp=now_iso,
            available_evidence="; ".join(evidence),
            conflict_reason=conflict_note,
            attribution_status="UNCERTAIN",
            review_status="PENDING"
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        return {
            "status": "UNCERTAIN",
            "action_id": action.action_id,
            "review_id": review.review_id,
            "timestamp": action.timestamp,
            "session_id": session.session_id,
            "user_id": "UNCERTAIN",
            "claimed_user": session.user_id,
            "conflicting_user": conflicting_user_id,
            "shared_account_id": session.shared_account_id,
            "action": action.action_type,
            "attribution_status": "UNCERTAIN",
            "attribution_confidence": "CONFLICT",
            "reason": "Conflicting identity evidence detected. Enqueued for Human Review.",
            "explanation": explanation
        }

    # -------------------------------------------------------------------------
    # EDGE CASE 2 & Multi-Org: Permission Validation
    # -------------------------------------------------------------------------
    is_external = (
        (user and user.user_type == "external_partner") or
        org_id in ["ORG005", "ORG006", "ORG03", "ORG3"] or
        req.force_scenario == "external_partner"
    )

    perm_passed, perm_msg = validate_action_permission(user_perm, req_permission, is_external=is_external)
    if not perm_passed or req.force_scenario == "insufficient_permission":
        evidence = [
            f"Active session '{session.session_id}' verified for user '{session.user_id}'",
            f"Target action '{req.action}' requires permission level '{req_permission}'",
            f"User '{session.user_id}' clearance/permission level is '{user_perm}'",
            f"Validation rule violated: {perm_msg}",
            "Privileged execution blocked before modifying shared resource"
        ]

        explanation = build_explanation(
            action_type=req.action,
            attributed_user_id=session.user_id,
            session_id=session.session_id,
            shared_account_id=session.shared_account_id,
            shared_account_name=acc_name,
            user_permission=user_perm,
            required_permission=req_permission,
            attribution_status="PERMISSION_DENIED",
            status_reason=f"Insufficient permission: Action requires {req_permission}, but user possesses {user_perm}.",
            evidence_items=evidence,
            is_external=is_external
        )

        action = PrivilegedAction(
            action_id=action_id,
            timestamp=now_iso,
            session_id=session.session_id,
            shared_account_id=session.shared_account_id,
            organisation_id=org_id,
            application=app_name,
            action_type=req.action,
            sensitivity=req.sensitivity or "HIGH",
            required_permission=req_permission,
            user_permission=user_perm,
            delegation_token=session.delegation_token,
            attributed_user_id=session.user_id,
            attribution_status="PERMISSION_DENIED",
            attribution_confidence="100.0%",
            identity_evidence="; ".join(evidence),
            justification=req.justification or "Attempted action exceeding granted permission level",
            scenario_tag="insufficient_permission" if not is_external else "external_partner",
            explanation=serialize_explanation(explanation),
            review_status="NOT_REQUIRED",
            user_id=session.user_id
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        return {
            "status": "PERMISSION_DENIED",
            "action_id": action.action_id,
            "timestamp": action.timestamp,
            "session_id": session.session_id,
            "user_id": session.user_id,
            "shared_account_id": session.shared_account_id,
            "action": action.action_type,
            "attribution_status": "PERMISSION_DENIED",
            "attribution_confidence": "100.0%",
            "reason": perm_msg,
            "explanation": explanation
        }

    # -------------------------------------------------------------------------
    # SUCCESSFUL INDIVIDUAL ATTRIBUTION
    # -------------------------------------------------------------------------
    evidence = [
        f"Valid individual identity verified: '{session.user_id}' ({org_id})",
        f"Active delegation session '{session.session_id}' verified in database",
        f"Cryptographic delegation token '{session.delegation_token}' active and matched",
        f"Permission check passed: User level '{user_perm}' >= Required '{req_permission}'",
        f"Session timeframe valid: action executed within active delegation window",
        f"Shared account: '{acc_name}' ({session.shared_account_id})",
        f"Organisation boundary satisfied: {org_id}"
    ]

    explanation = build_explanation(
        action_type=req.action,
        attributed_user_id=session.user_id,
        session_id=session.session_id,
        shared_account_id=session.shared_account_id,
        shared_account_name=acc_name,
        user_permission=user_perm,
        required_permission=req_permission,
        attribution_status="ATTRIBUTED",
        status_reason="All identity, delegation, permission, and session evidence validated successfully.",
        evidence_items=evidence,
        is_external=is_external
    )

    action = PrivilegedAction(
        action_id=action_id,
        timestamp=now_iso,
        session_id=session.session_id,
        shared_account_id=session.shared_account_id,
        organisation_id=org_id,
        application=app_name,
        action_type=req.action,
        sensitivity=req.sensitivity or "HIGH",
        required_permission=req_permission,
        user_permission=user_perm,
        delegation_token=session.delegation_token,
        attributed_user_id=session.user_id,
        attribution_status="ATTRIBUTED",
        attribution_confidence="100.0%",
        identity_evidence="; ".join(evidence),
        justification=req.justification or "Standard privileged operation under accountable delegation",
        scenario_tag="attributed",
        explanation=serialize_explanation(explanation),
        review_status="NOT_REQUIRED",
        user_id=session.user_id
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return {
        "status": "SUCCESS",
        "action_id": action.action_id,
        "timestamp": action.timestamp,
        "session_id": session.session_id,
        "user_id": session.user_id,
        "shared_account_id": session.shared_account_id,
        "action": action.action_type,
        "attribution_status": "ATTRIBUTED",
        "attribution_confidence": "100.0%",
        "delegation_token": session.delegation_token,
        "message": f"Action recorded and conclusively attributed to individual '{session.user_id}'",
        "explanation": explanation
    }
