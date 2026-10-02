"""
routers/users.py — Synthetic user management endpoints with multi-organisation filtering.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User

router = APIRouter(prefix="/users", tags=["Users"])


def _serialize(u: User):
    return {
        "user_id":          u.user_id,
        "organisation_id":  u.organisation_id,
        "organisation":     u.organisation_id,
        "user_type":        u.user_type,
        "role":             u.role,
        "permission_level": u.permission_level,
        "clearance_level":  u.clearance_level,
        "account_type":     u.account_type,
        "mfa_enrolled":     u.mfa_enrolled,
        "active_status":    u.active_status,
        "status":           u.active_status,
        "created_date":     u.created_date,
    }


@router.get("/")
@router.get("")
def list_users(
    organisation: Optional[str] = Query(None),
    permission: Optional[str] = Query(None),
    user_type: Optional[str] = Query(None),
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(User)

    if organisation:
        query = query.filter(User.organisation_id == organisation.upper())
    if permission:
        query = query.filter(User.permission_level == permission.upper())
    if user_type:
        query = query.filter(User.user_type == user_type.lower())
    if active_only:
        query = query.filter(User.active_status == "ACTIVE")

    return [_serialize(u) for u in query.all()]


@router.get("/active")
def list_active_users(db: Session = Depends(get_db)):
    return [_serialize(u) for u in db.query(User).filter(User.active_status == "ACTIVE").all()]


@router.get("/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.user_id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return _serialize(u)
