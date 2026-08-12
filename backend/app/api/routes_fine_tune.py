from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.schemas import TrainingJobRequest, TrainingJobStatus
from app.services.trainer_engine import trainer_engine
from app.services.auth_service import verify_api_key

router = APIRouter(prefix="/finetune", tags=["QLoRA Fine-Tuning"])

@router.post("/jobs", response_model=TrainingJobStatus, dependencies=[Depends(verify_api_key)])
async def create_training_job(req: TrainingJobRequest):
    """Triggers a QLoRA fine-tuning job for text-to-SQL generation."""
    job = await trainer_engine.start_training_job(req)
    return job

@router.get("/jobs", response_model=list[TrainingJobStatus])
async def list_training_jobs():
    """Lists all fine-tuning jobs and their current state."""
    return trainer_engine.list_jobs()

@router.get("/jobs/{job_id}", response_model=TrainingJobStatus)
async def get_job_status(job_id: str):
    """Retrieves status and loss history for a specific fine-tuning job."""
    job = trainer_engine.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/jobs/{job_id}/cancel", dependencies=[Depends(verify_api_key)])
async def cancel_job(job_id: str):
    """Cancels an in-progress training job."""
    success = trainer_engine.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Unable to cancel job")
    return {"status": "cancelled", "job_id": job_id}

@router.get("/stream")
async def stream_training_telemetry():
    """Server-Sent Events (SSE) stream yielding real-time training step telemetry & logs."""
    return StreamingResponse(
        trainer_engine.subscribe(),
        media_type="text/event-stream"
    )
