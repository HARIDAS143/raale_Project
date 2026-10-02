"""
routers/shared_accounts.py — Shared account inventory endpoints with rich filters for Review 2.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import SharedAccount, PrivilegedAction, SystemLog, DelegationSession

router = APIRouter(prefix="/shared-accounts", tags=["Shared Accounts"])


@router.get("/")
@router.get("")
def list_shared_accounts(
    organisation: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    application: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(SharedAccount)

    if organisation:
        query = query.filter(SharedAccount.organisation_id == organisation.upper())
    if risk:
        query = query.filter(SharedAccount.risk_level == risk.upper())
    if status_filter:
        query = query.filter(SharedAccount.status == status_filter.upper())
    if application:
        query = query.filter(SharedAccount.application_name.ilike(f"%{application}%"))

    accounts = query.all()
    result = []
    for acc in accounts:
        baseline_count  = db.query(SystemLog).filter(
            SystemLog.shared_account_id == acc.shared_account_id
        ).count()
        prototype_count = db.query(PrivilegedAction).filter(
            PrivilegedAction.shared_account_id == acc.shared_account_id
        ).count()
        attributed_count = db.query(PrivilegedAction).filter(
            PrivilegedAction.shared_account_id == acc.shared_account_id,
            PrivilegedAction.attribution_status == "ATTRIBUTED",
        ).count()
        active_sessions = db.query(DelegationSession).filter(
            DelegationSession.shared_account_id == acc.shared_account_id,
            DelegationSession.status == "active"
        ).count()

        result.append({
            "shared_account_id":      acc.shared_account_id,
            "account_name":           acc.account_name,
            "application_id":         acc.application_id,
            "application_name":       acc.application_name,
            "application":            acc.application_name,
            "organisation_id":        acc.organisation_id,
            "organisation":           acc.organisation_id,
            "account_type":           acc.account_type,
            "risk_level":             acc.risk_level,
            "known_users_count":      acc.known_users_count,
            "requires_delegation":    acc.requires_delegation,
            "status":                 acc.status,
            "created_date":           acc.created_date,
            "baseline_log_count":     baseline_count,
            "prototype_action_count": prototype_count,
            "attributed_count":       attributed_count,
            "active_sessions_count":  active_sessions,
            "target_for_elimination": acc.requires_delegation == "YES" or acc.risk_level in ["HIGH", "CRITICAL"]
        })
    return result


@router.get("/{account_id}")
def get_shared_account(account_id: str, db: Session = Depends(get_db)):
    acc = db.query(SharedAccount).filter(
        SharedAccount.shared_account_id == account_id
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Shared account not found")
    return acc
