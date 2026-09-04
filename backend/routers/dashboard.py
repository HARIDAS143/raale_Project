"""
routers/dashboard.py — Phase 2 aggregated statistics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, SharedAccount, SystemLog, DelegationSession, PrivilegedAction

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_users           = db.query(User).count()
    active_users          = db.query(User).filter(User.active_status == "ACTIVE").count()
    total_shared_accounts = db.query(SharedAccount).count()
    active_sessions       = db.query(DelegationSession).filter(DelegationSession.status == "active").count()
    total_priv_actions    = db.query(PrivilegedAction).count()

    # IAR — baseline
    total_baseline        = db.query(SystemLog).count()
    baseline_sensitive    = db.query(SystemLog).filter(
        SystemLog.sensitivity.in_(["HIGH","CRITICAL"])
    ).count()

    # IAR — prototype
    proto_total      = db.query(PrivilegedAction).count()
    proto_attributed = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "ATTRIBUTED"
    ).count()
    proto_unattr     = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "UNATTRIBUTED"
    ).count()
    proto_denied     = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "PERMISSION_DENIED"
    ).count()

    baseline_iar  = 0.0
    prototype_iar = round(proto_attributed / proto_total * 100, 2) if proto_total else 0.0

    # Severity breakdown
    severity_breakdown = {
        sev: db.query(PrivilegedAction).filter(PrivilegedAction.sensitivity == sev).count()
        for sev in ["CRITICAL","HIGH","MEDIUM","LOW"]
    }

    # Actions per shared account
    account_action_data = []
    for acc in db.query(SharedAccount).all():
        count = db.query(PrivilegedAction).filter(
            PrivilegedAction.shared_account_id == acc.shared_account_id
        ).count()
        account_action_data.append({
            "account_name": acc.account_name,
            "application":  acc.application_name,
            "risk_level":   acc.risk_level,
            "action_count": count,
        })

    # Scenario breakdown
    scenario_data = {}
    for pa in db.query(PrivilegedAction).all():
        tag = pa.scenario_tag or "normal"
        scenario_data[tag] = scenario_data.get(tag, 0) + 1

    # User type breakdown
    user_type_data = {}
    for u in db.query(User).all():
        user_type_data[u.user_type] = user_type_data.get(u.user_type, 0) + 1

    return {
        "total_users":           total_users,
        "active_users":          active_users,
        "total_shared_accounts": total_shared_accounts,
        "active_sessions":       active_sessions,
        "total_privileged_actions": total_priv_actions,
        "baseline_iar":          baseline_iar,
        "prototype_iar":         prototype_iar,
        "baseline_total_logs":   total_baseline,
        "baseline_sensitive":    baseline_sensitive,
        "prototype_total":       proto_total,
        "prototype_attributed":  proto_attributed,
        "prototype_unattributed":proto_unattr,
        "prototype_denied":      proto_denied,
        "severity_breakdown":    severity_breakdown,
        "account_action_data":   account_action_data,
        "scenario_data":         scenario_data,
        "user_type_data":        user_type_data,
    }
