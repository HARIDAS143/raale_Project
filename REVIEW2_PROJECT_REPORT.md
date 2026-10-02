# Shared-Account Elimination Workflow Using Accountable Delegation and Session Attribution

**Project Review**: Review 2  
**Project Milestone Progress**: **70% Total Completion** (Review 1: 35% + Review 2: 35%)  
**Domain**: Cyber Security / Identity & Access Management (IAM) / Enterprise Auditing / Non-Repudiation  

---

## 1. Executive Summary & Abstract

In public sector computing environments, mission-critical operations often depend on legacy enterprise systems that lack granular Role-Based Access Control (RBAC) or modern identity federation (SSO/SAML/OIDC). To maintain operational continuity across departmental agencies and external IT contractors, organisations frequently rely on shared administrative accounts (e.g., `admin_shared`, `operator_shared`, `sysop_shared`). This operational compromise destroys **non-repudiation**: audit trails capture only the generic account moniker rather than the human actor who executed the command.

This project implements an **Accountable Delegation and Session Attribution Framework** that eliminates direct shared credential usage without refactoring legacy software backends. Building upon the foundational 35% baseline established in Review 1, the **Review 2 prototype (70% Completion)** introduces:
1. **Multi-Organisation Access Governance**: Differentiated policies across Government Department A (`ORG001`), Government Department B (`ORG002`), and External Technical Partners (`ORG005`, `ORG006`).
2. **Granular Permission Hierarchy**: Strict backend enforcement of L1 (Basic), L2 (Operational), L3 (Audit/Review), and L4 (Administrative) tiers.
3. **Deterministic Session Attribution Engine**: Cryptographic delegation tokens binding time-bound sessions to individual user identities.
4. **Rule-Based Explanation Layer**: Answers 6 mandatory forensic questions for every privileged action.
5. **Human Fallback Review Queue**: Zero-guessing incident adjudication workflow for conflicting identity telemetry.
6. **Five Realistic Failure Cases**: Comprehensive handling and blocking of missing delegations, insufficient clearances, expired sessions, revoked sessions, and identity telemetry conflicts.
7. **Empirical Dynamic Evaluation**: Automated benchmarking establishing an Individual Attribution Rate (IAR) increase from **0.0% (legacy baseline)** to **83.87% (Review 2 prototype)**, with an effective attribution rate of **85.48%** following human fallback adjudication.
8. **Automated Verification**: 14/14 automated tests passing across all security requirements.

---

## 2. Review 2 System Architecture

```text
                               +----------------------------+
                               |  Individual Human Operator |
                               |   (Synthetic ID: USERxxx)  |
                               +--------------+-------------+
                                              |
                                              v
                               +----------------------------+
                               |     React Web Frontend     |
                               |    (Cyber SOC Interface)   |
                               +--------------+-------------+
                                              |
                                              | REST API / JSON
                                              v
                               +----------------------------+
                               |    FastAPI Backend Core    |
                               +--------------+-------------+
                                              |
                +-----------------------------+-----------------------------+
                |                             |                             |
                v                             v                             v
  +---------------------------+ +---------------------------+ +---------------------------+
  |    Identity Validation    | |    Permission Service     | |    Delegation Service     |
  |  - Active status check    | |  - L1-L4 Level hierarchy  | |  - Token issuance         |
  |  - MFA verification       | |  - Multi-org restrictions | |  - Expiry timestamping    |
  |  - Org boundary check     | |  - External partner cap   | |  - Active session cache   |
  +-------------+-------------+ +-------------+-------------+ +-------------+-------------+
                |                             |                             |
                +-----------------------------+-----------------------------+
                                              |
                                              v
                               +----------------------------+
                               |      Session Manager       |
                               | (Active / Expired / Revoked)|
                               +--------------+-------------+
                                              |
                                              v
                               +----------------------------+
                               | Session Attribution Engine |
                               |  - Token verification      |
                               |  - Temporal validity check |
                               |  - Conflict detection      |
                               +--------------+-------------+
                                              |
                             +----------------+----------------+
                             |                                 |
                             v                                 v
               +---------------------------+     +---------------------------+
               |        ATTRIBUTED         |     |         UNCERTAIN         |
               | (Conclusive Identity Proof)|    |   (Telemetry Conflict)    |
               +-------------+-------------+     +-------------+-------------+
                             |                                 |
                             v                                 v
               +---------------------------+     +---------------------------+
               |     Explanation Layer     |     |   Human Fallback Queue    |
               | - 6 Mandatory Questions   |     | - Auditor adjudication    |
               | - Evidence Checklist      |     | - Synthetic ID: AUDITORxxx|
               +-------------+-------------+     +-------------+-------------+
                             |                                 |
                             +----------------+----------------+
                                              |
                                              v
                               +----------------------------+
                               |   Immutable Audit Trail    |
                               |  (SQLite: shared_workflow) |
                               +--------------+-------------+
                                              |
                                              v
                               +----------------------------+
                               |   Dynamic IAR Benchmark    |
                               | (evaluation_results.json)  |
                               +----------------------------+
```

