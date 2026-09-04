from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db
from seed import seed
from routers import dashboard, users, shared_accounts, sessions, actions
from routers.actions import get_audit_log
from routers.sessions import request_delegation
from schemas import DelegationRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed database
    seed()
    yield
    # Shutdown: nothing to clean up for SQLite


app = FastAPI(
    title="Shared-Account Elimination Workflow — Review 1 Prototype",
    description=(
        "Backend API for the cybersecurity capstone project prototype. "
        "Demonstrates accountable delegation and session attribution to replace shared-account usage."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the React dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(shared_accounts.router)
app.include_router(sessions.router)
app.include_router(actions.router)


@app.get("/")
def root():
    return {
        "project": "Shared-Account Elimination Workflow Using Accountable Delegation and Session Attribution",
        "review": "Review 1 — 35% Baseline Prototype",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/audit-log")
@app.get("/audit-log/")
def audit_log_alias(db: Session = Depends(get_db)):
    return get_audit_log(db)


@app.post("/delegations/request")
def delegation_request_alias(req: DelegationRequest, db: Session = Depends(get_db)):
    return request_delegation(req, db)
