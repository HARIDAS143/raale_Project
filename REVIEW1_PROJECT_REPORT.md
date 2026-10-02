# Shared-Account Elimination Workflow Using Accountable Delegation and Session Attribution

**Project Review**: Review 1  
**Project Milestone Progress**: 35%  
**Domain**: Network Security / Identity and Access Management (IAM) / Cyber Auditing  

---

## 1. Abstract

In government departments and public sector enterprise environments, legacy applications often rely on shared system accounts—such as `admin_shared`, `operator_shared`, or `legacy_admin`—to execute administrative and operational tasks. When multiple personnel share credentials to access these legacy systems, audit trails capture only the shared account moniker rather than the individual human operator. This structural deficiency eliminates individual accountability, obscures forensic investigations, and complicates compliance auditing during security incidents.

To address this critical security vulnerability, this project introduces a **Shared-Account Elimination Workflow using Accountable Delegation and Session Attribution**. The proposed framework replaces direct shared credential usage with a dynamic delegation protocol. An individual user authenticates their personal identity, undergoes permission validation against target resource risk levels, and receives a time-bound delegation token bound to a uniquely created session. All subsequent sensitive actions are deterministically attributed to the authenticated individual operator.

For **Review 1 (35% Progress)**, the project scope encompasses: (1) scenario definition and threat modeling for a multi-organisation public sector environment, (2) synthetic dataset design covering user rosters, shared credentials, baseline system logs, and privileged action traces, (3) a legacy baseline evaluation model demonstrating an Individual Attribution Rate (IAR) of 0.0%, (4) a full-stack baseline prototype built with Python FastAPI, React, and SQLite, and (5) preliminary deterministic session attribution logic. Advanced features—such as machine-learning anomaly detection, natural language explanation layers, and human-in-the-loop fallback review workflows—are reserved for subsequent project phases.

---

## 2. Introduction

Public sector digital infrastructure frequently spans decades of technology deployment. While core databases and enterprise portals are regularly modernized, numerous critical operations continue to rely on legacy applications that lack granular Role-Based Access Control (RBAC) or modern Single Sign-On (SSO) integration. To maintain operational continuity across inter-departmental workflows and external partner collaborations, organisations resort to shared account credentials.

Shared accounts permit multiple employees, contractors, or system administrators to log into a system under a single identity. While this practice bypasses legacy authentication barriers, it introduces a severe systemic risk: **loss of non-repudiation**. In cybersecurity, non-repudiation ensures that an action performed on an information system can be conclusively traced to the specific individual who authorized or executed it.

When a sensitive action—such as updating a citizen financial record, modifying a system security configuration, approving a high-value transaction, or exporting confidential data—is logged under a shared account, traditional audit logs record only that the shared account performed the action. Security Operations Center (SOC) analysts and forensic auditors cannot determine which specific employee held control of the session at that exact timestamp.

Eliminating reliance on shared accounts without rewriting legacy source code requires an intermediary governance layer. This project proposes an **Accountable Delegation and Session Attribution** mechanism. By intercepting access requests, validating individual authorization, and maintaining a deterministic token-to-session mapping, the framework restores complete individual accountability while preserving legacy application functionality.

---

## 3. Problem Statement

A government department operates multiple legacy applications with inconsistent identity records and minimal individual authorization controls. Multiple internal personnel and external partner contractors access sensitive enterprise applications through shared accounts (e.g., `admin_shared`, `operator_shared`, `legacy_admin`). Consequently, when a sensitive or privileged action is executed within the system, audit records identify only the shared account name, making it impossible to attribute the action to a specific individual human identity.

### Consequences of this Problem:

1. **Absence of Non-Repudiation**: Insiders can execute unauthorized or malicious actions under the cover of shared credentials without direct accountability.
2. **Impaired Forensic Investigation**: During security incidents or data breach reviews, security analysts cannot isolate the compromised user account or differentiate between authorized operational duty and insider threats.
3. **Regulatory Non-Compliance**: Public sector systems fail to satisfy mandatory cybersecurity audit frameworks (e.g., NIST SP 800-53, ISO/IEC 27001, CIS Controls), which explicitly mandate individual identity attribution for privileged operations.
4. **Coarse Access Control**: All users sharing a legacy account inherit the maximum privilege level of that account, violating the Principle of Least Privilege.

