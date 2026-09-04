"""
generate_datasets.py
====================
Phase 2 — Synthetic Dataset Generator
Project: Shared-Account Elimination Workflow Using Accountable Delegation
         and Session Attribution

Generates four CSV files with full referential integrity:
  - users.csv
  - shared_accounts.csv
  - system_logs.csv
  - privileged_actions.csv

Run from the backend/ directory:
    python generate_datasets.py

Or specify an output directory:
    python generate_datasets.py --out ./data
"""

import csv
import random
import argparse
import os
from datetime import datetime, timedelta

# ── Reproducibility ──────────────────────────────────────────────────────────
random.seed(42)

# ── Output directory ─────────────────────────────────────────────────────────
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ── Date range for all timestamps ────────────────────────────────────────────
SIM_START = datetime(2026, 7, 1, 8, 0, 0)
SIM_END   = datetime(2026, 9, 3, 18, 0, 0)

def rand_ts(start=SIM_START, end=SIM_END):
    delta = end - start
    return (start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))).strftime("%Y-%m-%dT%H:%M:%S")

def ts_after(base_ts, min_s=30, max_s=3600):
    base = datetime.strptime(base_ts, "%Y-%m-%dT%H:%M:%S")
    return (base + timedelta(seconds=random.randint(min_s, max_s))).strftime("%Y-%m-%dT%H:%M:%S")


# ════════════════════════════════════════════════════════════════════════════
# 1.  REFERENCE TABLES  (fixed vocabularies)
# ════════════════════════════════════════════════════════════════════════════

ORGANISATIONS = [
    ("ORG001", "Digital Governance Authority",        "government"),
    ("ORG002", "National Revenue Directorate",        "government"),
    ("ORG003", "Public Infrastructure Bureau",        "government"),
    ("ORG004", "CyberShield Audit Services",          "external_auditor"),
    ("ORG005", "TechPartner Solutions Pvt Ltd",       "vendor"),
    ("ORG006", "DataBridge Integration Corp",         "vendor"),
]

APPLICATIONS = [
    ("APP001", "LegacyERP",          "ERP system for finance and treasury operations"),
    ("APP002", "GovPortal",          "Citizen-facing government service portal"),
    ("APP003", "NetworkMonitor",     "Internal network and firewall management tool"),
    ("APP004", "CoreDatabase",       "Central government PostgreSQL database cluster"),
    ("APP005", "HRManagement",       "Human resources and payroll management system"),
    ("APP006", "ProcurementHub",     "Vendor registration and procurement approval"),
    ("APP007", "AuditTrailSystem",   "Centralised audit log aggregation platform"),
    ("APP008", "IdentityBroker",     "Legacy SSO and identity federation service"),
]

PERMISSION_LEVELS = ["L1", "L2", "L3", "L4"]

ROLES_BY_TYPE = {
    "government_employee": [
        "Finance Officer", "Treasury Analyst", "Revenue Inspector",
        "Procurement Officer", "Data Entry Operator", "Policy Analyst",
    ],
    "security_administrator": [
        "Security Admin", "IAM Engineer", "SOC Analyst",
    ],
    "auditor": [
        "Internal Auditor", "External Auditor", "Compliance Reviewer",
    ],
    "external_partner": [
        "Vendor Support Engineer", "System Integration Specialist",
        "Maintenance Technician", "Consultant",
    ],
}

PERMISSION_BY_TYPE = {
    "government_employee":    ["L1", "L2"],
    "security_administrator": ["L3", "L4"],
    "auditor":                ["L2", "L3"],
    "external_partner":       ["L1"],
}

