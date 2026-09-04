"""
routers/sessions.py — Delegation session management endpoints for Phase 4 prototype.
"""

import random
import string
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import DelegationSession, User, SharedAccount
from schemas import DelegationRequest

router = APIRouter(prefix="/sessions", tags=["Sessions"])

LEVEL_MAP = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}
RISK_MAP = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _enrich(s: DelegationSession, db: Session):
    user = db.query(User).filter(User.user_id == s.user_id).first() if s.user_id else None
    acc  = db.query(SharedAccount).filter(
        SharedAccount.shared_account_id == s.shared_account_id
    ).first()
    return {
        "session_id":           s.session_id,
        "user_id":              s.user_id,
        "user_name":            f"User {s.user_id}" if user else "Unattributed User",
        "user_type":            user.user_type if user else "N/A",
        "user_role":            user.role if user else "N/A",
        "user_permission":      user.permission_level if user else "N/A",
        "shared_account_id":    s.shared_account_id,
        "account_name":         acc.account_name if acc else "N/A",
        "application_name":     acc.application_name if acc else (acc.account_name if acc else "N/A"),
        "risk_level":           acc.risk_level if acc else "N/A",
        "delegation_token":     s.delegation_token,
        "start_time":           s.start_time,
        "end_time":             s.end_time,
        "status":               s.status,
        "justification":        s.justification,
    }


@router.get("/")
@router.get("")
def list_sessions(db: Session = Depends(get_db)):
    return [_enrich(s, db) for s in db.query(DelegationSession).order_by(DelegationSession.start_time.desc()).all()]


@router.get("/active")
def list_active_sessions(db: Session = Depends(get_db)):
    return [_enrich(s, db) for s in
            db.query(DelegationSession).filter(DelegationSession.status == "active").order_by(DelegationSession.start_time.desc()).all()]


@router.post("/request", status_code=status.HTTP_201_CREATED)
@router.post("/request/", status_code=status.HTTP_201_CREATED)
def request_delegation(req: DelegationRequest, db: Session = Depends(get_db)):
    """
    Workflow Steps 1-5:
    1. User selects synthetic identity
    2. User requests access to shared account
    3. System checks permission level
    4. System creates session
    5. Session is associated with individual user
    """
    user = db.query(User).filter(User.user_id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

    account = db.query(SharedAccount).filter(SharedAccount.shared_account_id == req.shared_account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail=f"Shared account {req.shared_account_id} not found")

    user_perm_val = LEVEL_MAP.get(user.permission_level, 1)
    acc_risk_val = RISK_MAP.get(account.risk_level, 1)

    permission_granted = user_perm_val >= acc_risk_val

    if not permission_granted:
        return {
            "status": "PERMISSION_DENIED",
            "permission_granted": False,
            "user_id": user.user_id,
            "user_permission": user.permission_level,
            "shared_account_id": account.shared_account_id,
            "account_risk_level": account.risk_level,
            "message": f"Permission level '{user.permission_level}' is insufficient for shared account risk level '{account.risk_level}'."
        }

    # Generate session ID and delegation token
    rand_id = "".join(random.choices(string.digits, k=4))
    session_id = f"SES-{rand_id}"
    token_rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    delegation_token = f"DEL-{token_rand}"

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_session = DelegationSession(
        session_id=session_id,
        user_id=user.user_id,
        shared_account_id=account.shared_account_id,
        delegation_token=delegation_token,
        start_time=now_iso,
        status="active",
        justification=req.justification or "Standard accountable delegation request"
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "status": "SUCCESS",
        "permission_granted": True,
        "user_id": user.user_id,
        "user_permission": user.permission_level,
        "shared_account_id": account.shared_account_id,
        "account_risk_level": account.risk_level,
        "session": _enrich(new_session, db)
    }


@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = db.query(DelegationSession).filter(
        DelegationSession.session_id == session_id
    ).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return _enrich(s, db)