---

## 4. Motivation

The motivation behind this project stems from real-world challenges faced by enterprise security teams in public sector and critical infrastructure environments:

* **Restoring Individual Accountability**: Guaranteeing that every privileged command can be linked back to a verifiable person, discouraging policy violations and insider misuse.
* **Streamlining Audit Operations**: Transforming ambiguous system logs into clear, actionable audit trails that simplify compliance reporting and incident response.
* **Overcoming Legacy Constraints**: Modernizing identity governance without requiring expensive, high-risk refactoring or replacement of legacy software backends.
* **Enforcing Least Privilege & Just-in-Time Access**: Restricting shared resource elevation through permission-checked delegation sessions rather than permanent credential distribution.
* **Responsible Identity Management**: Implementing identity attribution using privacy-preserving, synthetic identifiers to eliminate unnecessary collection or exposure of Personally Identifiable Information (PII).

---

## 5. Objectives

The primary objectives of this project are structured as follows:

1. **Identify Shared Accounts**: Catalog and structure legacy shared credentials across target departmental applications and risk tiers.
2. **Introduce Accountable Delegation**: Design an authorization workflow where users request time-bound delegation tokens bound to their individual identity before accessing shared resources.
3. **Create Individual Session Attribution**: Establish a deterministic binding between an individual user, a delegation session, and the shared account.
4. **Record Sensitive Actions**: Capture privileged operations (e.g., viewing sensitive records, configuration changes, transaction approvals, data exports) alongside contextual evidence.
5. **Improve Individual Attribution Percentage**: Demonstrate a measurable increase in the Individual Attribution Rate (IAR) from 0.0% (baseline) to over 80% (prototype).
6. **Establish Baseline Comparison**: Implement a simple legacy baseline script to empirically measure attribution deficits in un-delegated environments.
7. **Minimize Unnecessary Personal Data Collection**: Design the identity layer to operate strictly on synthetic identifiers and minimum required operational metadata.
8. **Provide a Scalable Foundation**: Establish a modular architecture that supports future extensions, including automated anomaly detection, natural language explanations, and human review fallback workflows.

---

## 6. Scope

To ensure clear project boundaries and realistic execution for **Review 1**, the scope is divided into completed deliverables and planned future development.

```
+-------------------------------------------------------+-------------------------------------------------------+
|              REVIEW 1 SCOPE (COMPLETED / 35%)         |               FUTURE WORK (PHASES 5-8)                |
+-------------------------------------------------------+-------------------------------------------------------+
| * Multi-organisation scenario definition              | * Machine learning anomaly detection & risk scoring   |
| * Synthetic dataset design & generation (4 CSVs)      | * Natural language explanation layer                  |
| * Legacy baseline evaluation model (0.0% IAR)         | * Human-in-the-loop fallback review workflow          |
| * Core 9-step accountable delegation workflow         | * Advanced edge-case handling & stress testing        |
| * FastAPI + SQLite backend API server                 | * Comprehensive stakeholder usability validation      |
| * React SPA frontend dashboard (7 interactive pages)   | * Production deployment & hardening checklist         |
| * Deterministic session attribution engine            | * Final comparative evaluation report                 |
+-------------------------------------------------------+-------------------------------------------------------+
```

---

## 7. Scenario Definition

The operational scenario models a representative government environment involving multi-agency coordination and shared system access.

```
               +---------------------------------------------------+
               |            ORGANISATIONAL DOMAIN                  |
               +---------------------------------------------------+
               |  * Government Department A (GovDeptA)             |
               |  * Government Department B (GovDeptB)             |
               |  * External Technical Partner (ExtPartner)        |
               +-------------------------+-------------------------+
                                         |
                                         v
               +---------------------------------------------------+
               |               USER ROLES & CLEARANCES             |
               +---------------------------------------------------+
               |  * Policy Analyst / Officer   (Level L1)          |
               |  * Finance / Revenue Inspector (Level L2)         |
               |  * Internal Auditor / Reviewer(Level L3)          |
               |  * Security Admin / IAM Eng.  (Level L4)          |
               +-------------------------+-------------------------+
                                         |
                                         v
               +---------------------------------------------------+
               |             LEGACY APPLICATIONS & ACCOUNTS        |
               +---------------------------------------------------+
               |  * Customs & Revenue Portal (AppID: APP001)        |
               |    Shared Account: admin_shared (Risk: HIGH)     |
               |  * Citizen Identity Registry (AppID: APP002)       |
               |    Shared Account: legacy_admin (Risk: CRITICAL)  |
               |  * Inter-Agency Logistics System (AppID: APP003)   |
               |    Shared Account: operator_shared (Risk: MEDIUM) |
               +---------------------------------------------------+
```