ACTIONS_BY_APP = {
    "APP001": ["LOGIN", "VIEW_FINANCIAL_REPORT", "MODIFY_BUDGET_ENTRY",
               "APPROVE_PAYMENT", "EXPORT_PAYROLL_DATA", "RESET_USER_PASSWORD",
               "GENERATE_FINANCIAL_STATEMENT", "BULK_DATA_IMPORT"],
    "APP002": ["LOGIN", "VIEW_CITIZEN_RECORD", "UPDATE_CITIZEN_RECORD",
               "DELETE_CITIZEN_RECORD", "APPROVE_CITIZEN_REQUEST",
               "EXPORT_CITIZEN_DATA", "VIEW_AUDIT_LOG"],
    "APP003": ["LOGIN", "VIEW_NETWORK_TOPOLOGY", "MODIFY_FIREWALL_RULE",
               "VIEW_TRAFFIC_LOGS", "BLOCK_IP_ADDRESS", "CONFIGURE_VPN",
               "PATCH_DEVICE_FIRMWARE"],
    "APP004": ["LOGIN", "BACKUP_DATABASE", "RESTORE_DATABASE", "DROP_TABLE",
               "BULK_DELETE_RECORDS", "MODIFY_SCHEMA", "GRANT_DB_ACCESS",
               "VIEW_SENSITIVE_TABLE"],
    "APP005": ["LOGIN", "VIEW_EMPLOYEE_RECORD", "MODIFY_SALARY",
               "PROCESS_PAYROLL", "EXPORT_HR_DATA", "CREATE_EMPLOYEE",
               "TERMINATE_EMPLOYEE"],
    "APP006": ["LOGIN", "VIEW_VENDOR_RECORD", "APPROVE_VENDOR",
               "BLACKLIST_VENDOR", "MODIFY_CONTRACT", "VIEW_PROCUREMENT_LOG",
               "GENERATE_PURCHASE_ORDER"],
    "APP007": ["LOGIN", "VIEW_AUDIT_LOG", "EXPORT_AUDIT_REPORT",
               "ARCHIVE_LOG_ENTRIES", "SEARCH_LOG_ENTRIES"],
    "APP008": ["LOGIN", "VIEW_IDENTITY_CONFIG", "MODIFY_SSO_POLICY",
               "CREATE_DELEGATION_TOKEN", "REVOKE_DELEGATION_TOKEN",
               "VIEW_SESSION_LIST", "FORCE_LOGOUT_SESSION"],
}

SENSITIVITY_BY_ACTION = {
    "LOGIN":                        "LOW",
    "VIEW_FINANCIAL_REPORT":        "MEDIUM",
    "MODIFY_BUDGET_ENTRY":          "HIGH",
    "APPROVE_PAYMENT":              "HIGH",
    "EXPORT_PAYROLL_DATA":          "HIGH",
    "RESET_USER_PASSWORD":          "HIGH",
    "GENERATE_FINANCIAL_STATEMENT": "MEDIUM",
    "BULK_DATA_IMPORT":             "HIGH",
    "VIEW_CITIZEN_RECORD":          "MEDIUM",
    "UPDATE_CITIZEN_RECORD":        "HIGH",
    "DELETE_CITIZEN_RECORD":        "CRITICAL",
    "APPROVE_CITIZEN_REQUEST":      "HIGH",
    "EXPORT_CITIZEN_DATA":          "HIGH",
    "VIEW_AUDIT_LOG":               "LOW",
    "VIEW_NETWORK_TOPOLOGY":        "MEDIUM",
    "MODIFY_FIREWALL_RULE":         "CRITICAL",
    "VIEW_TRAFFIC_LOGS":            "LOW",
    "BLOCK_IP_ADDRESS":             "HIGH",
    "CONFIGURE_VPN":                "HIGH",
    "PATCH_DEVICE_FIRMWARE":        "CRITICAL",
    "BACKUP_DATABASE":              "HIGH",
    "RESTORE_DATABASE":             "CRITICAL",
    "DROP_TABLE":                   "CRITICAL",
    "BULK_DELETE_RECORDS":          "CRITICAL",
    "MODIFY_SCHEMA":                "CRITICAL",
    "GRANT_DB_ACCESS":              "CRITICAL",
    "VIEW_SENSITIVE_TABLE":         "HIGH",
    "VIEW_EMPLOYEE_RECORD":         "MEDIUM",
    "MODIFY_SALARY":                "CRITICAL",
    "PROCESS_PAYROLL":              "HIGH",
    "EXPORT_HR_DATA":               "HIGH",
    "CREATE_EMPLOYEE":              "HIGH",
    "TERMINATE_EMPLOYEE":           "CRITICAL",
    "VIEW_VENDOR_RECORD":           "LOW",
    "APPROVE_VENDOR":               "HIGH",
    "BLACKLIST_VENDOR":             "HIGH",
    "MODIFY_CONTRACT":              "HIGH",
    "VIEW_PROCUREMENT_LOG":         "LOW",
    "GENERATE_PURCHASE_ORDER":      "HIGH",
    "EXPORT_AUDIT_REPORT":          "MEDIUM",
    "ARCHIVE_LOG_ENTRIES":          "MEDIUM",
    "SEARCH_LOG_ENTRIES":           "LOW",
    "VIEW_IDENTITY_CONFIG":         "HIGH",
    "MODIFY_SSO_POLICY":            "CRITICAL",
    "CREATE_DELEGATION_TOKEN":      "HIGH",
    "REVOKE_DELEGATION_TOKEN":      "HIGH",
    "VIEW_SESSION_LIST":            "MEDIUM",
    "FORCE_LOGOUT_SESSION":         "HIGH",
}

