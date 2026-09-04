"""
routers/actions.py — Privileged action execution and audit logging endpoints for Phase 4 prototype.
"""

import random
import string
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import PrivilegedAction, SystemLog, User, SharedAccount, DelegationSession
from schemas import PerformActionRequest

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.get("/privileged")
def list_privileged_actions(db: Session = Depends(get_db)):
    actions = db.query(PrivilegedAction).order_by(PrivilegedAction.timestamp.desc()).all()
    result  = []
    for a in actions:
        user = db.query(User).filter(User.user_id == a.user_id).first() if a.user_id else None
        acc  = db.query(SharedAccount).filter(
            SharedAccount.shared_account_id == a.shared_account_id
        ).first()
        result.append({
            "action_id":              a.action_id,
            "timestamp":              a.timestamp,
            "session_id":             a.session_id,
            "user_id":                a.attributed_user_id if a.attributed_user_id != "NONE" else (a.user_id or "UNATTRIBUTED"),
            "shared_account_id":      a.shared_account_id,
            "account_name":           acc.account_name if acc else "N/A",
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
        })
    return result


@router.get("/baseline")
def list_baseline_logs(db: Session = Depends(get_db)):
    logs   = db.query(SystemLog).order_by(SystemLog.timestamp.desc()).all()
    result = []
    for log in logs:
        acc = db.query(SharedAccount).filter(
            SharedAccount.shared_account_id == log.shared_account_id
        ).first()
        result.append({
            "log_id":               log.log_id,
            "timestamp":            log.timestamp,
            "session_id":           log.session_id,
            "shared_account_id":    log.shared_account_id,
            "account_name":         acc.account_name if acc else "N/A",
            "application":          log.application,
            "action":               log.action,
            "organisation_id":      log.organisation_id,
            "device_id":            log.device_id,
            "identity_evidence":    log.identity_evidence,
            "log_status":           log.log_status,
            "individual_identified":log.individual_identified,
            "sensitivity":          log.sensitivity,
        })
    return result


@router.get("/attribution-rate")
def get_attribution_rate(db: Session = Depends(get_db)):
    # Baseline
    baseline_total     = db.query(SystemLog).count()
    baseline_sensitive = db.query(SystemLog).filter(
        SystemLog.sensitivity.in_(["HIGH","CRITICAL"])
    ).count()

    # Prototype
    proto_total        = db.query(PrivilegedAction).count()
    proto_attributed   = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "ATTRIBUTED"
    ).count()
    proto_unattr       = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "UNATTRIBUTED"
    ).count()
    proto_denied       = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "PERMISSION_DENIED"
    ).count()
    proto_sensitive    = db.query(PrivilegedAction).filter(
        PrivilegedAction.sensitivity.in_(["HIGH","CRITICAL"])
    ).count()
    proto_sens_attr    = db.query(PrivilegedAction).filter(
        PrivilegedAction.sensitivity.in_(["HIGH","CRITICAL"]),
        PrivilegedAction.attribution_status == "ATTRIBUTED",
    ).count()

    baseline_iar  = 0.0
    prototype_iar = round(proto_attributed / proto_total * 100, 2) if proto_total else 0.0
    sensitive_iar = round(proto_sens_attr  / proto_sensitive * 100, 2) if proto_sensitive else 0.0

    return {
        "baseline": {
            "total_logs":        baseline_total,
            "sensitive_actions": baseline_sensitive,
            "attributed":        0,
            "unattributed":      baseline_total,
            "iar":               baseline_iar,
        },
        "prototype": {
            "total_actions":       proto_total,
            "attributed":          proto_attributed,
            "unattributed":        proto_unattr,
            "permission_denied":   proto_denied,
            "sensitive_actions":   proto_sensitive,
            "sensitive_attributed":proto_sens_attr,
            "iar":                 prototype_iar,
            "sensitive_iar":       sensitive_iar,
        },
        "improvement": round(prototype_iar - baseline_iar, 2),
    }