---

## 3. Granular Permission Hierarchy & Multi-Organisation Policy

### 3.1 Permission Hierarchy (L1 – L4)
The framework enforces four distinct operational permission levels:
* **L1 (Basic)**: Read-only inquiries, directory queries, low-risk informational access (`VIEW_SENSITIVE_RECORD`, `SEARCH_LOG_ENTRIES`).
* **L2 (Operational)**: Standard operational duties, routine transactions, account management (`APPROVE_TRANSACTION`, `CREATE_EMPLOYEE`).
* **L3 (Audit & Review)**: Compliance auditing, security log exports, network maintenance (`EXPORT_REPORT`, `CONFIGURE_VPN`, `BACKUP_DATABASE`).
* **L4 (Administrative)**: System configuration changes, firewall rule manipulation, database schema modification, user termination (`MODIFY_CONFIGURATION`, `MODIFY_FIREWALL_RULE`, `DROP_TABLE`, `TERMINATE_EMPLOYEE`).

### 3.2 Multi-Organisation Governance
Access rules adapt dynamically based on organisation affiliation:
1. **Government Department A (`ORG001`) & Government Department B (`ORG002`)**:
   * Departmental personnel can access shared accounts within their own organisation up to their assigned clearance.
   * Cross-departmental access requires at least L3 clearance.
2. **External Technical Partners (`ORG005`, `ORG006`)**:
   * **Mandatory Privilege Cap**: External partner personnel are restricted to a maximum permission level of **L2**.
   * **Resource Isolation**: External partners are strictly prohibited from accessing **CRITICAL** risk accounts (e.g. `db_admin_shared`, `admin_shared`).
   * Attempts to request or execute L4 actions result in an immediate `PERMISSION_DENIED` status.

---

## 4. The Explanation Layer

A core innovation in Review 2 is the **Deterministic Explanation Layer**. For every privileged action, the system generates a structured explanation answering six fundamental forensic questions:

```json
{
  "attributed_user": "USER012",
  "session_id": "SES-5615",
  "shared_account": {
    "id": "SACC001",
    "name": "admin_shared"
  },
  "permission_evaluation": {
    "user_permission": "L4",
    "required_permission": "L4",
    "passed": true,
    "is_external_partner": false
  },
  "evidence_checklist": [
    "Valid individual identity verified: 'USER012' (ORG001)",
    "Active delegation session 'SES-5615' verified in database",
    "Cryptographic delegation token 'TOK-DEL-568O69BN' active and matched",
    "Permission check passed: User level 'L4' >= Required 'L4'",
    "Session timeframe valid: action executed within active delegation window",
    "Shared account: 'admin_shared' (SACC001)",
    "Organisation boundary satisfied: ORG001"
  ],
  "attribution_status": "ATTRIBUTED",
  "outcome_summary": "Action ACCEPTED and conclusively bound to user 'USER012' based on active delegation token and verified authorization."
}
```

---

## 5. Human Fallback Review Workflow

When telemetry conflicts or ambiguous evidence arises, the attribution engine adheres to the **Principle of Non-Repudiation Integrity: Never Guess Identity**.