### Current Operational Challenge
Multiple personnel across Department A, Department B, and External Partner contractors utilize identical `admin_shared` or `operator_shared` credentials to log into `APP001` and `APP003`. When an unauthorized data export occurs, security logs reveal only `admin_shared` as the actor, preventing internal investigation.

---

## 8. Existing System / Baseline

In the existing legacy workflow, users log directly into legacy applications using shared credentials.

### Baseline Workflow Diagram
```
 [ User ]  --->  [ Shared Account Login ]  --->  [ Legacy Application ]  --->  [ Sensitive Action ]
                                                                                      |
                                                                                      v
 [ Unattributed Log Entry ]  <---  [ System Log: Actor = "Shared Account" ] <---------+
```

### Baseline Deficiencies
1. **No Individual Linkage**: System logs capture `session_id`, `shared_account_id`, `timestamp`, `action`, and `device_id`, but contain **zero identity evidence** linking to an individual person.
2. **Deficit Metric**: All sensitive actions are recorded under the shared account name, resulting in complete attribution failure.

### Baseline Evaluation Metric: Individual Attribution Rate (IAR)
To quantify individual accountability, the project defines the **Individual Attribution Rate (IAR)**:

$$\text{IAR} = \left( \frac{\text{Individually Attributable Sensitive Actions}}{\text{Total Sensitive Actions}} \right) \times 100$$

In the baseline legacy environment:

$$\text{Baseline IAR} = \frac{0}{N} \times 100 = 0.0\%$$

---

## 9. Proposed Solution

The proposed framework introduces an intermediary **Accountable Delegation and Session Attribution** mechanism that governs access to shared accounts without altering legacy application code.

### Proposed 9-Step End-to-End Workflow

```
 (1) User Selects Identity
        │
        v
 (2) Request Shared Account Access
        │
        v
 (3) System Checks Permission Level (L1-L4 vs Risk Tier)
        │
        ├──[ Denied (Permission Level < Risk Tier) ]──> (Access Rejected)
        │
        └──[ Granted (Permission Level >= Risk Tier) ]
                │
                v
         (4) System Creates Delegation Session & Generates Token (DEL-XXXX)
                │
                v
         (5) Session Bound to Authenticated Individual User ID
                │
                v
         (6) User Performs Sensitive Action (View, Modify, Approve, Export)
                │
                v
         (7) System Records Action Metadata & Timestamp
                │
                v
         (8) Session Attribution Engine Resolves Token -> Individual User ID
                │
                v
         (9) Immutable Audit Record Created (User ID + Session + Action)
```

---

## 10. System Architecture

The architecture consists of a multi-tier structure bridging frontend presentation, API routing, business logic, session tokenization, and persistent database storage.

### Text-Based System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                  FRONTEND LAYER                                   |
|   React SPA (Single Page Application) - Vanilla CSS, Chart.js, HTML5 Component UI |
|                                                                                   |
|  [ Dashboard ]  [ Users ]  [ Shared Accounts ]  [ Delegation ]                    |
|  [ Active Sessions ]  [ Privileged Actions ]    [ Audit Log ]                     |
+------------------------------------------+----------------------------------------+
                                           |  HTTP / REST JSON APIs
                                           v
+-----------------------------------------------------------------------------------+
|                             BACKEND FASTAPI APPLICATION                           |
|                                                                                   |
|  +-----------------------+  +------------------------+  +----------------------+  |
|  |   routers/users.py    |  | routers/shared_accs.py |  | routers/dashboard.py |  |
|  +-----------------------+  +------------------------+  +----------------------+  |
|  |  routers/sessions.py  |  |   routers/actions.py   |  |     schemas.py       |  |
|  +-----------------------+  +------------------------+  +----------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                        BUSINESS LOGIC ENGINE                                |  |
|  |  * Permission Validator  (User Clearance L1-L4 vs Account Risk Level)       |  |
|  |  * Token Generator       (Crypto-random Token DEL-XXXX & Session SES-XXXX)  |  |
|  |  * Session Attribution   (Deterministic Token-to-User Resolution)          |  |
|  +-----------------------------------------------------------------------------+  |
+------------------------------------------+----------------------------------------+
                                           |  SQLAlchemy ORM
                                           v
