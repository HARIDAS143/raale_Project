"""
routers/actions.py — Privileged action simulator, deterministic session attribution,
explanation layer API, and comprehensive forensic audit log.
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models import PrivilegedAction, SystemLog, User, SharedAccount
from schemas import PerformActionRequest
from services.attribution_service import process_privileged_action
from services.evaluation_service import compute_metrics

router = APIRouter(prefix="/actions", tags=["Actions"])


def _parse_explanation(raw_text: Optional[str]):
    if not raw_text:
        return None
    try:
        return json.loads(raw_text)
    except Exception:
        return {"formatted_text": raw_text}


@router.get("/privileged")
def list_privileged_actions(
    status_filter: Optional[str] = Query(None, alias="status"),
    org_filter: Optional[str] = Query(None, alias="organisation"),
    account_filter: Optional[str] = Query(None, alias="account"),
    db: Session = Depends(get_db)
):
    query = db.query(PrivilegedAction)
    if status_filter:
        query = query.filter(PrivilegedAction.attribution_status == status_filter.upper())
    if org_filter:
        query = query.filter(PrivilegedAction.organisation_id == org_filter.upper())
    if account_filter:
        query = query.filter(PrivilegedAction.shared_account_id == account_filter.upper())

    actions = query.order_by(PrivilegedAction.timestamp.desc()).all()
    result = []
    for a in actions:
        user = db.query(User).filter(User.user_id == a.user_id).first() if a.user_id else None
        acc  = db.query(SharedAccount).filter(
            SharedAccount.shared_account_id == a.shared_account_id
        ).first()

        result.append({
            "action_id":              a.action_id,
            "timestamp":              a.timestamp,
            "session_id":             a.session_id or "NONE",
            "user_id":                a.attributed_user_id if a.attributed_user_id not in ["NONE", ""] else (a.user_id or "UNATTRIBUTED"),
            "shared_account_id":      a.shared_account_id,
            "account_name":           acc.account_name if acc else a.shared_account_id,
            "organisation_id":        a.organisation_id,
            "application":            a.application,
            "action":                 a.action_type,
            "action_type":            a.action_type,
            "sensitivity":            a.sensitivity,
            "required_permission":    a.required_permission,
            "user_permission":        a.user_permission,
            "delegation_token":       a.delegation_token,
            "attributed_user_id":     a.attributed_user_id,
            "user_role":              user.role if user else "N/A",
            "user_type":              user.user_type if user else "N/A",
            "attribution_status":     a.attribution_status,
            "attribution_confidence": a.attribution_confidence,
            "identity_evidence":      a.identity_evidence,
            "justification":          a.justification,
            "scenario_tag":           a.scenario_tag,
            "explanation":            _parse_explanation(a.explanation),
            "review_status":          a.review_status,
        })
    return result


@router.get("/baseline")
def list_baseline_logs(db: Session = Depends(get_db)):
    logs = db.query(SystemLog).order_by(SystemLog.timestamp.desc()).all()
    result = []
    for log in logs:
        acc = db.query(SharedAccount).filter(
            SharedAccount.shared_account_id == log.shared_account_id
        ).first()
        result.append({
            "log_id":                log.log_id,
            "timestamp":             log.timestamp,
            "session_id":            log.session_id,
            "shared_account_id":     log.shared_account_id,
            "account_name":          acc.account_name if acc else "N/A",
            "application":           log.application,
            "action":                log.action,
            "organisation_id":       log.organisation_id,
            "device_id":             log.device_id,
            "identity_evidence":     log.identity_evidence,
            "log_status":            log.log_status,
            "individual_identified": log.individual_identified,
            "sensitivity":           log.sensitivity,
        })
    return result


@router.get("/attribution-rate")
def get_attribution_rate(db: Session = Depends(get_db)):
    metrics = compute_metrics(db)
    return {
        "baseline": metrics["baseline"],
        "prototype": metrics["prototype"],
        "improvement": metrics["metrics_summary"]["improvement"],
        "summary": metrics["metrics_summary"]
    }


@router.post("/perform", status_code=status.HTTP_201_CREATED)
def perform_action(req: PerformActionRequest, db: Session = Depends(get_db)):
    """
    Workflow Steps 6-11:
    6. Individual user performs a privileged action within delegation session
    7. System captures contextual activity evidence
    8. System runs deterministic attribution engine & failure case checks
    9. System constructs full structured Explanation Layer rationale
    10. If Uncertain, action is enqueued to Human Review Queue
    11. Immutable audit record is generated
    """
    result = process_privileged_action(db, req)
    return result


@router.get("/audit-log")
def get_audit_log(
    user_id: Optional[str] = None,
    organisation_id: Optional[str] = None,
    shared_account_id: Optional[str] = None,
    action_type: Optional[str] = None,
    attribution_status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(PrivilegedAction)

    if user_id and isinstance(user_id, str):
        query = query.filter((PrivilegedAction.attributed_user_id == user_id) | (PrivilegedAction.user_id == user_id))
    if organisation_id and isinstance(organisation_id, str):
        query = query.filter(PrivilegedAction.organisation_id == organisation_id.upper())
    if shared_account_id and isinstance(shared_account_id, str):
        query = query.filter(PrivilegedAction.shared_account_id == shared_account_id.upper())
    if action_type and isinstance(action_type, str):
        query = query.filter(PrivilegedAction.action_type.ilike(f"%{action_type}%"))
    if attribution_status and isinstance(attribution_status, str):
        query = query.filter(PrivilegedAction.attribution_status == attribution_status.upper())
    if risk_level and isinstance(risk_level, str):
        query = query.filter(PrivilegedAction.sensitivity == risk_level.upper())

    actions = query.order_by(PrivilegedAction.timestamp.desc()).all()
    audit_records = []
    for a in actions:
        acc = db.query(SharedAccount).filter(SharedAccount.shared_account_id == a.shared_account_id).first()
        user = db.query(User).filter(User.user_id == a.attributed_user_id).first() if a.attributed_user_id not in ["NONE", "UNATTRIBUTED", "UNKNOWN", "UNCERTAIN"] else None

        audit_records.append({
            "action_id":          a.action_id,
            "timestamp":          a.timestamp,
            "user_id":            a.attributed_user_id if a.attributed_user_id != "NONE" else (a.user_id or "UNATTRIBUTED"),
            "user_name":          f"User {a.attributed_user_id}" if user else a.attributed_user_id,
            "organisation_id":    a.organisation_id,
            "session_id":         a.session_id or "NONE",
            "shared_account":     acc.account_name if acc else a.shared_account_id,
            "shared_account_id":  a.shared_account_id,
            "application":        a.application,
            "action":             a.action_type,
            "sensitivity":        a.sensitivity,
            "user_permission":    a.user_permission,
            "required_permission":a.required_permission,
            "attribution_status": a.attribution_status,
            "attribution_confidence": a.attribution_confidence,
            "delegation_token":   a.delegation_token,
            "identity_evidence":  a.identity_evidence,
            "explanation":        _parse_explanation(a.explanation),
            "review_status":      a.review_status,
        })
    return audit_records


@router.get("/{action_id}/explanation")
def get_action_explanation(action_id: str, db: Session = Depends(get_db)):
    action = db.query(PrivilegedAction).filter(PrivilegedAction.action_id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found.")

    explanation = _parse_explanation(action.explanation)
    if not explanation:
        raise HTTPException(status_code=404, detail=f"No structured explanation found for action '{action_id}'.")

    return {
        "action_id": action.action_id,
        "action_type": action.action_type,
        "timestamp": action.timestamp,
        "attribution_status": action.attribution_status,
        "explanation": explanation
    }
