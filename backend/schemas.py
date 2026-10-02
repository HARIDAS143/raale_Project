"""
schemas.py — Pydantic models for Review 2 APIs.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class DelegationRequest(BaseModel):
    user_id: str
    shared_account_id: str
    duration_minutes: Optional[int] = Field(default=30, ge=1, le=480)
    justification: Optional[str] = "Standard accountable delegation request for privileged access"


class RevokeSessionRequest(BaseModel):
    reason: Optional[str] = "Administrative revocation of delegation session"
    revoked_by: Optional[str] = "SECURITY_ADMIN"


class PerformActionRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    shared_account_id: Optional[str] = None
    action: str  # e.g., View sensitive record, Modify configuration, Approve transaction, Export report, Change access configuration
    sensitivity: Optional[str] = "HIGH"
    required_permission: Optional[str] = None
    justification: Optional[str] = "Routine privileged action execution"
    # Testing / Simulation flags for edge cases
    force_scenario: Optional[str] = None  # None | missing_delegation | insufficient_permission | expired_session | invalid_session | conflicting_evidence | external_partner
    conflicting_user_id: Optional[str] = None  # Simulates conflicting identity evidence in logs


class HumanReviewDecisionRequest(BaseModel):
    reviewer_id: str = "AUDITOR001"
    decision: str  # CONFIRMED | UNATTRIBUTED
    reason: str


class EvaluationRunRequest(BaseModel):
    include_baseline: Optional[bool] = True
    iterations: Optional[int] = 1
