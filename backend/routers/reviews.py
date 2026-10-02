"""
routers/reviews.py — Human Review Queue and Fallback Review workflow endpoints.
"""

from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import HumanReview, PrivilegedAction, SharedAccount
from schemas import HumanReviewDecisionRequest
from services.evaluation_service import compute_metrics, save_evaluation_results

router = APIRouter(prefix="/reviews", tags=["Human Review"])


def _enrich_review(r: HumanReview, db: Session):
    acc = db.query(SharedAccount).filter(SharedAccount.shared_account_id == r.shared_account_id).first()
    action = db.query(PrivilegedAction).filter(PrivilegedAction.action_id == r.action_id).first()

    return {
        "review_id":           r.review_id,
        "action_id":           r.action_id,
        "action_type":         action.action_type if action else "N/A",
        "sensitivity":         action.sensitivity if action else "HIGH",
        "session_id":          r.session_id,
        "shared_account_id":   r.shared_account_id,
        "account_name":        acc.account_name if acc else r.shared_account_id,
        "claimed_user_id":     r.claimed_user_id,
        "conflicting_user_id": r.conflicting_user_id,
        "timestamp":           r.timestamp,
        "available_evidence":  r.available_evidence,
        "conflict_reason":     r.conflict_reason,
        "attribution_status":  r.attribution_status,
        "review_status":       r.review_status,
        "reviewer_id":         r.reviewer_id,
        "reviewer_decision":   r.reviewer_decision,
        "reviewer_reason":     r.reviewer_reason,
        "reviewed_at":         r.reviewed_at,
    }


@router.get("/")
@router.get("")
def list_review_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Lists cases in the Human Fallback Review queue."""
    query = db.query(HumanReview)
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(HumanReview.review_status == status_filter.upper())

    cases = query.order_by(HumanReview.timestamp.desc()).all()
    return [_enrich_review(r, db) for r in cases]


@router.get("/{review_id}")
def get_review_case(review_id: str, db: Session = Depends(get_db)):
    r = db.query(HumanReview).filter(HumanReview.review_id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Review case '{review_id}' not found.")
    return _enrich_review(r, db)


@router.post("/{review_id}/decide")
def submit_review_decision(
    review_id: str,
    req: HumanReviewDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Submits a forensic human reviewer's final ruling on an uncertain action:
    - CONFIRMED: Conclusively validates individual attribution based on external corroboration.
    - UNATTRIBUTED: Rules evidence inconclusive; refuses to blindly guess.
    """
    review = db.query(HumanReview).filter(HumanReview.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail=f"Review case '{review_id}' not found.")

    decision_norm = req.decision.strip().upper()
    if decision_norm not in ["CONFIRMED", "UNATTRIBUTED"]:
        raise HTTPException(
            status_code=400,
            detail="Decision must be either 'CONFIRMED' or 'UNATTRIBUTED'."
        )

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    review.reviewer_id       = req.reviewer_id or "AUDITOR001"
    review.reviewer_decision = decision_norm
    review.reviewer_reason   = req.reason
    review.reviewed_at       = now_iso
    review.review_status     = decision_norm

    # Update associated PrivilegedAction in audit log
    action = db.query(PrivilegedAction).filter(PrivilegedAction.action_id == review.action_id).first()
    if action:
        action.review_status = "RESOLVED"
        if decision_norm == "CONFIRMED":
            action.attributed_user_id     = review.claimed_user_id or "USER_CONFIRMED"
            action.attribution_status     = "ATTRIBUTED"
            action.attribution_confidence = "HUMAN_CONFIRMED (95.0%)"
            action.identity_evidence     += f" | Corroborated by {req.reviewer_id}: {req.reason}"
        else:
            action.attributed_user_id     = "UNATTRIBUTED"
            action.attribution_status     = "UNATTRIBUTED"
            action.attribution_confidence = "0.0%"
            action.identity_evidence     += f" | Inconclusive forensic determination by {req.reviewer_id}: {req.reason}"

    db.commit()
    db.refresh(review)

    # Recompute and persist updated evaluation metrics
    metrics = compute_metrics(db)
    save_evaluation_results(metrics)

    return {
        "status": "SUCCESS",
        "message": f"Review case '{review_id}' resolved as '{decision_norm}' by reviewer '{review.reviewer_id}'.",
        "review": _enrich_review(review, db)
    }