```text
Privileged Action Dispatch
          |
          v
Attribution Engine
          |
          +---- Valid, Consistent Evidence ----> ATTRIBUTED (100.0%)
          |
          +---- Telemetry Conflict Detected
                        |
                        v
                 UNCERTAIN Status
                        |
                        v
               Human Review Queue
                        |
                        v
          Forensic Auditor (AUDITOR001)
                        |
               +--------+--------+
               |                 |
               v                 v
           CONFIRMED        UNATTRIBUTED
         (Corroborated)   (Inconclusive)
```

Auditors inspect incident telemetry, evaluate physical badge swipes or supervisor tickets, select synthetic reviewer IDs (`AUDITOR001`, `AUDITOR002`, `AUDITOR003`), and submit a formal justification. The action's audit log entry and evaluation metrics update dynamically upon resolution.

---

## 6. Implementation of Five Realistic Edge & Failure Cases

| Case | Scenario | Technical Mechanism | Expected Outcome |
|---|---|---|---|
| **Case 1** | **Missing Delegation** | An operator attempts to invoke a shared account without providing a session header. | `BLOCKED` / `UNATTRIBUTED`. Explanation notes missing token. |
| **Case 2** | **Insufficient Permission** | An L1 Policy Analyst attempts to execute an L4 `Modify configuration` action. | `PERMISSION_DENIED`. Backend check blocks action before shared system execution. |
| **Case 3** | **Expired Session** | An action is attempted after the session's time-bound expiration timestamp has passed. | `BLOCKED` / `UNATTRIBUTED`. Least-privilege time restriction enforced. |
| **Case 4** | **Invalid / Revoked Session** | An action is attempted with a forged session ID or an administratively revoked session. | `REJECTED` / `BLOCKED`. Security killswitch immediately disables token. |
| **Case 5** | **Conflicting Telemetry** | Session is registered to `USER007`, but incoming client certificate or IP trace asserts `USER009`. | `UNCERTAIN`. Routed to Human Review Queue; zero automated guessing. |

---

## 7. Empirical Evaluation & Benchmark Analysis

### 7.1 Individual Attribution Rate (IAR) Formulation
$$\text{IAR} = \frac{\text{Individually Attributable Sensitive Actions}}{\text{Total Sensitive Actions}} \times 100$$

### 7.2 Benchmark Results (Extracted from `evaluation_results.json`)
The reproducible synthetic experiment compares the 140 baseline logs against 62 prototype privileged actions:

| Metric Indicator | Legacy Baseline System | Review 2 Prototype | Measurable Improvement |
|---|---|---|---|
| **Total Actions Evaluated** | 140 | 62 | — |
| **Sensitive Actions** | 82 | 60 | — |
| **Individually Attributed** | **0** | **52** | **+52 Actions Bound** |
| **Unattributed Actions** | 140 | 4 | **-136 Actions** |
| **Permission Denials Intercepted** | 0 | 5 | Active Least Privilege |
| **Blocked / Expired Actions** | 0 | 0 (Normal) / Dynamic | Time-bound Enforcement |
| **Uncertain (Human Fallback)** | 0 | 1 Pending, 1 Confirmed | Zero Identity Guessing |
| **Overall IAR** | **0.0%** | **83.87%** | **+83.87% Improvement** |
| **Sensitive Action IAR** | **0.0%** | **83.33%** | **+83.33% Improvement** |
| **Effective IAR (with Fallback)** | **0.0%** | **85.48%** | **+85.48% Total Traceability** |

---

## 8. Automated Verification Suite Results

The automated test suite (`backend/test_review2.py`) executes 14 end-to-end tests validating the full Review 2 specification:

```text
======================================================================
  REVIEW 2 AUTOMATED VERIFICATION SUITE — 70% COMPLETION MILESTONE   
======================================================================
  [PASS] Test 01: Valid Delegation Request
  [PASS] Test 02: Invalid Delegation (Unknown Identity)
  [PASS] Test 03: Permission Denial (L1 vs HIGH Account)
  [PASS] Test 04: External Partner Policy Restriction
  [PASS] Test 05: Session Revocation
  [PASS] Test 06: Revoked Session Action Blocked
  [PASS] Test 07: Expired Session Action Blocked
  [PASS] Test 08: Invalid Session Rejection
  [PASS] Test 09: Missing Delegation (Unattributed)
  [PASS] Test 10: Individual Attribution & Explanation Layer
  [PASS] Test 11: Conflicting Identity Evidence -> Human Review Queue
  [PASS] Test 12: Human Review Decision Workflow (CONFIRMED)
  [PASS] Test 13: Evaluation Benchmark Run & Persistence (IAR > 80%)
  [PASS] Test 14: Audit Log Filtering
======================================================================
  VERIFICATION RESULTS:  Passed: 14 / 14  |  Failed: 0
======================================================================
```