REQUIRED_PERMISSION_BY_SENSITIVITY = {
    "LOW":      "L1",
    "MEDIUM":   "L2",
    "HIGH":     "L3",
    "CRITICAL": "L4",
}

DEVICE_PREFIXES = ["WS", "LT", "SRV", "MB"]

IDENTITY_EVIDENCE_TYPES = [
    "SMARTCARD_AND_PIN",
    "PASSWORD_ONLY",
    "OTP_TOKEN",
    "BIOMETRIC_AND_PIN",
    "VPN_CERTIFICATE",
    "NONE",
]

JUSTIFICATION_TEMPLATES = [
    "Routine {role} duty -- ref {ref}",
    "Authorised by supervisor -- ticket {ref}",
    "Scheduled maintenance window MW-{ref}",
    "Emergency change EC-{ref}",
    "Audit requirement AR-{ref}",
    "Vendor SLA task VT-{ref}",
    "Data correction request CR-{ref}",
    "Incident response IR-{ref}",
]


def rand_ref():
    return str(random.randint(1000, 9999))


def make_device_id():
    return f"{random.choice(DEVICE_PREFIXES)}-{random.randint(10000,99999)}"


# ════════════════════════════════════════════════════════════════════════════
# 2.  USERS (20 records)
# ════════════════════════════════════════════════════════════════════════════

def generate_users():
    rows = []
    uid = 1

    distribution = (
        [("government_employee",    "ORG001")] * 4 +
        [("government_employee",    "ORG002")] * 3 +
        [("government_employee",    "ORG003")] * 3 +
        [("security_administrator", "ORG001")] * 2 +
        [("security_administrator", "ORG002")] * 2 +
        [("auditor",                "ORG004")] * 2 +
        [("auditor",                "ORG001")] * 1 +
        [("external_partner",       "ORG005")] * 2 +
        [("external_partner",       "ORG006")] * 1
    )

    for user_type, org_id in distribution:
        role         = random.choice(ROLES_BY_TYPE[user_type])
        perm_level   = random.choice(PERMISSION_BY_TYPE[user_type])
        account_type = "internal" if org_id in ("ORG001","ORG002","ORG003") else "external"
        mfa_enrolled = "YES" if perm_level in ("L3","L4") else random.choice(["YES","NO"])
        created_date = (SIM_START - timedelta(days=random.randint(30,1800))).strftime("%Y-%m-%d")

        rows.append({
            "user_id":          f"USER{uid:03d}",
            "organisation_id":  org_id,
            "user_type":        user_type,
            "role":             role,
            "permission_level": perm_level,
            "clearance_level":  perm_level,
            "account_type":     account_type,
            "mfa_enrolled":     mfa_enrolled,
            "active_status":    "ACTIVE",
            "created_date":     created_date,
        })
        uid += 1

    # Mark last 2 as INACTIVE for realism
    for i in range(1, 3):
        rows[-i]["active_status"] = "INACTIVE"

    return rows


# ════════════════════════════════════════════════════════════════════════════
# 3.  SHARED ACCOUNTS (8 records)
# ════════════════════════════════════════════════════════════════════════════

