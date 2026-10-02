"""
seed.py — Seeds the SQLite database from CSV datasets and initializes Review 2
components: active sessions, explanation layer data, and human review queue.
"""

import csv
import os
from datetime import datetime, timezone, timedelta
from database import engine, SessionLocal, Base
from models import User, SharedAccount, SystemLog, DelegationSession, PrivilegedAction, HumanReview
from services.explanation_service import build_explanation, serialize_explanation
from services.evaluation_service import compute_metrics, save_evaluation_results

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
VALID_USER_IDS = set()


def _read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── 1. Users ─────────────────────────────────────────────────────
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

        # ── 2. Shared Accounts ───────────────────────────────────────────
        print("Seeding shared accounts ...")
        account_map = {}
        for row in _read_csv("shared_accounts.csv"):
            acc = SharedAccount(
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
            )
            db.add(acc)
            account_map[acc.shared_account_id] = acc
        db.flush()

        # ── 3. Delegation Sessions ───────────────────────────────────────
        print("Seeding delegation sessions ...")
        action_rows = _read_csv("privileged_actions.csv")
        log_rows    = _read_csv("system_logs.csv")

        now = datetime.now(timezone.utc)
        seen_sessions = {}
        for idx, row in enumerate(action_rows):
            sid = row["session_id"]
            if sid not in seen_sessions:
                uid = row["attributed_user_id"] if row["attributed_user_id"] in VALID_USER_IDS else None
                user = db.query(User).filter(User.user_id == uid).first() if uid else None
                acc = account_map.get(row["shared_account_id"])

                # Make the most recent 3 sessions active for live demonstration
                is_recent = idx < 3 and uid is not None
                sess_status = "active" if is_recent else "closed"
                st_time = (now - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ") if is_recent else row["timestamp"]
                end_time = (now + timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%SZ") if is_recent else (now - timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

                seen_sessions[sid] = {
                    "session_id":        sid,
                    "user_id":           uid,
                    "shared_account_id": row["shared_account_id"],
                    "organisation_id":   user.organisation_id if user else (acc.organisation_id if acc else "ORG001"),
                    "delegation_token":  row["delegation_token"],
                    "start_time":        st_time,
                    "end_time":          end_time,
                    "status":            sess_status,
                    "justification":     row.get("justification", "Routine delegation session"),
                    "granted_level":     user.permission_level if user else "L2",
                }

        # Add sessions from system_logs that don't appear in privileged_actions
        for row in log_rows:
            sid = row["session_id"]
            if sid not in seen_sessions:
                seen_sessions[sid] = {
                    "session_id":        sid,
                    "user_id":           None,
                    "shared_account_id": row["shared_account_id"],
                    "organisation_id":   row["organisation_id"],
                    "delegation_token":  f"TOK-BASELINE-{sid}",
                    "start_time":        row["timestamp"],
                    "end_time":          row["timestamp"],
                    "status":            "closed",
                    "justification":     "Baseline session (no delegation token)",
                    "granted_level":     "L1",
                }

        for s in seen_sessions.values():
            db.add(DelegationSession(**s))
        db.flush()

        # ── 4. System Logs (baseline) ────────────────────────────────────
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

        # ── 5. Privileged Actions (prototype with explanations) ───────────
        print(f"Seeding privileged actions ({len(action_rows)} records) ...")
        for idx, row in enumerate(action_rows):
            uid = row["attributed_user_id"] if row["attributed_user_id"] in VALID_USER_IDS else None
            acc = account_map.get(row["shared_account_id"])
            acc_name = acc.account_name if acc else row["shared_account_id"]

            attr_status = row["attribution_status"]
            attr_user = row["attributed_user_id"]

            # Build evidence checklist
            evidence_items = [
                f"Identity Record: '{attr_user}'",
                f"Delegation Token: '{row['delegation_token']}'",
                f"Session Reference: '{row['session_id']}'",
                f"User Clearance: '{row['user_permission']}' vs Action Requirement: '{row['required_permission']}'",
                f"Identity Telemetry: '{row.get('identity_evidence', 'TOKEN')}'"
            ]

            explanation = build_explanation(
                action_type=row["action_type"],
                attributed_user_id=attr_user,
                session_id=row["session_id"],
                shared_account_id=row["shared_account_id"],
                shared_account_name=acc_name,
                user_permission=row["user_permission"],
                required_permission=row["required_permission"],
                attribution_status=attr_status,
                status_reason=f"Action processed with status '{attr_status}' during maintenance window.",
                evidence_items=evidence_items,
                is_external=(row["organisation_id"] in ["ORG005", "ORG006"])
            )

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
                attributed_user_id     = attr_user,
                attribution_status     = attr_status,
                attribution_confidence = row["attribution_confidence"],
                identity_evidence      = row["identity_evidence"],
                justification          = row.get("justification",""),
                scenario_tag           = row.get("scenario_tag","normal"),
                explanation            = serialize_explanation(explanation),
                review_status          = "NOT_REQUIRED",
                user_id                = uid,
            ))
        db.flush()

        # ── 6. Initial Seed Cases for Human Review Queue ──────────────────
        print("Seeding initial human review queue cases ...")
        # Review Case 1: An uncertain action with conflicting telemetry (Pending Review)
        uncertain_action_id = "ACT-CONF-001"
        now_iso = (now - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        conflict_evidence = [
            "Active delegation session 'SESSION053' issued to user 'USER008'",
            "Concurrent terminal command dispatched with client cert of 'USER006'",
            "Network IP address maps to shared workstation room WS-B4",
            "Identity evidence conflict: Multiple candidate operators identified"
        ]
        conflict_explanation = build_explanation(
            action_type="MODIFY_FIREWALL_RULE",
            attributed_user_id="UNCERTAIN",
            session_id="SESSION053",
            shared_account_id="SACC004",
            shared_account_name="sysop_shared",
            user_permission="L2",
            required_permission="L4",
            attribution_status="UNCERTAIN",
            status_reason="Conflicting identity evidence between session owner (USER008) and client certificate (USER006).",
            evidence_items=conflict_evidence,
            conflict_details="Identity conflict between USER008 and USER006. Dispatched to Human Review Queue."
        )

        db.add(PrivilegedAction(
            action_id              = uncertain_action_id,
            timestamp              = now_iso,
            session_id             = "SESSION053",
            shared_account_id      = "SACC004",
            organisation_id        = "ORG003",
            application            = "NetworkMonitor",
            action_type            = "MODIFY_FIREWALL_RULE",
            sensitivity            = "CRITICAL",
            required_permission    = "L4",
            user_permission        = "L2",
            delegation_token       = "TOK-E584X24",
            attributed_user_id     = "UNCERTAIN",
            attribution_status     = "UNCERTAIN",
            attribution_confidence = "CONFLICT",
            identity_evidence      = "; ".join(conflict_evidence),
            justification          = "Emergency firewall modification during off-hours maintenance",
            scenario_tag           = "conflicting_evidence",
            explanation            = serialize_explanation(conflict_explanation),
            review_status          = "PENDING",
            user_id                = "USER008"
        ))
        db.flush()

        # Create HumanReview record 1 (PENDING)
        db.add(HumanReview(
            review_id           = "REV-0001",
            action_id           = uncertain_action_id,
            session_id          = "SESSION053",
            shared_account_id   = "SACC004",
            claimed_user_id     = "USER008",
            conflicting_user_id = "USER006",
            timestamp           = now_iso,
            available_evidence  = "; ".join(conflict_evidence),
            conflict_reason     = "Session registered to USER008, but SSL client handshake asserted USER006.",
            attribution_status  = "UNCERTAIN",
            review_status       = "PENDING"
        ))

        # Review Case 2: Previously resolved case (CONFIRMED by AUDITOR002)
        resolved_action_id = "ACT-RES-002"
        res_time = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        res_evidence = [
            "Session 'SESSION012' registered to USER008",
            "Physical badge swipe corroborated entry at Server Room B",
            "Signed supervisor authorization ticket #8841 verified"
        ]
        res_explanation = build_explanation(
            action_type="BACKUP_DATABASE",
            attributed_user_id="USER008",
            session_id="SESSION012",
            shared_account_id="SACC004",
            shared_account_name="sysop_shared",
            user_permission="L2",
            required_permission="L3",
            attribution_status="ATTRIBUTED",
            status_reason="Confirmed by forensic reviewer AUDITOR002 following badge swipe and ticket verification.",
            evidence_items=res_evidence
        )
        db.add(PrivilegedAction(
            action_id              = resolved_action_id,
            timestamp              = res_time,
            session_id             = "SESSION012",
            shared_account_id      = "SACC004",
            organisation_id        = "ORG003",
            application            = "NetworkMonitor",
            action_type            = "BACKUP_DATABASE",
            sensitivity            = "HIGH",
            required_permission    = "L3",
            user_permission        = "L2",
            delegation_token       = "TOK-T335U38",
            attributed_user_id     = "USER008",
            attribution_status     = "ATTRIBUTED",
            attribution_confidence = "HUMAN_CONFIRMED (95.0%)",
            identity_evidence      = "; ".join(res_evidence) + " | Corroborated by AUDITOR002",
            justification          = "Scheduled database snapshot verification",
            scenario_tag           = "fallback_confirmed",
            explanation            = serialize_explanation(res_explanation),
            review_status          = "RESOLVED",
            user_id                = "USER008"
        ))
        db.flush()

        db.add(HumanReview(
            review_id           = "REV-0002",
            action_id           = resolved_action_id,
            session_id          = "SESSION012",
            shared_account_id   = "SACC004",
            claimed_user_id     = "USER008",
            conflicting_user_id = "USER010",
            timestamp           = res_time,
            available_evidence  = "; ".join(res_evidence),
            conflict_reason     = "Ambiguous console session between USER008 and USER010.",
            attribution_status  = "ATTRIBUTED",
            review_status       = "CONFIRMED",
            reviewer_id         = "AUDITOR002",
            reviewer_decision   = "CONFIRMED",
            reviewer_reason     = "Physical security badge swipe at Server Room B and signed supervisor ticket conclusively corroborate USER008.",
            reviewed_at         = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ))

        db.commit()

        # Compute initial evaluation metrics and save evaluation_results.json
        print("Computing and saving initial evaluation results ...")
        metrics = compute_metrics(db)
        save_evaluation_results(metrics)
        print("Seeding complete successfully.")

    except Exception as e:
        db.rollback()
        print(f"Seeding error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
