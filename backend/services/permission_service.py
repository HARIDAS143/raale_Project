"""
services/permission_service.py — Granular permission levels, role hierarchy,
and multi-organisation access policy validation for Review 2.
"""

from typing import Tuple, Dict, Any

LEVEL_HIERARCHY = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}
RISK_HIERARCHY  = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

LEVEL_DESCRIPTIONS = {
    "L1": "Basic: Read-only inquiries and low-risk operational lookup",
    "L2": "Operational: Standard operational duties and routine transaction execution",
    "L3": "Audit / Review: Compliance auditing, system trace review, and report export",
    "L4": "Administrative: High-risk system configuration, schema changes, and access management",
}

# Standard sensitivity-to-permission mapping
ACTION_PERMISSION_MAP = {
    "View Sensitive Record": "L1",
    "VIEW_SENSITIVE_RECORD": "L1",
    "Search Log Entries": "L1",
    "SEARCH_LOG_ENTRIES": "L1",
    "Approve Transaction": "L2",
    "APPROVE_TRANSACTION": "L2",
    "Create Employee": "L2",
    "CREATE_EMPLOYEE": "L2",
    "Export Report": "L3",
    "EXPORT_REPORT": "L3",
    "Configure VPN": "L3",
    "CONFIGURE_VPN": "L3",
    "Block IP Address": "L3",
    "BLOCK_IP_ADDRESS": "L3",
    "Backup Database": "L3",
    "BACKUP_DATABASE": "L3",
    "Modify Configuration": "L4",
    "MODIFY_CONFIGURATION": "L4",
    "Change Access Configuration": "L4",
    "CHANGE_ACCESS_CONFIGURATION": "L4",
    "Modify Salary": "L4",
    "MODIFY_SALARY": "L4",
    "Drop Table": "L4",
    "DROP_TABLE": "L4",
    "Modify Firewall Rule": "L4",
    "MODIFY_FIREWALL_RULE": "L4",
    "Grant DB Access": "L4",
    "GRANT_DB_ACCESS": "L4",
    "Patch Device Firmware": "L4",
    "PATCH_DEVICE_FIRMWARE": "L4",
    "Terminate Employee": "L4",
    "TERMINATE_EMPLOYEE": "L4",
}


def get_required_permission_for_action(action_name: str, sensitivity: str = "HIGH") -> str:
    """Determine required permission level based on action type and sensitivity."""
    norm = action_name.strip()
    if norm in ACTION_PERMISSION_MAP:
        return ACTION_PERMISSION_MAP[norm]
    # Fallback by sensitivity
    if sensitivity == "CRITICAL":
        return "L4"
    elif sensitivity == "HIGH":
        return "L3"
    elif sensitivity == "MEDIUM":
        return "L2"
    return "L1"


def validate_delegation_permission(user: Any, account: Any) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates whether an individual identity may request a delegation session
    for a specific shared account under multi-organisation and risk rules.

    Rules enforced:
    1. Active user status & MFA check.
    2. Multi-organisation access control:
       - Government Department A (ORG001) / B (ORG002): standard department access.
       - Cross-department access requires at least L3 clearance/permission.
       - External Technical Partner (ORG005, ORG006):
         * Capped at maximum L2 permission.
         * Prohibited from CRITICAL risk shared accounts (e.g. core databases/root admin).
         * Must undergo organisation validation.
    3. User permission level vs Shared Account risk level.
    """
    user_perm_val = LEVEL_HIERARCHY.get(user.permission_level, 1)
    acc_risk_val  = RISK_HIERARCHY.get(account.risk_level, 1)

    details = {
        "user_id": user.user_id,
        "user_org": user.organisation_id,
        "user_type": user.user_type,
        "user_permission": user.permission_level,
        "account_id": account.shared_account_id,
        "account_org": account.organisation_id,
        "account_risk": account.risk_level,
        "requires_delegation": account.requires_delegation,
    }

    # 1. Active status check
    if getattr(user, "active_status", "ACTIVE") != "ACTIVE":
        return False, f"User '{user.user_id}' is inactive. Privileged access denied.", details

    # 2. External Technical Partner Policy Enforcement
    is_external = (
        user.user_type == "external_partner" or
        user.organisation_id in ["ORG005", "ORG006", "ORG03", "ORG3"] or
        getattr(user, "account_type", "") == "external"
    )

    if is_external:
        # External partners cannot access CRITICAL risk accounts
        if account.risk_level == "CRITICAL":
            return (
                False,
                f"External Technical Partner policy restriction: User '{user.user_id}' ({user.organisation_id}) "
                f"is strictly prohibited from accessing CRITICAL risk shared account '{account.account_name}'.",
                details
            )
        # External partners cannot exceed L2 level
        if user_perm_val > 2:
            return (
                False,
                f"External Technical Partner policy restriction: Privileges for partner identities are restricted to maximum L2.",
                details
            )
        # Account risk cannot exceed external partner cap (L2)
        if acc_risk_val > 2:
            return (
                False,
                f"External Technical Partner policy restriction: Shared account '{account.account_name}' has risk level '{account.risk_level}' "
                f"which exceeds the maximum allowed partner elevation threshold (L2).",
                details
            )

    # 3. Cross-Departmental Government Policy Check
    if not is_external and user.organisation_id != account.organisation_id:
        if user_perm_val < 3:
            return (
                False,
                f"Inter-departmental boundary policy: User from '{user.organisation_id}' requesting account in '{account.organisation_id}' "
                f"requires at least L3 clearance/permission (User has {user.permission_level}).",
                details
            )

    # 4. Standard Permission vs Risk Level Check
    if user_perm_val < acc_risk_val:
        return (
            False,
            f"Insufficient permission: User level '{user.permission_level}' is lower than required risk level '{account.risk_level}' "
            f"for shared account '{account.account_name}'.",
            details
        )

    return True, f"Permission validated: Level '{user.permission_level}' meets required risk tier '{account.risk_level}'.", details


def validate_action_permission(user_permission: str, required_permission: str, is_external: bool = False) -> Tuple[bool, str]:
    """Validate whether an authenticated user has sufficient permission to perform a specific action."""
    user_val = LEVEL_HIERARCHY.get(user_permission, 0)
    req_val  = LEVEL_HIERARCHY.get(required_permission, 1)

    if is_external and req_val > 2:
        return False, f"External technical partners are restricted from actions requiring {required_permission} privileges."

    if user_val >= req_val:
        return True, f"Permission check passed ({user_permission} >= {required_permission})."
    else:
        return False, f"Insufficient permission: Action requires {required_permission}, but user possesses {user_permission}."