SHARED_ACCOUNT_DEFINITIONS = [
    ("SACC001", "admin_shared",       "APP001", "ORG001", "shared_admin",    "HIGH",     "ACTIVE", 6),
    ("SACC002", "operator_shared",    "APP001", "ORG001", "shared_operator", "MEDIUM",   "ACTIVE", 8),
    ("SACC003", "legacy_admin",       "APP002", "ORG001", "legacy_admin",    "HIGH",     "ACTIVE", 4),
    ("SACC004", "sysop_shared",       "APP003", "ORG002", "shared_operator", "HIGH",     "ACTIVE", 3),
    ("SACC005", "db_admin_shared",    "APP004", "ORG001", "shared_admin",    "CRITICAL", "ACTIVE", 2),
    ("SACC006", "hr_shared",          "APP005", "ORG002", "shared_operator", "HIGH",     "ACTIVE", 5),
    ("SACC007", "procurement_shared", "APP006", "ORG003", "shared_operator", "MEDIUM",   "ACTIVE", 7),
    ("SACC008", "audit_viewer",       "APP007", "ORG004", "read_only",       "LOW",      "ACTIVE", 4),
]

def generate_shared_accounts():
    rows = []
    for acc_id, acc_name, app_id, org_id, acc_type, risk, status, known_count in SHARED_ACCOUNT_DEFINITIONS:
        app_name = next(a[1] for a in APPLICATIONS if a[0] == app_id)
        created  = (SIM_START - timedelta(days=random.randint(365, 3000))).strftime("%Y-%m-%d")
        rows.append({
            "shared_account_id":   acc_id,
            "account_name":        acc_name,
            "application_id":      app_id,
            "application_name":    app_name,
            "organisation_id":     org_id,
            "account_type":        acc_type,
            "risk_level":          risk,
            "known_users_count":   known_count,
            "requires_delegation": "YES" if risk in ("HIGH","CRITICAL") else "NO",
            "status":              status,
            "created_date":        created,
        })
    return rows


# ════════════════════════════════════════════════════════════════════════════
# 4.  SESSIONS  (internal helper — not exported as CSV)
# ════════════════════════════════════════════════════════════════════════════

def generate_sessions(users, shared_accounts, n=80):
    sessions = []
    active_users = [u for u in users if u["active_status"] == "ACTIVE"]

    for i in range(1, n + 1):
        user  = random.choice(active_users)
        sacc  = random.choice(shared_accounts)
        start = rand_ts()
        end   = ts_after(start, 300, 7200)

        scenario = random.choices(
            ["normal", "external_partner", "high_privilege",
             "failed_permission", "missing_evidence", "attributed"],
            weights=[35, 15, 15, 10, 10, 15],
            k=1
        )[0]

        if scenario == "external_partner":
            ext = [u for u in active_users if u["account_type"] == "external"]
            user = random.choice(ext) if ext else user
        elif scenario == "high_privilege":
            hi  = [u for u in active_users if u["permission_level"] in ("L3","L4")]
            user = random.choice(hi) if hi else user

        delegation_token = (
            f"TOK-{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"
            f"{random.randint(100,999)}"
            f"{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"
            f"{random.randint(10,99)}"
        )

        sessions.append({
            "session_id":        f"SESSION{i:03d}",
            "user_id":           user["user_id"],
            "user_type":         user["user_type"],
            "user_perm":         user["permission_level"],
            "org_id":            user["organisation_id"],
            "shared_account_id": sacc["shared_account_id"],
            "application_id":    sacc["application_id"],
            "application_name":  sacc["application_name"],
            "risk_level":        sacc["risk_level"],
            "start_time":        start,
            "end_time":          end,
            "delegation_token":  delegation_token,
            "scenario":          scenario,
            "device_id":         make_device_id(),
        })
    return sessions


# ════════════════════════════════════════════════════════════════════════════
# 5.  SYSTEM LOGS  (120+ records — baseline, no individual attribution)
# ════════════════════════════════════════════════════════════════════════════

