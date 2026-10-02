# Shared-Account Elimination Workflow Using Accountable Delegation and Session Attribution
## Review 2 Prototype — 70% Completion Milestone

**Domain**: Cyber Security / Identity & Access Management (IAM) / Enterprise Auditing  
**Progress**: Review 1 (35%) + Review 2 (35%) = **70% Total Project Completion**  
**Architecture**: React (Frontend) + FastAPI (Backend) + SQLite (Database)

---

## 1. Project Overview

In public sector and enterprise IT environments, legacy applications frequently rely on shared system monikers (e.g., `admin_shared`, `operator_shared`, `sysop_shared`) to perform administrative maintenance. When multiple operators share credentials, audit logs capture only the shared moniker. Consequently, non-repudiation is completely lost, forensics are obscured, and compliance standards (NIST SP 800-53, ISO 27001) are violated.

This project delivers an **Accountable Delegation and Deterministic Session Attribution Framework** that eliminates direct shared-account access without requiring high-risk source code modifications to legacy systems. Individual operators authenticate their personal identity, undergo multi-organisation permission checks, receive time-bound cryptographic delegation tokens bound to dedicated sessions, and execute privileged operations with deterministic individual attribution, an Explanation Layer, and a Human Fallback Review queue.

---

## 2. Problem Statement

Legacy public sector systems present critical vulnerabilities:
1. **Absence of Non-Repudiation**: Privileged actions are logged under shared monikers; individual operators cannot be identified.
2. **Coarse Privilege Inheritance**: All operators sharing a credential inherit maximum privileges (violating Least Privilege).
3. **Zero Killswitch Granularity**: Revoking an individual operator requires resetting credentials for all shared users.
4. **Ambiguous Telemetry**: Audit logs lack context, preventing forensic reconstruction of incidents.

---

## 3. Review 2 Target Architecture

```text
                    USER (Individual Identity)
                               |
                               v
                     React Web Frontend
                               |
                               v
                      FastAPI Backend API
                               |
        +----------------------+----------------------+
        |                      |                      |
        v                      v                      v
 Identity Validation   Permission Service    Delegation Service
 (Clearance/MFA/Org)   (L1-L4 Hierarchy)     (Token/Time-bound)
        |                      |                      |
        +----------------------+----------------------+
                               |
                               v
                        Session Manager
                    (Active / Expiry / Revoke)
                               |
                               v
                   Session Attribution Engine
                               |
                +--------------+--------------+
                |                             |
                v                             v
           ATTRIBUTED                     UNCERTAIN
         (Valid Evidence)             (Telemetry Conflict)
                |                             |
                v                             v
        Explanation Layer            Human Fallback Review
    (6 Mandatory Questions)           (Auditor Adjudication)
                |                             |
                +--------------+--------------+
                               |
                               v
                      Immutable Audit Log
                               |
                               v
                    Empirical Evaluation
                   (Dynamic IAR Calculation)
```

---

## 4. Technology Stack

* **Frontend**: React 18, Babel standalone, Chart.js, Vanilla CSS Design System (no Node build step required; open in any browser).
* **Backend**: Python 3.11, FastAPI 0.115, Starlette, Uvicorn ASGI server, Pydantic v2.
* **Database & ORM**: SQLite (`backend/shared_workflow.db`), SQLAlchemy 2.0 ORM.
* **Automated Testing**: Pytest, FastAPI TestClient, Urllib verification suite.
* **Evaluation Data**: Structured JSON persistence (`backend/evaluation_results.json`).

---

## 5. Synthetic Dataset Description

The system operates strictly on synthetic, privacy-preserving datasets stored in `backend/data/`:
1. `users.csv` (20 synthetic identities): Government Department A (`ORG001`), Government Department B (`ORG002`), Government Department C (`ORG003`), Independent Auditors (`ORG004`), External Technical Partners (`ORG005`, `ORG006`).
2. `shared_accounts.csv` (8 legacy accounts): `admin_shared`, `operator_shared`, `legacy_admin`, `sysop_shared`, `db_admin_shared`, `hr_shared`, `procurement_shared`, `audit_viewer`.
3. `system_logs.csv` (140 baseline logs): Legacy operational logs where individual identification is 0.0%.
4. `privileged_actions.csv` (60 prototype records): Privileged action execution records with attribution tags, evidence strings, and scenario categories.

---

## 6. Setup & Execution Instructions

### Prerequisites
* Python 3.10+ (tested on Python 3.11.9)
* Any modern web browser (Edge, Chrome, Firefox)

