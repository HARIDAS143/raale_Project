"""
routers/dashboard.py — Aggregated Review 2 statistics and dynamic chart data.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, SharedAccount, SystemLog, DelegationSession, PrivilegedAction, HumanReview
from services.evaluation_service import compute_metrics

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    metrics = compute_metrics(db)

    total_users           = db.query(User).count()
    active_users          = db.query(User).filter(User.active_status == "ACTIVE").count()
    total_shared_accounts = db.query(SharedAccount).count()
    active_sessions       = db.query(DelegationSession).filter(DelegationSession.status == "active").count()

    proto_metrics = metrics["prototype"]
    baseline_metrics = metrics["baseline"]
    summary = metrics["metrics_summary"]
    reviews = metrics["human_review_queue"]

    # Attribution status breakdown
    status_counts = {}
    for st in ["ATTRIBUTED", "UNATTRIBUTED", "PERMISSION_DENIED", "BLOCKED", "UNCERTAIN"]:
        status_counts[st] = db.query(PrivilegedAction).filter(PrivilegedAction.attribution_status == st).count()

    # Severity / Sensitivity breakdown
    severity_breakdown = {
        sev: db.query(PrivilegedAction).filter(PrivilegedAction.sensitivity == sev).count()
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    }

    # Actions per organisation
    org_actions = {}
    for a in db.query(PrivilegedAction).all():
        org_actions[a.organisation_id] = org_actions.get(a.organisation_id, 0) + 1

    # Actions per shared account
    account_action_data = []
    for acc in db.query(SharedAccount).all():
        count = db.query(PrivilegedAction).filter(
            PrivilegedAction.shared_account_id == acc.shared_account_id
        ).count()
        attributed = db.query(PrivilegedAction).filter(
            PrivilegedAction.shared_account_id == acc.shared_account_id,
            PrivilegedAction.attribution_status == "ATTRIBUTED"
        ).count()
        account_action_data.append({
            "account_id":   acc.shared_account_id,
            "account_name": acc.account_name,
            "application":  acc.application_name,
            "organisation": acc.organisation_id,
            "risk_level":   acc.risk_level,
            "action_count": count,
            "attributed_count": attributed,
            "requires_delegation": acc.requires_delegation,
        })

    # Human review resolution stats
    human_review_stats = {
        "total": reviews["total_cases"],
        "pending": reviews["pending_review"],
        "confirmed": reviews["confirmed_attributed"],
        "unattributed": reviews["ruled_unattributed"],
    }

    return {
        # 8 Review 2 KPI Cards
        "total_shared_accounts":   total_shared_accounts,
        "active_sessions":         active_sessions,
        "total_privileged_actions": proto_metrics["total_actions"],
        "prototype_attributed":    proto_metrics["individually_attributed"],
        "prototype_unattributed":  proto_metrics["unattributed"],
        "blocked_actions":         proto_metrics["blocked_actions"] + proto_metrics["permission_denied"],
        "human_review_cases":      reviews["total_cases"],
        "prototype_iar":           summary["prototype_iar"],

        # Additional core metrics
        "total_users":             total_users,
        "active_users":            active_users,
        "baseline_iar":            summary["baseline_iar"],
        "sensitive_iar":           summary["sensitive_iar"],
        "improvement":             summary["improvement"],
        "baseline_total_logs":     baseline_metrics["total_system_logs"],
        "baseline_sensitive":      baseline_metrics["sensitive_actions"],
        "prototype_total":         proto_metrics["total_actions"],
        "prototype_denied":        proto_metrics["permission_denied"],
        "prototype_uncertain":     proto_metrics["uncertain_actions"],

        # Dynamic charts data
        "status_counts":           status_counts,
        "severity_breakdown":      severity_breakdown,
        "org_actions":             org_actions,
        "account_action_data":     account_action_data,
        "human_review_stats":      human_review_stats,
    }