---

## 9. Review 2 Live Demonstration Protocol

Evaluators can reproduce the entire Review 2 prototype directly via the web UI in 12 steps:
1. **User Identity Inspection**: Open **Users & Identities** tab; inspect L1-L4 roles and multi-org classifications.
2. **Catalog Legacy Accounts**: Open **Shared Accounts**; filter by risk tier and view accounts flagged for elimination.
3. **Accountable Delegation**: Open **Request Delegation**; select `USER012` and `SACC001`; observe the Pre-Flight Policy Check and issue a 30-minute session.
4. **Active Session Inspection**: Navigate to **Active Sessions**; verify active status and expiration timer.
5. **Privileged Action Execution**: Open **Action Simulator**; execute `Modify configuration`.
6. **Individual Attribution**: Observe instant attribution to `USER012` with 100.0% confidence.
7. **Forensic Explanation Inspection**: Open **Audit Log & Evidence**; click `🔍 View Explanation` to inspect the 6-question checklist.
8. **Failure Case 1 (Missing Delegation)**: In simulator, click `🔴 Edge Case 1`; verify action is blocked as unattributed.
9. **Failure Case 2 (Insufficient Permission)**: Click `🔴 Edge Case 2`; verify L1 user attempting L4 action is denied.
10. **Failure Case 5 (Conflicting Evidence)**: Click `⚖️ Edge Case 5`; verify action is marked `UNCERTAIN` and dispatched to Human Review Queue.
11. **Human Fallback Adjudication**: Switch to **Human Review Queue**; adjudicate the case as `AUDITOR001` with justification. Confirm status changes to `CONFIRMED`.
12. **Session Revocation & Benchmark Verification**: In **Active Sessions**, revoke a live session; confirm subsequent actions fail. Open **Evaluation Benchmarks** and verify dynamic IAR calculation.

---

## 10. Summary of Deliverables & Project Progress

```text
+-----------------------------------------------------------------------------------+
|                           PROJECT PROGRESSION SUMMARY                             |
+------------------------------------+----------------------------------------------+
| REVIEW 1 MILESTONE (35% COMPLETED) | * Scenario modeling & problem definition     |
|                                    | * Synthetic datasets (Users, Accounts, Logs) |
|                                    | * Legacy baseline evaluation (0% IAR)        |
|                                    | * Initial FastAPI + React + SQLite scaffold  |
+------------------------------------+----------------------------------------------+
| REVIEW 2 MILESTONE (35% DEVELOPED) | * Granular L1-L4 Permission Service          |
|                                    | * Multi-Organisation Policy Framework       |
|                                    | * Deterministic Session Attribution Engine   |
|                                    | * Rule-Based Explanation Layer (6 questions) |
|                                    | * Human Fallback Review Queue & Adjudication |
|                                    | * 5 Realistic Edge & Failure Case Handlers   |
|                                    | * Session Revocation & Expiration Killswitch |
|                                    | * Dynamic Empirical Benchmarks (>83% IAR)    |
|                                    | * Automated Test Suite (14/14 Passed)        |
+------------------------------------+----------------------------------------------+
| TOTAL CURRENT COMPLETION           |                  70% TOTAL                   |
+------------------------------------+----------------------------------------------+
| REMAINING FOR REVIEW 3 (100% GOAL) | * Dynamic heuristic anomaly scoring          |
|                                    | * Enterprise SIEM connectors (Splunk/Elastic)|
|                                    | * Continuous in-session risk reassessment    |
|                                    | * Multi-factor biometric step-up integration |
+------------------------------------+----------------------------------------------+
```
