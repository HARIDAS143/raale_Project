"""
routers/evaluation.py — Synthetic evaluation benchmarks and results export endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.evaluation_service import compute_metrics, save_evaluation_results, load_evaluation_results

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get("/results")
def get_evaluation_results(db: Session = Depends(get_db)):
    """Returns the latest empirical evaluation metrics comparing Baseline vs Prototype."""
    return load_evaluation_results(db)


@router.post("/run")
def trigger_evaluation_run(db: Session = Depends(get_db)):
    """
    Executes a reproducible evaluation pass across the active database,
    calculates empirical IAR, and updates evaluation_results.json.
    """
    results = compute_metrics(db)
    filepath = save_evaluation_results(results)
    return {
        "status": "SUCCESS",
        "message": "Evaluation executed successfully from database evidence.",
        "results_file": filepath,
        "metrics": results
    }