### Step 1: Install Python Dependencies
```powershell
cd backend
pip install -r requirements.txt
```

### Step 2: Start the FastAPI Backend Server
```powershell
cd backend
python -m uvicorn main:app --port 8001 --host 127.0.0.1 --reload
```
* **API URL**: http://127.0.0.1:8001
* **Interactive OpenAPI Swagger Docs**: http://127.0.0.1:8001/docs
* **Database initialization**: Tables are verified and seeded automatically upon startup.

### Step 3: Launch the Frontend Interface
Open `frontend/index.html` directly in any web browser, or via simple HTTP server:
```powershell
# Directly double-click frontend/index.html in Windows Explorer
# OR launch via python:
cd frontend
python -m http.server 3000
```
Then visit: http://localhost:3000 (or `file:///.../frontend/index.html`).  
The UI automatically detects whether the backend is listening on port 8001 or 8000.

---

## 7. Granular Permission Levels & Multi-Organisation Policy

### Permission Levels
* **L1 — Basic**: Read-only inquiries and low-risk operational lookups.
* **L2 — Operational**: Standard operational duties, transaction approvals, routine maintenance.
* **L3 — Audit / Review**: Compliance inspection, audit log exports, backup procedures.
* **L4 — Administrative**: High-risk system configuration changes, access management, database table drops.

### Multi-Organisation Policies
1. **Government Department A & B (`ORG001`, `ORG002`)**: Standard departmental authorization up to user's assigned clearance.
2. **Cross-Departmental Requests**: Inter-departmental access requires at least L3 clearance/permission.
3. **External Technical Partners (`ORG005`, `ORG006`)**:
   * Privilege cap: Strictly limited to maximum **L2**.
   * Restricted Resources: Prohibited from requesting **CRITICAL** risk accounts (e.g. `db_admin_shared`, `admin_shared`).

---

## 8. Explanation Layer

For every action, the Explanation Layer answers 6 mandatory forensic questions:
1. **Who was attributed?** (e.g. `USER012`)
2. **Which session was used?** (e.g. `SES-5615`)
3. **Which shared account was involved?** (e.g. `admin_shared` / `SACC001`)
4. **What permission was checked?** (e.g. User `L4` >= Required `L4`)
5. **What evidence supported attribution?** (Valid token, active timeframe, session binding, MFA verification)
6. **Why was the action accepted or rejected?** (Explicit deterministic rationale)

---

## 9. Realistic Edge & Failure Cases (Part 5)

| Edge Case | Description | Expected Outcome | Trigger in UI |
|---|---|---|---|
| **Edge Case 1 — Missing Delegation** | Action attempted directly on shared account without delegation token | Action: `BLOCKED`<br>Attribution: `UNATTRIBUTED`<br>Reason: `No active delegation` | Simulator: 🔴 Edge Case 1 |
| **Edge Case 2 — Insufficient Permission** | L1 user attempts high-risk administrative action (L4) | Access: `PERMISSION_DENIED`<br>Reason: `User level L1 < Required L4` | Simulator: 🔴 Edge Case 2 |
| **Edge Case 3 — Expired Session** | Valid session reaches end_time before action execution | Action: `BLOCKED`<br>Attribution: `UNATTRIBUTED`<br>Reason: `Session expired` | Simulator: 🔴 Edge Case 3 |
| **Edge Case 4 — Invalid Session** | Request contains non-existent or forged session ID | Action: `REJECTED`<br>Reason: `Invalid session ID` | Simulator: 🔴 Edge Case 4 |
| **Edge Case 5 — Conflicting Evidence** | Session belongs to `USER007`, but log telemetry claims `USER009` | Attribution: `UNCERTAIN`<br>Fallback: `Enqueued to Human Review Queue` | Simulator: ⚖️ Edge Case 5 |
| **Partner Policy Restriction** | External vendor contractor attempts administrative L4 action | Access: `PERMISSION_DENIED`<br>Reason: `External partner capped at L2` | Simulator: 🔵 Partner Restriction |

---

## 10. Human Fallback Review Workflow (Part 4)

When identity evidence conflicts or is ambiguous, the attribution engine refuses to guess:
```text
Uncertain Action -> Human Review Queue -> Security Auditor Review (AUDITOR001)
                                      -> Decisions:
                                           ├── CONFIRMED: Attributed with corroboration
                                           └── UNATTRIBUTED: Ruled inconclusive
```
Auditors can inspect evidence, review telemetry conflicts, select synthetic reviewer IDs (`AUDITOR001`, `AUDITOR002`, `AUDITOR003`), provide justifications, and resolve incidents directly through the UI.

