"""
main.py — FastAPI Application Entry Point for Review 2 (70% Completion).
Shared-Account Elimination Workflow Using Accountable Delegation and Session Attribution.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db
from seed import seed
from routers import dashboard, users, shared_accounts, sessions, actions, reviews, evaluation, scenarios
from routers.actions import get_audit_log
from routers.sessions import request_delegation
from schemas import DelegationRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed database if tables are empty
    seed()
    yield
    # Shutdown: clean up if needed


app = FastAPI(
    title="Shared-Account Elimination Workflow — Review 2 Prototype",
    description=(
        "Production-grade cybersecurity prototype for Review 2 (70% milestone). "
        "Implements accountable delegation, deterministic session attribution, explanation layer, "
        "and human fallback review queue to eliminate shared accounts in legacy enterprise architectures."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for the React frontend running in browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Review 2 Routers
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(shared_accounts.router)
app.include_router(sessions.router)
app.include_router(actions.router)
app.include_router(reviews.router)
app.include_router(evaluation.router)
app.include_router(scenarios.router)


@app.get("/")
def root():
    return {
        "project": "Shared-Account Elimination Workflow Using Accountable Delegation and Session Attribution",
        "review": "Review 2 Prototype",
        "milestone_completion": "70%",
        "status": "operational",
        "docs": "/docs",
        "components": [
            "Accountable Delegation Service",
            "Deterministic Session Attribution",
            "Multi-Organisation Policy Enforcement",
            "Granular L1-L4 Permission Validation",
            "Rule-Based Explanation Layer",
            "Human Fallback Review Queue",
            "Empirical Evaluation & Benchmark Runner",
            "Edge Case & Failure Simulator"
        ]
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "milestone": "Review 2 (70%)"
    }


# Backwards-compatible aliases for Review 1 frontends / tests
@app.get("/audit-log")
@app.get("/audit-log/")
def audit_log_alias(
    user_id: str = None,
    organisation_id: str = None,
    shared_account_id: str = None,
    action_type: str = None,
    attribution_status: str = None,
    risk_level: str = None,
    db: Session = Depends(get_db)
):
    return get_audit_log(
        user_id=user_id,
        organisation_id=organisation_id,
        shared_account_id=shared_account_id,
        action_type=action_type,
        attribution_status=attribution_status,
        risk_level=risk_level,
        db=db
    )


@app.post("/delegations/request")
def delegation_request_alias(req: DelegationRequest, db: Session = Depends(get_db)):
    return request_delegation(req, db)
