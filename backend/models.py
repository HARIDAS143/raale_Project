"""
models.py — Review 2 updated ORM models for Accountable Delegation,
Session Attribution, Explanation Layer, and Human Fallback Review.
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# ---------------------------------------------------------------------------
# User  (Synthetic identities across organisations)
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    user_id          = Column(String, primary_key=True, index=True)
    organisation_id  = Column(String, nullable=False, index=True)
    user_type        = Column(String, nullable=False)   # government_employee | security_administrator | auditor | external_partner
    role             = Column(String, nullable=False)
    permission_level = Column(String, nullable=False)   # L1 | L2 | L3 | L4
    clearance_level  = Column(String, nullable=False)   # L1 | L2 | L3 | L4
    account_type     = Column(String, nullable=False)   # internal | external
    mfa_enrolled     = Column(String, nullable=False)   # YES | NO
    active_status    = Column(String, nullable=False)   # ACTIVE | INACTIVE
    created_date     = Column(String, nullable=False)

    sessions           = relationship("DelegationSession", back_populates="user")
    privileged_actions = relationship("PrivilegedAction",  back_populates="user",
                                      foreign_keys="PrivilegedAction.user_id")


# ---------------------------------------------------------------------------
# Shared Account  (Legacy shared credentials catalog)
# ---------------------------------------------------------------------------
class SharedAccount(Base):
    __tablename__ = "shared_accounts"

    shared_account_id   = Column(String, primary_key=True, index=True)
    account_name        = Column(String, nullable=False)
    application_id      = Column(String, nullable=False)
    application_name    = Column(String, nullable=False)
    organisation_id     = Column(String, nullable=False, index=True)
    account_type        = Column(String, nullable=False)
    risk_level          = Column(String, nullable=False)   # LOW | MEDIUM | HIGH | CRITICAL
    known_users_count   = Column(Integer, nullable=False)
    requires_delegation = Column(String, nullable=False)   # YES | NO
    status              = Column(String, nullable=False)   # ACTIVE | DEPRECATED | TARGET_ELIMINATION
    created_date        = Column(String, nullable=False)

    system_logs        = relationship("SystemLog",         back_populates="shared_account")
    sessions           = relationship("DelegationSession", back_populates="shared_account")
    privileged_actions = relationship("PrivilegedAction",  back_populates="shared_account")


# ---------------------------------------------------------------------------
# System Log  (BASELINE — legacy un-attributed logs)
# ---------------------------------------------------------------------------
class SystemLog(Base):
    __tablename__ = "system_logs"

    log_id                = Column(String, primary_key=True, index=True)
    timestamp             = Column(String, nullable=False)
    session_id            = Column(String, nullable=False)
    shared_account_id     = Column(String, ForeignKey("shared_accounts.shared_account_id"), nullable=False)
    application           = Column(String, nullable=False)
    action                = Column(String, nullable=False)
    organisation_id       = Column(String, nullable=False)
    device_id             = Column(String, nullable=False)
    identity_evidence     = Column(String, nullable=False)
    log_status            = Column(String, nullable=False)
    individual_identified = Column(String, nullable=False, default="NO")
    sensitivity           = Column(String, nullable=False)

    shared_account = relationship("SharedAccount", back_populates="system_logs")


# ---------------------------------------------------------------------------
# Delegation Session  (Accountable delegation sessions with expiry & revocation)
# ---------------------------------------------------------------------------
class DelegationSession(Base):
    __tablename__ = "delegation_sessions"

    session_id        = Column(String, primary_key=True, index=True)
    user_id           = Column(String, ForeignKey("users.user_id"), nullable=True)
    shared_account_id = Column(String, ForeignKey("shared_accounts.shared_account_id"), nullable=False)
    organisation_id   = Column(String, nullable=True)
    delegation_token  = Column(String, nullable=False, unique=True, index=True)
    start_time        = Column(String, nullable=False)
    end_time          = Column(String, nullable=True)   # ISO timestamp when session expires
    status            = Column(String, nullable=False, default="active") # active | expired | revoked | closed
    justification     = Column(Text, nullable=True)
    granted_level     = Column(String, nullable=True)   # L1 | L2 | L3 | L4

    user               = relationship("User",          back_populates="sessions")
    shared_account     = relationship("SharedAccount", back_populates="sessions")
    privileged_actions = relationship("PrivilegedAction", back_populates="session")


# ---------------------------------------------------------------------------
# Privileged Action  (Actions executed with attribution, explanation, audit)
# ---------------------------------------------------------------------------
class PrivilegedAction(Base):
    __tablename__ = "privileged_actions"

    action_id              = Column(String, primary_key=True, index=True)
    timestamp              = Column(String, nullable=False)
    session_id             = Column(String, ForeignKey("delegation_sessions.session_id"), nullable=True)
    shared_account_id      = Column(String, ForeignKey("shared_accounts.shared_account_id"), nullable=False)
    organisation_id        = Column(String, nullable=False, index=True)
    application            = Column(String, nullable=False)
    action_type            = Column(String, nullable=False)
    sensitivity            = Column(String, nullable=False)   # LOW | MEDIUM | HIGH | CRITICAL
    required_permission    = Column(String, nullable=False)   # L1 | L2 | L3 | L4
    user_permission        = Column(String, nullable=False)   # L1 | L2 | L3 | L4 | NONE
    delegation_token       = Column(String, nullable=False)
    attributed_user_id     = Column(String, nullable=False)   # USERxxx | NONE | UNKNOWN | UNATTRIBUTED
    attribution_status     = Column(String, nullable=False)   # ATTRIBUTED | UNATTRIBUTED | PERMISSION_DENIED | BLOCKED | UNCERTAIN
    attribution_confidence = Column(String, nullable=False)   # HIGH (100%) | MEDIUM | LOW | 0.0% | CONFLICT
    identity_evidence      = Column(String, nullable=False)
    justification          = Column(Text, nullable=True)
    scenario_tag           = Column(String, nullable=True)    # normal | missing_delegation | insufficient_permission | expired_session | invalid_session | conflicting_evidence | external_partner
    explanation            = Column(Text, nullable=True)      # Structured JSON/text from Explanation Layer
    review_status          = Column(String, nullable=False, default="NOT_REQUIRED") # NOT_REQUIRED | PENDING | RESOLVED

    user_id        = Column(String, ForeignKey("users.user_id"), nullable=True)

    session        = relationship("DelegationSession", back_populates="privileged_actions")
    shared_account = relationship("SharedAccount",     back_populates="privileged_actions")
    user           = relationship("User", back_populates="privileged_actions",
                                  foreign_keys=[user_id])
    human_reviews  = relationship("HumanReview", back_populates="action")


# ---------------------------------------------------------------------------
# Human Review Queue  (Review 2 Fallback Workflow for Uncertain / Conflicting Cases)
# ---------------------------------------------------------------------------
class HumanReview(Base):
    __tablename__ = "human_reviews"

    review_id           = Column(String, primary_key=True, index=True)
    action_id           = Column(String, ForeignKey("privileged_actions.action_id"), nullable=False)
    session_id          = Column(String, nullable=False)
    shared_account_id   = Column(String, nullable=False)
    claimed_user_id     = Column(String, nullable=True)
    conflicting_user_id = Column(String, nullable=True)
    timestamp           = Column(String, nullable=False)
    available_evidence  = Column(Text, nullable=False)
    conflict_reason     = Column(Text, nullable=False)
    attribution_status  = Column(String, nullable=False, default="UNCERTAIN")
    review_status       = Column(String, nullable=False, default="PENDING")   # PENDING | CONFIRMED | UNATTRIBUTED
    reviewer_id         = Column(String, nullable=True)                      # e.g., AUDITOR001
    reviewer_decision   = Column(String, nullable=True)                      # CONFIRMED | UNATTRIBUTED
    reviewer_reason     = Column(Text, nullable=True)
    reviewed_at         = Column(String, nullable=True)

    action = relationship("PrivilegedAction", back_populates="human_reviews")
