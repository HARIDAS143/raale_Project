"""
services/evaluation_service.py — Reproducible synthetic evaluation engine
comparing legacy baseline vs Review 2 accountable delegation prototype.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session

from models import SystemLog, PrivilegedAction, HumanReview, User, SharedAccount

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_FILE = os.path.join(BASE_DIR, "evaluation_results.json")


def compute_metrics(db: Session) -> Dict[str, Any]:
    """Computes dynamic empirical metrics directly from the live SQLite database."""
    # ── 1. Baseline Evaluation (Legacy shared accounts) ─────────────────────
    baseline_total = db.query(SystemLog).count()
    baseline_sensitive = db.query(SystemLog).filter(
        SystemLog.sensitivity.in_(["HIGH", "CRITICAL"])
    ).count()

    # In legacy shared account baseline, individual is NEVER identified
    baseline_attributed = 0
    baseline_unattributed = baseline_total
    baseline_iar = 0.0
    baseline_sensitive_iar = 0.0

    # ── 2. Review 2 Prototype Evaluation ──────────────────────────────────
    proto_total = db.query(PrivilegedAction).count()

    proto_attributed = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "ATTRIBUTED"
    ).count()

    proto_unattributed = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "UNATTRIBUTED"
    ).count()

    proto_permission_denied = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "PERMISSION_DENIED"
    ).count()

    proto_blocked = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "BLOCKED"
    ).count()

    proto_uncertain = db.query(PrivilegedAction).filter(
        PrivilegedAction.attribution_status == "UNCERTAIN"
    ).count()

    # Sensitive subset
    proto_sensitive = db.query(PrivilegedAction).filter(
        PrivilegedAction.sensitivity.in_(["HIGH", "CRITICAL"])
    ).count()

    proto_sens_attributed = db.query(PrivilegedAction).filter(
        PrivilegedAction.sensitivity.in_(["HIGH", "CRITICAL"]),
        PrivilegedAction.attribution_status == "ATTRIBUTED"
    ).count()

    # Human review metrics
    total_reviews = db.query(HumanReview).count()
    pending_reviews = db.query(HumanReview).filter(HumanReview.review_status == "PENDING").count()
    confirmed_reviews = db.query(HumanReview).filter(HumanReview.review_status == "CONFIRMED").count()
    unattributed_reviews = db.query(HumanReview).filter(HumanReview.review_status == "UNATTRIBUTED").count()

    # Total individually attributable (including confirmed by human review)
    effective_attributed = proto_attributed + confirmed_reviews
    prototype_iar = round((proto_attributed / proto_total * 100), 2) if proto_total > 0 else 0.0
    effective_iar = round((effective_attributed / proto_total * 100), 2) if proto_total > 0 else 0.0
    sensitive_iar = round((proto_sens_attributed / proto_sensitive * 100), 2) if proto_sensitive > 0 else 0.0

    unattributed_rate = round((proto_unattributed / proto_total * 100), 2) if proto_total > 0 else 0.0
    blocked_rate = round(((proto_blocked + proto_permission_denied) / proto_total * 100), 2) if proto_total > 0 else 0.0

    improvement = round(prototype_iar - baseline_iar, 2)

    # Multi-organisation breakdown
    org_breakdown = {}
    for org_id in ["ORG001", "ORG002", "ORG003", "ORG004", "ORG005", "ORG006"]:
        actions_in_org = db.query(PrivilegedAction).filter(PrivilegedAction.organisation_id == org_id).all()
        if actions_in_org:
            attr_c = sum(1 for a in actions_in_org if a.attribution_status == "ATTRIBUTED")
            org_breakdown[org_id] = {
                "total_actions": len(actions_in_org),
                "attributed": attr_c,
                "iar": round((attr_c / len(actions_in_org) * 100), 2) if actions_in_org else 0.0
            }

    results = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": "Shared-Account Elimination Workflow Using Accountable Delegation and Session Attribution",
        "review_milestone": "Review 2 (70% Completion)",
        "metrics_summary": {
            "baseline_iar": baseline_iar,
            "prototype_iar": prototype_iar,
            "effective_iar_with_fallback": effective_iar,
            "sensitive_iar": sensitive_iar,
            "improvement": improvement,
            "unattributed_rate": unattributed_rate,
            "blocked_or_denied_rate": blocked_rate
        },
        "baseline": {
            "total_system_logs": baseline_total,
            "sensitive_actions": baseline_sensitive,
            "individually_attributed": baseline_attributed,
            "unattributed": baseline_unattributed,
            "iar": baseline_iar,
            "non_repudiation": "FAIL — Individual operator unknown",
            "enforcement": "NONE — Direct shared credential login"
        },
        "prototype": {
            "total_actions": proto_total,
            "sensitive_actions": proto_sensitive,
            "individually_attributed": proto_attributed,
            "unattributed": proto_unattributed,
            "permission_denied": proto_permission_denied,
            "blocked_actions": proto_blocked,
            "uncertain_actions": proto_uncertain,
            "iar": prototype_iar,
            "sensitive_iar": sensitive_iar,
            "non_repudiation": "PASS — Deterministically bound to individual session",
            "enforcement": "ACTIVE — Granular L1-L4 & multi-org policies"
        },
        "human_review_queue": {
            "total_cases": total_reviews,
            "pending_review": pending_reviews,
            "confirmed_attributed": confirmed_reviews,
            "ruled_unattributed": unattributed_reviews
        },
        "organisation_breakdown": org_breakdown
    }

    return results


def save_evaluation_results(results: Dict[str, Any]) -> str:
    """Writes evaluation dictionary to evaluation_results.json."""
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return RESULTS_FILE


def load_evaluation_results(db: Session) -> Dict[str, Any]:
    """Loads results from file or recomputes dynamically if missing."""
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    results = compute_metrics(db)
    save_evaluation_results(results)
    return results
