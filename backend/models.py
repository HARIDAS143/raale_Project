"""
models.py — Phase 2 updated ORM models matching the generated CSV schema.
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# ---------------------------------------------------------------------------
# User  (20 records)
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    user_id          = Column(String, primary_key=True, index=True)
    organisation_id  = Column(String, nullable=False)
    user_type        = Column(String, nullable=False)
    role             = Column(String, nullable=False)
    permission_level = Column(String, nullable=False)
    clearance_level  = Column(String, nullable=False)
    account_type     = Column(String, nullable=False)
    mfa_enrolled     = Column(String, nullable=False)
    active_status    = Column(String, nullable=False)
    created_date     = Column(String, nullable=False)

    sessions           = relationship("DelegationSession", back_populates="user")
    privileged_actions = relationship("PrivilegedAction",  back_populates="user",
                                      foreign_keys="PrivilegedAction.user_id")


# ---------------------------------------------------------------------------
# Shared Account  (8 records)
# ---------------------------------------------------------------------------
class SharedAccount(Base):
    __tablename__ = "shared_accounts"

    shared_account_id   = Column(String, primary_key=True, index=True)
    account_name        = Column(String, nullable=False)
    application_id      = Column(String, nullable=False)
    application_name    = Column(String, nullable=False)
    organisation_id     = Column(String, nullable=False)
    account_type        = Column(String, nullable=False)
    risk_level          = Column(String, nullable=False)
    known_users_count   = Column(Integer, nullable=False)
    requires_delegation = Column(String, nullable=False)
    status              = Column(String, nullable=False)
    created_date        = Column(String, nullable=False)

    system_logs        = relationship("SystemLog",         back_populates="shared_account")
    sessions           = relationship("DelegationSession", back_populates="shared_account")
    privileged_actions = relationship("PrivilegedAction",  back_populates="shared_account")


# ---------------------------------------------------------------------------
# System Log  (BASELINE — individual_identified always NO)
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
# Delegation Session
# ---------------------------------------------------------------------------
class DelegationSession(Base):
    __tablename__ = "delegation_sessions"

    session_id        = Column(String, primary_key=True, index=True)
    user_id           = Column(String, ForeignKey("users.user_id"), nullable=True)
    shared_account_id = Column(String, ForeignKey("shared_accounts.shared_account_id"), nullable=False)
    delegation_token  = Column(String, nullable=False, unique=True)
    start_time        = Column(String, nullable=False)
    end_time          = Column(String, nullable=True)
    status            = Column(String, nullable=False, default="active")
    justification     = Column(Text, nullable=True)

    user               = relationship("User",          back_populates="sessions")
    shared_account     = relationship("SharedAccount", back_populates="sessions")
    privileged_actions = relationship("PrivilegedAction", back_populates="session")


# ---------------------------------------------------------------------------
# Privileged Action  (PROTOTYPE — with full attribution)
# ---------------------------------------------------------------------------
class PrivilegedAction(Base):
    __tablename__ = "privileged_actions"

    action_id              = Column(String, primary_key=True, index=True)
    timestamp              = Column(String, nullable=False)
    session_id             = Column(String, ForeignKey("delegation_sessions.session_id"), nullable=False)
    shared_account_id      = Column(String, ForeignKey("shared_accounts.shared_account_id"), nullable=False)
    organisation_id        = Column(String, nullable=False)
    application            = Column(String, nullable=False)
    action_type            = Column(String, nullable=False)
    sensitivity            = Column(String, nullable=False)
    required_permission    = Column(String, nullable=False)
    user_permission        = Column(String, nullable=False)
    delegation_token       = Column(String, nullable=False)
    attributed_user_id     = Column(String, nullable=False)   # USER001 | NONE | UNKNOWN
    attribution_status     = Column(String, nullable=False)   # ATTRIBUTED | UNATTRIBUTED | PERMISSION_DENIED
    attribution_confidence = Column(String, nullable=False)
    identity_evidence      = Column(String, nullable=False)
    justification          = Column(Text, nullable=True)
    scenario_tag           = Column(String, nullable=True)

    # user_id FK: nullable because attributed_user_id may be NONE/UNKNOWN
    user_id        = Column(String, ForeignKey("users.user_id"), nullable=True)

    session        = relationship("DelegationSession", back_populates="privileged_actions")
    shared_account = relationship("SharedAccount",     back_populates="privileged_actions")
    user           = relationship("User", back_populates="privileged_actions",
                                  foreign_keys=[user_id])
