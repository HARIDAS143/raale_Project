"""
routers/sessions.py — Accountable delegation session lifecycle,
revocation, and multi-organisation validation endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models import DelegationSession, User, SharedAccount
from schemas import DelegationRequest, RevokeSessionRequest
from services.delegation_service import (
    create_delegation_session,
    revoke_delegation_session,
    check_session_status
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _enrich(s: DelegationSession, db: Session):
    user = db.query(User).filter(User.user_id == s.user_id).first() if s.user_id else None
    acc  = db.query(SharedAccount).filter(
        SharedAccount.shared_account_id == s.shared_account_id
    ).first()

    # Dynamic status evaluation (check if active session has passed end_time)
    is_valid, current_status = check_session_status(s, db)

    return {
        "session_id":        s.session_id,
        "user_id":           s.user_id or "UNATTRIBUTED",
        "user_name":         f"User {s.user_id}" if user else "Unattributed User",
        "user_type":         user.user_type if user else "N/A",
        "user_role":         user.role if user else "N/A",
        "user_permission":   user.permission_level if user else (s.granted_level or "N/A"),
        "organisation_id":   s.organisation_id or (user.organisation_id if user else (acc.organisation_id if acc else "N/A")),
        "shared_account_id": s.shared_account_id,
        "account_name":      acc.account_name if acc else "N/A",
        "application_name":  acc.application_name if acc else "N/A",
        "risk_level":        acc.risk_level if acc else "N/A",
        "delegation_token":  s.delegation_token,
        "start_time":        s.start_time,
        "end_time":          s.end_time,
        "status":            s.status,
        "is_active":         is_valid,
        "justification":     s.justification,
        "granted_level":     s.granted_level or (user.permission_level if user else "L1"),
    }


@router.get("/")
@router.get("")
def list_sessions(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(DelegationSession)
    if status_filter:
        query = query.filter(DelegationSession.status == status_filter.lower())
    sessions = query.order_by(DelegationSession.start_time.desc()).all()
    return [_enrich(s, db) for s in sessions]


@router.get("/active")
def list_active_sessions(db: Session = Depends(get_db)):
    all_active = db.query(DelegationSession).filter(DelegationSession.status == "active").order_by(DelegationSession.start_time.desc()).all()
    enriched = []
    for s in all_active:
        is_valid, _ = check_session_status(s, db)
        if is_valid:
            enriched.append(_enrich(s, db))
    return enriched


@router.post("/request", status_code=status.HTTP_201_CREATED)
@router.post("/request/", status_code=status.HTTP_201_CREATED)
def request_delegation(req: DelegationRequest, db: Session = Depends(get_db)):
    """
    Workflow Steps 1-5:
    1. Select individual synthetic identity
    2. Request access to specific shared account
    3. Validate permission & multi-organisation policy
    4. Issue cryptographic delegation token and session
    5. Return session bound to user
    """
    user = db.query(User).filter(User.user_id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User identity '{req.user_id}' not found.")

    account = db.query(SharedAccount).filter(SharedAccount.shared_account_id == req.shared_account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail=f"Shared account '{req.shared_account_id}' not found.")

    success, session, reason, details = create_delegation_session(
        db=db,
        user=user,
        account=account,
        duration_minutes=req.duration_minutes or 30,
        justification=req.justification or "Standard accountable delegation request"
    )

    if not success:
        return {
            "status": "PERMISSION_DENIED",
            "permission_granted": False,
            "user_id": user.user_id,
            "user_permission": user.permission_level,
            "shared_account_id": account.shared_account_id,
            "account_risk_level": account.risk_level,
            "message": reason,
            "policy_details": details
        }

    return {
        "status": "SUCCESS",
        "permission_granted": True,
        "user_id": user.user_id,
        "user_permission": user.permission_level,
        "shared_account_id": account.shared_account_id,
        "account_risk_level": account.risk_level,
        "session": _enrich(session, db),
        "message": reason
    }


@router.post("/{session_id}/revoke")
def revoke_session(
    session_id: str,
    req: RevokeSessionRequest = RevokeSessionRequest(),
    db: Session = Depends(get_db)
):
    """
    Revokes an active delegation session.
    After revocation, any sensitive action using this session will be BLOCKED.
    """
    success, session, msg = revoke_delegation_session(
        db=db,
        session_id=session_id,
        reason=req.reason or "Security revocation",
        revoked_by=req.revoked_by or "SECURITY_ADMIN"
    )
    if not success:
        raise HTTPException(status_code=404, detail=msg)

    return {
        "status": "SUCCESS",
        "message": msg,
        "session": _enrich(session, db)
    }


@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = db.query(DelegationSession).filter(DelegationSession.session_id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return _enrich(s, db)
