from typing import List
from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.schemas import ExperimentRecord, ExperimentComparisonResponse
from app.services.experiment_service import experiment_service
from app.api.routes_serve import verify_api_key

router = APIRouter(prefix="/experiments", tags=["Experiments & MLOps"])

@router.get("", response_model=List[ExperimentRecord])
def list_experiments():
    """Returns all recorded reproducible MLOps experiments."""
    return experiment_service.list_experiments()

@router.get("/compare", response_model=ExperimentComparisonResponse)
def compare_experiments(
    exp1_id: str = Query(..., description="First Experiment ID"),
    exp2_id: str = Query(..., description="Second Experiment ID")
):
    """Compares two experiments side-by-side and returns metric differences."""
    try:
        return experiment_service.compare_experiments(exp1_id, exp2_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.get("/{experiment_id}", response_model=ExperimentRecord)
def get_experiment(experiment_id: str):
    """Returns details for a specific experiment ID."""
    exp = experiment_service.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
    return exp

@router.post("/create", response_model=ExperimentRecord)
def create_experiment(
    record: ExperimentRecord,
    authorized: bool = Depends(verify_api_key)
):
    """Registers a new MLOps experiment record."""
    return experiment_service.record_experiment(record)
