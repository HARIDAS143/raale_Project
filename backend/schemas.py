"""
schemas.py — Pydantic models for request bodies in Phase 4 prototype.
"""

from pydantic import BaseModel
from typing import Optional


class DelegationRequest(BaseModel):
    user_id: str
    shared_account_id: str
    justification: Optional[str] = "Standard delegation request for privileged access"


class PerformActionRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    shared_account_id: Optional[str] = None
    action: str  # e.g., View sensitive record, Modify configuration, Approve transaction, Export report
    sensitivity: Optional[str] = "HIGH"
    justification: Optional[str] = "Routine privileged action execution"