def pick_identity_evidence(scenario):
    if scenario == "missing_evidence":
        return "NONE"
    if scenario == "external_partner":
        return random.choice(["VPN_CERTIFICATE", "OTP_TOKEN", "PASSWORD_ONLY"])
    if scenario in ("high_privilege", "attributed"):
        return random.choice(["SMARTCARD_AND_PIN", "BIOMETRIC_AND_PIN", "OTP_TOKEN"])
    if scenario == "failed_permission":
        return random.choice(["PASSWORD_ONLY", "NONE", "OTP_TOKEN"])
    return random.choice(["SMARTCARD_AND_PIN", "PASSWORD_ONLY", "OTP_TOKEN", "BIOMETRIC_AND_PIN"])


def generate_system_logs(sessions, target=120):
    rows  = []
    log_id = 1

    shuffled = sessions[:]
    random.shuffle(shuffled)

    for sess in shuffled:
        n_actions = random.randint(1, 3)
        app_acts  = ACTIONS_BY_APP.get(sess["application_id"], ["LOGIN"])
        ts        = sess["start_time"]

        for _ in range(n_actions):
            action   = random.choice(app_acts)
            scenario = sess["scenario"]

            if scenario == "failed_permission":
                high_acts = [a for a in app_acts
                             if SENSITIVITY_BY_ACTION.get(a,"LOW") in ("HIGH","CRITICAL")]
                action = random.choice(high_acts) if high_acts else action

            sensitivity   = SENSITIVITY_BY_ACTION.get(action, "LOW")
            required_perm = REQUIRED_PERMISSION_BY_SENSITIVITY[sensitivity]
            user_perm     = sess["user_perm"]
            evidence      = pick_identity_evidence(scenario)

            if scenario == "failed_permission" and user_perm < required_perm:
                log_status = "PERMISSION_DENIED"
            elif evidence == "NONE":
                log_status = "ANONYMOUS_ACTION"
            elif scenario == "missing_evidence":
                log_status = random.choice(["ANONYMOUS_ACTION", "WEAK_EVIDENCE"])
            else:
                log_status = "RECORDED"

            rows.append({
                "log_id":               f"LOG{log_id:04d}",
                "timestamp":            ts,
                "session_id":           sess["session_id"],
                "shared_account_id":    sess["shared_account_id"],
                "application":          sess["application_name"],
                "action":               action,
                "organisation_id":      sess["org_id"],
                "device_id":            sess["device_id"],
                "identity_evidence":    evidence,
                "log_status":           log_status,
                "individual_identified":"NO",
                "sensitivity":          sensitivity,
            })
            log_id += 1
            ts = ts_after(ts, 10, 600)

        if log_id > target + 20:
            break

    while len(rows) < target:
        sess     = random.choice(sessions)
        app_acts = ACTIONS_BY_APP.get(sess["application_id"], ["LOGIN"])
        action   = random.choice(app_acts)
        evidence = pick_identity_evidence(sess["scenario"])
        rows.append({
            "log_id":               f"LOG{log_id:04d}",
            "timestamp":            rand_ts(),
            "session_id":           sess["session_id"],
            "shared_account_id":    sess["shared_account_id"],
            "application":          sess["application_name"],
            "action":               action,
            "organisation_id":      sess["org_id"],
            "device_id":            sess["device_id"],
            "identity_evidence":    evidence,
            "log_status":           "RECORDED",
            "individual_identified":"NO",
            "sensitivity":          SENSITIVITY_BY_ACTION.get(action, "LOW"),
        })
        log_id += 1

    rows.sort(key=lambda r: r["timestamp"])
    return rows


# ════════════════════════════════════════════════════════════════════════════
# 6.  PRIVILEGED ACTIONS  (60+ records — prototype, with attribution)
# ════════════════════════════════════════════════════════════════════════════

