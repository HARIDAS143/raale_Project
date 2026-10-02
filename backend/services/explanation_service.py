"""
services/explanation_service.py — Deterministic rule-based Explanation Layer
generating structured forensic evidence and non-repudiation rationales.
"""

from typing import Dict, Any, List, Optional
import json


def build_explanation(
    action_type: str,
    attributed_user_id: str,
    session_id: Optional[str],
    shared_account_id: str,
    shared_account_name: str,
    user_permission: str,
    required_permission: str,
    attribution_status: str,
    status_reason: str,
    evidence_items: List[str],
    is_external: bool = False,
    conflict_details: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs an immutable, structured explanation answering the 6 mandatory questions:
    1. Who was attributed?
    2. Which session was used?
    3. Which shared account was involved?
    4. What permission was checked?
    5. What evidence supported attribution?
    6. Why was the action accepted or rejected?
    """

    # Determine acceptance/rejection summary
    if attribution_status == "ATTRIBUTED":
        outcome_summary = f"Action ACCEPTED and conclusively bound to user '{attributed_user_id}' based on active delegation token and verified authorization."
    elif attribution_status == "PERMISSION_DENIED":
        outcome_summary = f"Action REJECTED due to insufficient permission level ({user_permission} possessed vs {required_permission} required)."
    elif attribution_status == "BLOCKED":
        outcome_summary = f"Action BLOCKED: {status_reason}."
    elif attribution_status == "UNCERTAIN":
        outcome_summary = f"Attribution UNCERTAIN: Conflicting or ambiguous identity evidence detected. Action routed to Human Fallback Review queue."
    else:
        outcome_summary = f"Action processed with status '{attribution_status}': {status_reason}."

    # Format human-readable text block
    text_lines = [
        f"Action: {action_type}",
        f"Attributed User: {attributed_user_id}",
        f"Session ID: {session_id or 'NONE'}",
        f"Shared Account: {shared_account_name} ({shared_account_id})",
        f"Permission Check: User [{user_permission}] vs Required [{required_permission}]",
        f"Attribution Status: {attribution_status}",
        "",
        "Forensic Evidence Checklist:",
    ]
    for item in evidence_items:
        text_lines.append(f"  • {item}")

    if conflict_details:
        text_lines.append(f"\n⚠️ Conflict / Fallback Note: {conflict_details}")

    text_lines.append(f"\nOutcome: {outcome_summary}")
    formatted_text = "\n".join(text_lines)

    return {
        "attributed_user": attributed_user_id,
        "session_id": session_id or "NONE",
        "shared_account": {
            "id": shared_account_id,
            "name": shared_account_name
        },
        "permission_evaluation": {
            "user_permission": user_permission,
            "required_permission": required_permission,
            "passed": user_permission >= required_permission if user_permission and required_permission else False,
            "is_external_partner": is_external
        },
        "evidence_checklist": evidence_items,
        "conflict_details": conflict_details,
        "attribution_status": attribution_status,
        "status_reason": status_reason,
        "outcome_summary": outcome_summary,
        "formatted_text": formatted_text
    }


def serialize_explanation(explanation_dict: Dict[str, Any]) -> str:
    """Serializes explanation dictionary to JSON string for database persistence."""
    try:
        return json.dumps(explanation_dict, ensure_ascii=False)
    except Exception:
        return str(explanation_dict)