---

## 11. Automated Test Suite (Part 18)

Run the automated test suite verifying all 14 core requirements:
```powershell
cd backend
python test_review2.py
```

### Test Suite Execution Output:
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

To run Review 1 backwards compatibility verification:
```powershell
python test_phase4.py
```

---

## 12. Dynamic Evaluation & Success Metric (Part 13 & 15)

### Individual Attribution Rate (IAR) Formula:
$$\text{IAR} = \frac{\text{Individually Attributable Sensitive Actions}}{\text{Total Sensitive Actions}} \times 100$$

### Empirical Benchmark Findings (from `evaluation_results.json`):
* **Baseline IAR (Legacy Shared Accounts)**: **0.0%** (140 logs, 0 individuals identified)
* **Prototype IAR (Review 2)**: **83.87%** (Sensitive IAR: **83.33%**)
* **Effective Attribution (with Human Fallback)**: **85.48%**
* **Attribution Improvement**: **+83.87%** over legacy baseline

Results can be dynamically re-evaluated from database evidence at any time via `POST /evaluation/run` or via the **Evaluation Benchmarks** tab in the UI.

---

## 13. Review 2 Live Demonstration Workflow (Part 21)

Follow this 12-step script during the live Review 2 demonstration:
1. **Step 1 — Login / Select User**: Navigate to **Users & Identities**; select `USER012` (L4 Security Admin, `ORG001`).
2. **Step 2 — Select Organisation**: Filter by `ORG001` (Gov Dept A) and observe external partner restrictions for `ORG005`.
3. **Step 3 — Request Shared Account Access**: Open **Request Delegation**; select `SACC001` (`admin_shared`, LegacyERP).
4. **Step 4 — Show Permission Validation**: Observe the live Pre-Flight Policy Check confirming `L4 >= HIGH`.
5. **Step 5 — Create Delegation Session**: Click **Validate & Issue Session**; note generated session ID (`SES-xxxx`) and token (`TOK-DEL-xxxx`).
6. **Step 6 — Verify Active Session**: Switch to **Active Sessions**; verify live status and expiration timestamp.
7. **Step 7 — Perform Sensitive Action**: Open **Action Simulator**; execute `Modify configuration` under the active session.
8. **Step 8 — Show Individual Attribution**: Confirm instant attribution status: `✓ ATTRIBUTED (100.0%)` to `USER012`.
9. **Step 9 — Show Explanation Layer**: Open **Audit Log & Evidence**; click `🔍 View Explanation` to display the 6-question forensic evidence checklist.
10. **Step 10 — Run Failure Cases**: Return to simulator; trigger **🔴 Missing Delegation**, **🔴 Insufficient Permission**, and **🔴 Expired Session**. Show immediate blocking.
11. **Step 11 — Trigger Conflict & Fallback**: Click **⚖️ Conflicting Evidence**; observe routing to **Human Review Queue**; submit an adjudication decision as `AUDITOR001`.
12. **Step 12 — Review Dynamic Evaluation**: Open **Evaluation Benchmarks**; click **Re-run Benchmark Evaluation** to show real-time dynamic IAR generation.

---

## 14. Responsible AI & Privacy Considerations

* **Synthetic Data Only**: All user IDs (`USER001`-`USER020`), organisation IDs, session IDs, and reviewer monikers (`AUDITOR001`) are synthetic. No PII is stored.
* **Deterministic Attribution**: Attribution relies on verifiable cryptographic delegation bindings and audit logs, not opaque machine learning guesses.
* **Zero Guessing Fallback**: Ambiguous telemetry is explicitly isolated in the Human Review Queue.

---

## 15. Review Status & Remaining Work (Target: 100%)

### Project Completion Breakdown
* **Review 1 Milestone**: **35%** (Datasets, legacy baseline, initial FastAPI + React scaffold)
* **Review 2 Milestone Work**: **35%** (Granular permissions, multi-org policies, explanation layer, human fallback queue, 5 failure cases, session revocation, dynamic evaluation, automated test suite)
* **Total Current Progress**: **70%**

### Remaining Work for Final Review 3 (100% Target)
1. Dynamic behavioral anomaly detection using adaptive heuristic scoring.
2. Enterprise SIEM integration connectors (Splunk / Elastic Common Schema).
3. Automated continuous session risk scoring during active delegation.
4. Comprehensive multi-factor biometric step-up authentication integration.