+-----------------------------------------------------------------------------------+
|                                 DATABASE LAYER                                    |
|   SQLite Database (shared_workflow.db)                                            |
|   Tables: users | shared_accounts | delegation_sessions | privileged_actions    |
+-----------------------------------------------------------------------------------+
```

---

## 11. Data Design

The system relies on four structured, synthetic datasets designed to replicate realistic government operations while eliminating PII exposure.

```
                      +-----------------------------+
                      |         users.csv           |
                      |  (User Identity Roster)     |
                      +--------------+--------------+
                                     | 1
                                     |
                                     | N (Bound User)
                      +--------------v--------------+
                      |   delegation_sessions.csv   |
                      |  (Token & Session Binds)    |
                      +--------------+--------------+
                                     | 1
                                     |
                                     | N (Attributed Actions)
                      +--------------v--------------+
                      |   privileged_actions.csv    |
                      |  (Prototype Action Logs)    |
                      +-----------------------------+
                                     ^
                                     | N
                                     | 1 (Shared Account FK)
                      +--------------+--------------+
                      |    shared_accounts.csv      |
                      | (Shared Account Inventory)  |
                      +-----------------------------+
```

### Dataset Specifications

#### 1. `shared_credentials_inventory.csv` (`shared_accounts.csv`)
* **Fields**: `shared_account_id`, `account_name`, `application_id`, `application_name`, `organisation_id`, `account_type`, `risk_level`, `known_users_count`, `requires_delegation`, `status`, `created_date`.
* **Description**: Catalogs legacy shared accounts across departments.

#### 2. `user_roster.csv` (`users.csv`)
* **Fields**: `user_id`, `organisation_id`, `user_type`, `role`, `permission_level`, `clearance_level`, `account_type`, `mfa_enrolled`, `active_status`, `created_date`.
* **Description**: Maintains individual synthetic user profiles and clearance levels.

#### 3. `system_logs.csv`
* **Fields**: `log_id`, `timestamp`, `session_id`, `shared_account_id`, `application`, `action`, `organisation_id`, `device_id`, `identity_evidence`, `log_status`, `individual_identified`, `sensitivity`.
* **Description**: Captures baseline legacy logs where `individual_identified` is uniformly set to `NO`.

#### 4. `privileged_actions.csv`
* **Fields**: `action_id`, `timestamp`, `session_id`, `shared_account_id`, `organisation_id`, `application`, `action_type`, `sensitivity`, `required_permission`, `user_permission`, `delegation_token`, `attributed_user_id`, `attribution_status`, `attribution_confidence`, `identity_evidence`, `justification`.
* **Description**: Records prototype operations with deterministic attribution status (`ATTRIBUTED` vs `UNATTRIBUTED`).

---

## 12. Privacy and Responsible AI

### Responsible Identity Handling
1. **Synthetic Identities Only**: All user IDs (`USER001`–`USER020`), organisation IDs (`ORG01`–`ORG06`), and shared account IDs (`SACC001`–`SACC008`) are entirely synthetic. No real employee names, email addresses, phone numbers, or government national IDs are collected or stored.
2. **Data Minimization**: The delegation engine processes only the operational metadata necessary to bind sessions and validate clearance (`user_id`, `permission_level`, `shared_account_id`).
3. **Transparent Non-Repudiation**: System actions explicitly record attribution status (`ATTRIBUTED` or `UNATTRIBUTED`) rather than producing silent fallback guesses.

### Risk Analysis & Mitigation

| Risk Vector | Impact | Mitigation Strategy |
|-------------|--------|---------------------|
| **Incorrect Session Attribution** | High | Enforce single-user session binding and crypto-random delegation tokens (`DEL-XXXX`). |
| **Excessive Operator Monitoring** | Medium | Limit audit logging strictly to designated privileged/sensitive actions. |
| **Permission Bypass Attempts** | High | Implement server-side permission validation before issuing delegation tokens. |
| **False Confidence in Logs** | Medium | Maintain explicit `attribution_confidence` fields and audit log flags. |

---

## 13. Technology Stack

The prototype uses a lightweight, robust, student-friendly technology stack:

* **Frontend Framework**: **React 18** (Single Page Application architecture for dynamic UI components).
* **Styling & UI**: **Vanilla CSS3** (Custom design system with dark-mode color tokens, CSS grid/flexbox layouts).
* **Backend API Framework**: **Python FastAPI** (Asynchronous, high-performance REST API with automatic Pydantic data validation).
* **Database Management System**: **SQLite 3** via **SQLAlchemy ORM** (Lightweight, serverless relational database).
* **Visualization Engine**: **Chart.js 4.4** (Client-side HTML5 canvas charts for donut metrics and severity distribution).
* **Development Environment**: **Visual Studio Code** on Windows OS.

### Rationale
This stack provides seamless setup, zero external database server dependencies, rapid API execution, and clean separation of concerns between presentation and security logic.

---

## 14. Review 1 Progress Summary

The following table summarizes the implementation status across project components for **Review 1 (35% Milestone)**:

| Project Component | Review 1 Status | Deliverable Artifact / File |
|-------------------|-----------------|-----------------------------|
| **Scenario Definition** | ✅ Completed | Multi-dept scenario specification |
| **Problem Analysis** | ✅ Completed | Problem statement & threat model |
| **Dataset Design** | ✅ Completed | 4 Synthetic CSV datasets (`data/*.csv`) |
| **Baseline Evaluation** | ✅ Completed | `baseline_evaluation.py` (0.0% Baseline IAR) |
| **Workflow Design** | ✅ Completed | 9-Step Accountable Delegation Protocol |
| **Architecture Design** | ✅ Completed | Multi-tier FastAPI + React design |
| **Backend REST API** | ✅ Completed | `backend/main.py` & `routers/*.py` (10 endpoints) |
| **Frontend Prototype** | ✅ Completed | `frontend/index.html` (7 Interactive Pages) |
| **Automated Test Suite** | ✅ Completed | `backend/test_phase4.py` (9/9 Tests Passing) |
| **Explanation Layer** | ⏳ Planned (Phase 5) | Future AI/Rule-based natural language explainer |
| **Human Fallback Review** | ⏳ Planned (Phase 6) | Future SOC analyst escalation interface |
| **Edge-Case Stress Testing** | ⏳ Planned (Phase 7) | Future concurrent session conflict testing |
| **Final Evaluation Report** | ⏳ Planned (Phase 8) | Final project review documentation |

---

## 15. Expected Evaluation

In future project phases, the system will undergo rigorous comparative evaluation between the legacy baseline and the accountable delegation prototype.

### Core Quantitative Metrics

1. **Individual Attribution Rate (IAR)**:
   $$\text{IAR} = \frac{\text{Attributable Sensitive Actions}}{\text{Total Sensitive Actions}} \times 100$$
2. **Permission Denial Accuracy**: Percentage of invalid access attempts correctly rejected by the permission validator.
3. **Unattributed Action Percentage**: Ratio of actions executed without an active delegation token.

### Initial Empirical Evaluation Results (Review 1 Dataset)

```
+-----------------------------------+-------------------+-------------------+
| EVALUATION METRIC                 | BASELINE SYSTEM   | PROTOTYPE SYSTEM  |
+-----------------------------------+-------------------+-------------------+
| Total Logged Operations           | 140 Log Entries   | 60 Action Traces  |
| Sensitive Actions (High/Critical) | 140 Actions       | 60 Actions        |
| Individually Attributed Actions   | 0 Actions         | 51 Actions        |
| Unattributed Actions              | 140 Actions       | 9 Actions         |
| Individual Attribution Rate (IAR) | 0.00%             | 85.00%            |
+-----------------------------------+-------------------+-------------------+
| NET IAR IMPROVEMENT               |                   | +85.00%           |
+-----------------------------------+-------------------+-------------------+
```

> **Note on Metric Realism**: The prototype achieves an 85.0% attribution rate rather than an artificial 100%, accurately reflecting permission denials and un-delegated baseline edge cases included in the synthetic dataset.

---

## 16. Expected Outcomes

Upon full completion, the system is expected to achieve:

* **Elimination of Anonymous Shared Usage**: Full traceability of legacy shared account actions to verified human operators.
* **Granular Privilege Enforcement**: Prevention of low-clearance personnel accessing high-risk shared accounts.
* **Enhanced Audit Integrity**: Automated creation of non-repudiable, time-stamped audit logs.
* **Multi-Department Support**: Seamless handling of internal staff and external contractor access across varied organisational boundaries.
* **Robust Exception Handling**: Clear categorization of unattributed or permission-denied events for post-incident review.

---

## 17. Future Work Plan

Following Review 1, project development will proceed across the remaining phases:

1. **Complete Working Prototype Enhancement**: Expand real-time WebSocket notifications for active delegation session events.
2. **Natural Language Explanation Layer**: Develop an explanation engine to summarize attribution evidence for SOC analysts.
3. **Human-in-the-Loop Fallback Workflow**: Implement a manual review dashboard for resolving ambiguous or unattributed session logs.
4. **Edge-Case Scenario Handling**: Evaluate system behavior under session timeouts, concurrent token requests, and network dropouts.
5. **Machine Learning Anomaly Detection**: Incorporate behavioral scoring to detect credential misuse or session hijacking.
6. **Stakeholder Usability Validation**: Conduct user testing with security analysts to assess workflow clarity.
7. **Comprehensive Privacy Evaluation**: Perform formal privacy impact analysis on identity token storage.
8. **Deployment Hardening Checklist**: Formulate production security guidelines including TLS encryption, JWT signed tokens, and database encryption at rest.
9. **Final Comparative Evaluation Report**: Compile final thesis documentation and performance benchmarking results.

---

## 18. Review 1 Conclusion

The **Review 1 (35% Progress)** milestone successfully establishes the foundational architecture and proof-of-concept for the **Shared-Account Elimination Workflow Using Accountable Delegation and Session Attribution**. 

By defining realistic multi-department scenarios, engineering synthetic evaluation datasets, constructing a legacy baseline model showing a 0.0% attribution rate, and delivering a functional FastAPI + React full-stack prototype, the project demonstrates that accountable delegation effectively restores individual non-repudiation to legacy systems. 

Subsequent phases will build upon this foundation by adding explanation mechanisms, human fallback review workflows, and comprehensive edge-case evaluation.

---

## 19. References

1. National Institute of Standards and Technology (NIST). (2020). *Security and Privacy Controls for Information Systems and Organizations*. NIST Special Publication 800-53, Revision 5.
2. International Organization for Standardization (ISO). (2022). *Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC 27001:2022.
3. Center for Internet Security (CIS). (2021). *CIS Critical Security Controls Version 8 — Control 5: Account Management & Control 6: Access Control Management*.
4. Sandhu, R. S., Coyne, E. J., Feinstein, H. L., & Youman, C. E. (1996). *Role-based access control models*. IEEE Computer, 29(2), 38-47.
5. Hu, V. C., Ferraiolo, D., Kuhn, R., Friedman, A. R., Lang, A. J., Cogdell, M. M., & Scarfone, K. (2013). *Guide to Attribute Based Access Control (ABAC) Definition and Considerations*. NIST Special Publication 800-162.

---

## Review 1 Deliverables Summary

1. **Scenario Definition**: Multi-agency government department threat and operational scenario.
2. **Baseline Design**: Empirical 0.0% IAR baseline evaluation script (`baseline_evaluation.py`).
3. **Synthetic Dataset Design**: 4 structured synthetic CSV datasets (`users.csv`, `shared_accounts.csv`, `system_logs.csv`, `privileged_actions.csv`).
4. **Proposed Architecture**: Multi-tier architecture diagram and component specification.
5. **Accountable Delegation Workflow**: Permission-checked 9-step access request protocol.
6. **Session Attribution Workflow**: Deterministic delegation token-to-user resolution logic.
7. **Basic Working Prototype**: Python FastAPI backend + React frontend SPA with 7 interactive pages.
8. **Evaluation Methodology**: Standardized Individual Attribution Rate (IAR) evaluation framework.
