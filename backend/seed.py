"""
seed.py — Phase 2: Seeds the SQLite database from the generated CSV files.
"""

import csv
import os
from database import engine, SessionLocal, Base
from models import User, SharedAccount, SystemLog, DelegationSession, PrivilegedAction

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

VALID_USER_IDS = set()   # populated during seeding


def _read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed():
    Base.metadata.drop_all(bind=engine)   # Always rebuild with fresh Phase 2 schema
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── Users ────────────────────────────────────────────────────────
        print("Seeding users ...")
        for row in _read_csv("users.csv"):
            db.add(User(
                user_id          = row["user_id"],
                organisation_id  = row["organisation_id"],
                user_type        = row["user_type"],
                role             = row["role"],
                permission_level = row["permission_level"],
                clearance_level  = row["clearance_level"],
                account_type     = row["account_type"],
                mfa_enrolled     = row["mfa_enrolled"],
                active_status    = row["active_status"],
                created_date     = row["created_date"],
            ))
            VALID_USER_IDS.add(row["user_id"])
        db.flush()

        # ── Shared Accounts ──────────────────────────────────────────────
        print("Seeding shared accounts ...")
        for row in _read_csv("shared_accounts.csv"):
            db.add(SharedAccount(
                shared_account_id   = row["shared_account_id"],
                account_name        = row["account_name"],
                application_id      = row["application_id"],
                application_name    = row["application_name"],
                organisation_id     = row["organisation_id"],
                account_type        = row["account_type"],
                risk_level          = row["risk_level"],
                known_users_count   = int(row["known_users_count"]),
                requires_delegation = row["requires_delegation"],
                status              = row["status"],
                created_date        = row["created_date"],
            ))
        db.flush()

        # ── Delegation Sessions (synthetic — one per unique session_id from logs) ─
        print("Seeding delegation sessions ...")
        action_rows   = _read_csv("privileged_actions.csv")
        log_rows      = _read_csv("system_logs.csv")

        # Collect all session IDs and their context from privileged_actions
        seen_sessions = {}
        for row in action_rows:
            sid = row["session_id"]
            if sid not in seen_sessions:
                uid = row["attributed_user_id"] if row["attributed_user_id"] in VALID_USER_IDS else None
                seen_sessions[sid] = {
                    "session_id":        sid,
                    "user_id":           uid,
                    "shared_account_id": row["shared_account_id"],
                    "delegation_token":  row["delegation_token"],
                    "start_time":        row["timestamp"],
                    "end_time":          None,
                    "status":            "closed",
                    "justification":     row.get("justification",""),
                }

        # Also add sessions from system_logs that don't appear in privileged_actions
        priv_session_ids = set(seen_sessions.keys())
        for row in log_rows:
            sid = row["session_id"]
            if sid not in seen_sessions:
                seen_sessions[sid] = {
                    "session_id":        sid,
                    "user_id":           None,
                    "shared_account_id": row["shared_account_id"],
                    "delegation_token":  f"TOK-BASELINE-{sid}",
                    "start_time":        row["timestamp"],
                    "end_time":          None,
                    "status":            "closed",
                    "justification":     "Baseline session (no delegation token)",
                }

        for s in seen_sessions.values():
            db.add(DelegationSession(**s))
        db.flush()

        # ── System Logs (baseline) ───────────────────────────────────────
        print(f"Seeding system logs ({len(log_rows)} records) ...")
        for row in log_rows:
            db.add(SystemLog(
                log_id                = row["log_id"],
                timestamp             = row["timestamp"],
                session_id            = row["session_id"],
                shared_account_id     = row["shared_account_id"],
                application           = row["application"],
                action                = row["action"],
                organisation_id       = row["organisation_id"],
                device_id             = row["device_id"],
                identity_evidence     = row["identity_evidence"],
                log_status            = row["log_status"],
                individual_identified = row["individual_identified"],
                sensitivity           = row["sensitivity"],
            ))
        db.flush()

        # ── Privileged Actions (prototype) ───────────────────────────────
        print(f"Seeding privileged actions ({len(action_rows)} records) ...")
        for row in action_rows:
            uid = row["attributed_user_id"] if row["attributed_user_id"] in VALID_USER_IDS else None
            db.add(PrivilegedAction(
                action_id              = row["action_id"],
                timestamp              = row["timestamp"],
                session_id             = row["session_id"],
                shared_account_id      = row["shared_account_id"],
                organisation_id        = row["organisation_id"],
                application            = row["application"],
                action_type            = row["action_type"],
                sensitivity            = row["sensitivity"],
                required_permission    = row["required_permission"],
                user_permission        = row["user_permission"],
                delegation_token       = row["delegation_token"],
                attributed_user_id     = row["attributed_user_id"],
                attribution_status     = row["attribution_status"],
                attribution_confidence = row["attribution_confidence"],
                identity_evidence      = row["identity_evidence"],
                justification          = row.get("justification",""),
                scenario_tag           = row.get("scenario_tag",""),
                user_id                = uid,
            ))

        db.commit()
        print("Seeding complete.")

    except Exception as e:
        db.rollback()
        print(f"Seeding error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