def generate_privileged_actions(sessions, users, target=60):
    rows    = []
    act_id  = 1
    user_map = {u["user_id"]: u for u in users}

    important = [s for s in sessions if s["risk_level"] in ("HIGH","CRITICAL")]
    pool      = important + random.choices(sessions, k=max(0, target - len(important)))
    random.shuffle(pool)

    for sess in pool:
        app_acts  = ACTIONS_BY_APP.get(sess["application_id"], ["LOGIN"])
        sensitive = [a for a in app_acts
                     if SENSITIVITY_BY_ACTION.get(a,"LOW") in ("HIGH","CRITICAL")]
        if not sensitive:
            sensitive = app_acts

        action        = random.choice(sensitive)
        sensitivity   = SENSITIVITY_BY_ACTION.get(action, "HIGH")
        required_perm = REQUIRED_PERMISSION_BY_SENSITIVITY[sensitivity]
        scenario      = sess["scenario"]
        user          = user_map.get(sess["user_id"], {})
        user_perm     = user.get("permission_level", "L1")

        if scenario == "failed_permission":
            attr_status     = "PERMISSION_DENIED"
            attr_user       = "NONE"
            attr_confidence = "N/A"
        elif scenario == "missing_evidence":
            attr_status     = "UNATTRIBUTED"
            attr_user       = "UNKNOWN"
            attr_confidence = "LOW"
        elif scenario == "external_partner":
            attr_status     = "ATTRIBUTED"
            attr_user       = sess["user_id"]
            attr_confidence = random.choice(["MEDIUM","HIGH"])
        else:
            attr_status     = "ATTRIBUTED"
            attr_user       = sess["user_id"]
            attr_confidence = "HIGH"

        justification = random.choice(JUSTIFICATION_TEMPLATES).format(
            role=user.get("role","Officer"), ref=rand_ref()
        )

        rows.append({
            "action_id":              f"ACT{act_id:04d}",
            "timestamp":              ts_after(sess["start_time"], 60, 3000),
            "session_id":             sess["session_id"],
            "shared_account_id":      sess["shared_account_id"],
            "organisation_id":        sess["org_id"],
            "application":            sess["application_name"],
            "action_type":            action,
            "sensitivity":            sensitivity,
            "required_permission":    required_perm,
            "user_permission":        user_perm,
            "delegation_token":       sess["delegation_token"],
            "attributed_user_id":     attr_user,
            "attribution_status":     attr_status,
            "attribution_confidence": attr_confidence,
            "identity_evidence":      pick_identity_evidence(scenario),
            "justification":          justification,
            "scenario_tag":           scenario,
        })
        act_id += 1

        if act_id > target:
            break

    while len(rows) < target:
        sess   = random.choice(sessions)
        action = random.choice(ACTIONS_BY_APP.get(sess["application_id"], ["LOGIN"]))
        rows.append({
            "action_id":              f"ACT{act_id:04d}",
            "timestamp":              ts_after(sess["start_time"], 60, 1800),
            "session_id":             sess["session_id"],
            "shared_account_id":      sess["shared_account_id"],
            "organisation_id":        sess["org_id"],
            "application":            sess["application_name"],
            "action_type":            action,
            "sensitivity":            SENSITIVITY_BY_ACTION.get(action, "MEDIUM"),
            "required_permission":    REQUIRED_PERMISSION_BY_SENSITIVITY.get(
                                          SENSITIVITY_BY_ACTION.get(action,"MEDIUM"), "L2"),
            "user_permission":        user_map.get(sess["user_id"],{}).get("permission_level","L2"),
            "delegation_token":       sess["delegation_token"],
            "attributed_user_id":     sess["user_id"],
            "attribution_status":     "ATTRIBUTED",
            "attribution_confidence": "HIGH",
            "identity_evidence":      pick_identity_evidence("normal"),
            "justification":          random.choice(JUSTIFICATION_TEMPLATES).format(
                                          role="Officer", ref=rand_ref()),
            "scenario_tag":           "normal",
        })
        act_id += 1

    rows.sort(key=lambda r: r["timestamp"])
    return rows


# ════════════════════════════════════════════════════════════════════════════
# 7.  VALIDATION
# ════════════════════════════════════════════════════════════════════════════

