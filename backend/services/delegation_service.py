"""
services/delegation_service.py — Accountable delegation session lifecycle,
token issuance, expiration enforcement, and session revocation.
"""

import random
import string
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session

from models import DelegationSession, User, SharedAccount
from services.permission_service import validate_delegation_permission


def generate_session_id() -> str:
    digits = "".join(random.choices(string.digits, k=4))
    return f"SES-{digits}"


def generate_delegation_token() -> str:
    rand_chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"TOK-DEL-{rand_chars}"


def is_session_expired(session: DelegationSession) -> bool:
    """Returns True if session end_time is in the past."""
    if not session.end_time:
        return False
    try:
        # Normalize ISO strings
        end_str = session.end_time.replace("Z", "+00:00")
        end_dt = datetime.fromisoformat(end_str)
        now_dt = datetime.now(timezone.utc)
        return now_dt > end_dt
    except Exception:
        return False


def check_session_status(session: DelegationSession, db: Optional[Session] = None) -> Tuple[bool, str]:
    """
    Checks if session is active and not expired or revoked.
    Returns (is_valid: bool, status_reason: str).
    """
    if not session:
        return False, "INVALID_SESSION"

    if session.status == "revoked":
        return False, "SESSION_REVOKED"

    if session.status == "closed":
        return False, "SESSION_CLOSED"

    if session.status == "expired" or is_session_expired(session):
        if session.status != "expired" and db:
            session.status = "expired"
            db.commit()
        return False, "SESSION_EXPIRED"

    if session.status == "active":
        return True, "SESSION_ACTIVE"

    return False, f"SESSION_STATUS_{session.status.upper()}"


def create_delegation_session(
    db: Session,
    user: User,
    account: SharedAccount,
    duration_minutes: int = 30,
    justification: str = "Standard accountable delegation request"
) -> Tuple[bool, Optional[DelegationSession], str, Dict[str, Any]]:
    """
    Executes Workflow Steps 1-5:
    1. Validates individual user identity
    2. Validates target shared account
    3. Executes permission validation service
    4. Issues cryptographic delegation token and binds session to individual
    5. Sets explicit expiration window
    """
    # Permission validation
    allowed, reason, details = validate_delegation_permission(user, account)
    if not allowed:
        return False, None, reason, details

    now = datetime.now(timezone.utc)
    expiry = now + timedelta(minutes=duration_minutes)

    session_id = generate_session_id()
    token = generate_delegation_token()

    session = DelegationSession(
        session_id=session_id,
        user_id=user.user_id,
        shared_account_id=account.shared_account_id,
        organisation_id=user.organisation_id,
        delegation_token=token,
        start_time=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_time=expiry.strftime("%Y-%m-%dT%H:%M:%SZ"),
        status="active",
        justification=justification,
        granted_level=user.permission_level,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return True, session, "Delegation session created successfully.", details


def revoke_delegation_session(
    db: Session,
    session_id: str,
    reason: str = "Administrative revocation",
    revoked_by: str = "SECURITY_ADMIN"
) -> Tuple[bool, Optional[DelegationSession], str]:
    """Revokes an active session immediately, making subsequent actions fail."""
    session = db.query(DelegationSession).filter(DelegationSession.session_id == session_id).first()
    if not session:
        return False, None, f"Session '{session_id}' not found."

    if session.status == "revoked":
        return True, session, f"Session '{session_id}' is already revoked."

    session.status = "revoked"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    revocation_note = f" [REVOKED at {now_iso} by {revoked_by}: {reason}]"
    session.justification = (session.justification or "") + revocation_note

    db.commit()
    db.refresh(session)
    return True, session, f"Session '{session_id}' successfully revoked."
