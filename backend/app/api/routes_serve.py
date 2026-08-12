from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.models.schemas import SQLGenerationRequest, SQLGenerationResponse
from app.services.inference_engine import inference_engine
from app.services.auth_service import verify_api_key

router = APIRouter(prefix="/serve", tags=["Inference & SQL Serving"])

@router.post("/generate", response_model=SQLGenerationResponse, dependencies=[Depends(verify_api_key)])
async def generate_sql(request: SQLGenerationRequest):
    """Generates a text-to-SQL query from natural language with schema grounding & live execution."""
    if request.stream:
        return StreamingResponse(
            inference_engine.generate_sql_stream(request),
            media_type="text/event-stream"
        )
    return await inference_engine.generate_sql(request)

@router.post("/generate/stream", dependencies=[Depends(verify_api_key)])
async def generate_sql_stream(request: SQLGenerationRequest):
    """Streams generated SQL query tokens over Server-Sent Events (SSE)."""
    return StreamingResponse(
        inference_engine.generate_sql_stream(request),
        media_type="text/event-stream"
    )
