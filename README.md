# Project: Shared-Account Elimination Workflow Using Accountable Delegation and Session Attribution
# Review 1 Prototype

## Quick Start

### 1. Backend (FastAPI + SQLite)

Open a terminal in this directory and run:

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The API will be available at: http://localhost:8000
Interactive API docs (Swagger): http://localhost:8000/docs

The database is seeded automatically on first startup.

### 2. Frontend

Open `frontend/index.html` directly in any modern browser (Chrome, Edge, Firefox).

**No Node.js or build step required.** The frontend uses React, Babel, and Chart.js from CDN.

---

## Project Structure

```
haridas project/
├── backend/
│   ├── main.py                   # FastAPI app entry point
│   ├── database.py               # SQLite connection (shared_workflow.db)
│   ├── models.py                 # ORM models (User, SharedAccount, SystemLog, Session, Action)
│   ├── seed.py                   # Seeds DB from CSV files
│   ├── requirements.txt
│   ├── routers/
│   │   ├── dashboard.py          # GET /dashboard/stats
│   │   ├── users.py              # GET /users/
│   │   ├── shared_accounts.py    # GET /shared-accounts/
│   │   ├── sessions.py           # GET /sessions/, /sessions/active
│   │   └── actions.py            # GET /actions/privileged, /baseline, /attribution-rate
│   └── data/
│       ├── users.csv             # 10 synthetic users
│       ├── shared_accounts.csv   # 5 legacy shared accounts
│       ├── system_logs.csv       # 20 baseline logs (no attribution)
│       └── privileged_actions.csv # 20 prototype actions (all attributed)
└── frontend/
    ├── index.html                # Single-file React app (open in browser)
    └── README.md
```

---

## Prototype Pages

| Page | URL/Nav | Description |
|------|---------|-------------|
| Dashboard | 📊 Dashboard | Summary stats + charts |
| Shared Accounts | 🔗 Shared Accounts | Legacy account table |
| Users | 👥 Users | Registered identities |
| Active Sessions | 🟢 Active Sessions | Delegation sessions |
| Privileged Actions | ⚡ Privileged Actions | Baseline vs prototype actions |
| Attribution Result | 📈 Attribution Result | IAR metric + comparison |

---

## Success Metric

**Individual Attribution Rate (IAR)**

```
IAR = Attributable Sensitive Actions / Total Sensitive Actions × 100
```

| System | IAR |
|--------|-----|
| Baseline (shared accounts) | 0% |
| Review 1 Prototype | 100% |
| **Improvement** | **+100%** |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /dashboard/stats | Aggregated dashboard statistics |
| GET | /users/ | All registered users |
| GET | /shared-accounts/ | All shared accounts |
| GET | /sessions/ | All delegation sessions |
| GET | /sessions/active | Active sessions only |
| GET | /actions/privileged | Attributed actions (prototype) |
| GET | /actions/baseline | System logs (baseline) |
| GET | /actions/attribution-rate | IAR calculation |

---

## Scenario

**Government Department: Digital Governance Authority (DGA)**

The DGA operates legacy applications (LegacyERP, GovPortal, NetworkMonitor, CoreDatabase) using shared accounts. Multiple employees and external vendors use the same credentials. When a sensitive action occurs — such as approving a payment or deleting a citizen record — the system can only record which shared account was used, not which individual performed the action.

**The Review 1 prototype demonstrates that by introducing an Accountable Delegation Workflow**, every sensitive action can be traced to an individual through a delegation token that binds the user's verified identity to their shared-account session.

---

## Actors

| Actor | Role | Description |
|-------|------|-------------|
| Government Employee | Action performer | Uses shared accounts for routine government tasks |
| Security Administrator | Workflow manager | Issues delegation tokens, manages session policies |
| Auditor | Reviewer | Examines audit trail for compliance and investigation |
| External Partner | Vendor user | Accesses systems under strict delegation with limited scope |
| Shared Account | Legacy identity | The shared credential (admin_shared, operator_shared, etc.) |
| Legacy Application | System | LegacyERP, GovPortal, NetworkMonitor, CoreDatabase |

---

## Workflow

```
User → Identity Verification → Accountable Delegation → Session Creation
     → Sensitive Action → Session Attribution → Audit Record
```

Each step:
1. **User** requests access to a shared account
2. **Identity Verification** confirms individual identity (USER001, USER002…)
3. **Accountable Delegation** issues a unique delegation token (TOK-XXXXXX)
4. **Session Creation** creates a SESSION record binding user ↔ shared account ↔ token
5. **Sensitive Action** is performed under the session
6. **Session Attribution** links the action to the individual via the token
7. **Audit Record** is created with full individual identity trail