def validate(users, shared_accounts, logs, actions):
    errors   = []
    user_ids = {u["user_id"] for u in users}
    sacc_ids = {s["shared_account_id"] for s in shared_accounts}

    for u in users:
        if u["permission_level"] not in PERMISSION_LEVELS:
            errors.append(f"Invalid permission level for {u['user_id']}")

    for l in logs:
        if l["shared_account_id"] not in sacc_ids:
            errors.append(f"LOG {l['log_id']} references unknown shared_account {l['shared_account_id']}")

    for a in actions:
        if a["attributed_user_id"] not in user_ids | {"NONE","UNKNOWN"}:
            errors.append(f"ACT {a['action_id']} references unknown user {a['attributed_user_id']}")
        if a["shared_account_id"] not in sacc_ids:
            errors.append(f"ACT {a['action_id']} references unknown shared_account {a['shared_account_id']}")

    return errors


# ════════════════════════════════════════════════════════════════════════════
# 8.  WRITE CSV
# ════════════════════════════════════════════════════════════════════════════

def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):4d} rows  ->  {path}")


# ════════════════════════════════════════════════════════════════════════════
# 9.  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main(out_dir):
    print(f"\nPhase 2 - Synthetic Dataset Generator")
    print(f"Output directory: {out_dir}\n")

    print("Generating users ...")
    users = generate_users()

    print("Generating shared accounts ...")
    shared_accounts = generate_shared_accounts()

    print("Generating sessions (internal) ...")
    sessions = generate_sessions(users, shared_accounts, n=80)

    print("Generating system logs (baseline) ...")
    logs = generate_system_logs(sessions, target=120)

    print("Generating privileged actions (prototype) ...")
    actions = generate_privileged_actions(sessions, users, target=60)

    print("\nValidating referential integrity ...")
    errors = validate(users, shared_accounts, logs, actions)
    if errors:
        print(f"  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  All checks passed.")

    print("\nWriting CSV files ...")
    write_csv(
        os.path.join(out_dir, "users.csv"),
        users,
        ["user_id","organisation_id","user_type","role","permission_level",
         "clearance_level","account_type","mfa_enrolled","active_status","created_date"],
    )
    write_csv(
        os.path.join(out_dir, "shared_accounts.csv"),
        shared_accounts,
        ["shared_account_id","account_name","application_id","application_name",
         "organisation_id","account_type","risk_level","known_users_count",
         "requires_delegation","status","created_date"],
    )
    write_csv(
        os.path.join(out_dir, "system_logs.csv"),
        logs,
        ["log_id","timestamp","session_id","shared_account_id","application",
         "action","organisation_id","device_id","identity_evidence",
         "log_status","individual_identified","sensitivity"],
    )
    write_csv(
        os.path.join(out_dir, "privileged_actions.csv"),
        actions,
        ["action_id","timestamp","session_id","shared_account_id","organisation_id",
         "application","action_type","sensitivity","required_permission",
         "user_permission","delegation_token","attributed_user_id",
         "attribution_status","attribution_confidence","identity_evidence",
         "justification","scenario_tag"],
    )

    # Summary stats
    attributed   = sum(1 for a in actions if a["attribution_status"] == "ATTRIBUTED")
    unattributed = sum(1 for a in actions if a["attribution_status"] == "UNATTRIBUTED")
    denied       = sum(1 for a in actions if a["attribution_status"] == "PERMISSION_DENIED")
    total        = len(actions)
    iar          = round(attributed / total * 100, 2) if total else 0

    print(f"""
Dataset Summary
-----------------------------------------------------------
  users.csv              {len(users):>4d} records
  shared_accounts.csv    {len(shared_accounts):>4d} records
  system_logs.csv        {len(logs):>4d} records  (baseline)
  privileged_actions.csv {len(actions):>4d} records  (prototype)

Privileged Actions Breakdown
  ATTRIBUTED        {attributed:>4d}  ({attributed/total*100:.1f}%)
  UNATTRIBUTED      {unattributed:>4d}  ({unattributed/total*100:.1f}%)
  PERMISSION_DENIED {denied:>4d}  ({denied/total*100:.1f}%)

IAR (prototype): {iar}%
-----------------------------------------------------------
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 2 Synthetic Dataset Generator")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output directory")
    args = parser.parse_args()
    main(args.out)