@router.post("/perform", status_code=status.HTTP_201_CREATED)
def perform_action(req: PerformActionRequest, db: Session = Depends(get_db)):
    """
    Workflow Steps 6-9:
    6. User performs a sensitive action
    7. System records the action
    8. System attributes the action to the individual user (Deterministic Session Attribution)
    9. Audit record is created
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rand_num = "".join(random.choices(string.digits, k=4))
    action_id = f"ACT-{rand_num}"

    session = None
    if req.session_id:
        session = db.query(DelegationSession).filter(DelegationSession.session_id == req.session_id).first()

    if session and session.user_id:
        # Deterministic Session Attribution
        user = db.query(User).filter(User.user_id == session.user_id).first()
        acc = db.query(SharedAccount).filter(SharedAccount.shared_account_id == session.shared_account_id).first()

        attributed_user_id = session.user_id
        attribution_status = "ATTRIBUTED"
        attribution_confidence = "100.0"
        delegation_token = session.delegation_token
        shared_account_id = session.shared_account_id
        org_id = user.organisation_id if user else (acc.organisation_id if acc else "ORG01")
        app_name = acc.application_name if acc else "Legacy App"
        user_perm = user.permission_level if user else "L1"
        user_db_id = user.user_id if user else None
        evidence = f"Token: {delegation_token} | Session: {session.session_id} | User: {user.user_id if user else 'Unknown'}"
    else:
        # Baseline/Unattributed action without active delegation session
        sh_acc_id = req.shared_account_id or "ACC001"
        acc = db.query(SharedAccount).filter(SharedAccount.shared_account_id == sh_acc_id).first()

        attributed_user_id = "UNATTRIBUTED"
        attribution_status = "UNATTRIBUTED"
        attribution_confidence = "0.0"
        delegation_token = "NONE"
        shared_account_id = sh_acc_id
        org_id = acc.organisation_id if acc else "ORG01"
        app_name = acc.application_name if acc else "Legacy App"
        user_perm = "NONE"
        user_db_id = req.user_id
        evidence = "No active delegation session token found"

    new_action = PrivilegedAction(
        action_id=action_id,
        timestamp=now_iso,
        session_id=req.session_id or f"SES-UNKN-{rand_num}",
        shared_account_id=shared_account_id,
        organisation_id=org_id,
        application=app_name,
        action_type=req.action,
        sensitivity=req.sensitivity or "HIGH",
        required_permission="L2",
        user_permission=user_perm,
        delegation_token=delegation_token,
        attributed_user_id=attributed_user_id,
        attribution_status=attribution_status,
        attribution_confidence=attribution_confidence,
        identity_evidence=evidence,
        justification=req.justification or "Privileged action executed in session",
        scenario_tag="prototype_interactive",
        user_id=user_db_id
    )

    db.add(new_action)
    db.commit()
    db.refresh(new_action)

    return {
        "status": "SUCCESS",
        "action_id": new_action.action_id,
        "timestamp": new_action.timestamp,
        "session_id": new_action.session_id,
        "user_id": attributed_user_id,
        "shared_account_id": new_action.shared_account_id,
        "action": new_action.action_type,
        "attribution_status": new_action.attribution_status,
        "delegation_token": new_action.delegation_token,
        "message": f"Action recorded and attributed to {attributed_user_id}"
    }


@router.get("/audit-log")
def get_audit_log(db: Session = Depends(get_db)):
    actions = db.query(PrivilegedAction).order_by(PrivilegedAction.timestamp.desc()).all()
    audit_records = []
    for a in actions:
        acc = db.query(SharedAccount).filter(SharedAccount.shared_account_id == a.shared_account_id).first()
        user = db.query(User).filter(User.user_id == a.attributed_user_id).first() if a.attributed_user_id not in ["NONE", "UNATTRIBUTED"] else None
        
        audit_records.append({
            "timestamp": a.timestamp,
            "user_id": a.attributed_user_id if a.attributed_user_id != "NONE" else (a.user_id or "UNATTRIBUTED"),
            "user_name": f"User {a.attributed_user_id}" if user or (a.attributed_user_id and a.attributed_user_id.startswith("USER")) else "Unattributed",
            "session_id": a.session_id,
            "shared_account": acc.account_name if acc else a.shared_account_id,
            "shared_account_id": a.shared_account_id,
            "action": a.action_type,
            "attribution_status": a.attribution_status,
            "delegation_token": a.delegation_token,
            "sensitivity": a.sensitivity,
        })
    return audit_records
