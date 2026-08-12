from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ModelCheckpoint, DynamicHotSwapRequest, DeploymentEvent
from app.services.registry_service import registry_service
from app.services.auth_service import verify_api_key

router = APIRouter(prefix="/models", tags=["Model Registry & Lifecycle"])


@router.get("", response_model=list[ModelCheckpoint])
async def list_models():
    """Lists all registered model versions, hyperparameters, metrics, and lifecycle status."""
    return registry_service.list_checkpoints()


@router.get("/active", response_model=ModelCheckpoint)
async def get_active_model():
    """Returns the currently active serving model checkpoint."""
    return registry_service.get_active_checkpoint()


@router.get("/deployments/history", response_model=list[DeploymentEvent])
async def get_deployment_history():
    """Returns immutable deployment and rollback event history."""
    return registry_service.get_deployment_history()


@router.post("/active/swap", dependencies=[Depends(verify_api_key)])
async def hot_swap_active_model(req: DynamicHotSwapRequest):
    """Hot-swaps the serving model adapter live without downtime."""
    success, msg = registry_service.deploy_checkpoint(req.checkpoint_id)
    if not success:
        raise HTTPException(status_code=404 if "not found" in msg.lower() else 400, detail=msg)
    active = registry_service.get_active_checkpoint()
    return {"message": msg, "active_model": active}


@router.post("/{checkpoint_id}/deploy", dependencies=[Depends(verify_api_key)])
async def deploy_model(checkpoint_id: str):
    """Deploys a registered model checkpoint version to production serving traffic."""
    success, msg = registry_service.deploy_checkpoint(checkpoint_id)
    if not success:
        raise HTTPException(status_code=404 if "not found" in msg.lower() else 400, detail=msg)
    active = registry_service.get_active_checkpoint()
    return {"message": msg, "active_model": active}


@router.post("/rollback", dependencies=[Depends(verify_api_key)])
async def rollback_model():
    """Rolls back serving traffic to the previously active model checkpoint."""
    success, msg, rolled_back_cp = registry_service.rollback()
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "active_model": rolled_back_cp}


@router.delete("/{checkpoint_id}", dependencies=[Depends(verify_api_key)])
async def delete_checkpoint(checkpoint_id: str):
    """Deletes a checkpoint from registry. Blocked if the checkpoint is currently active."""
    success, msg = registry_service.delete_checkpoint(checkpoint_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "checkpoint_id": checkpoint_id}
