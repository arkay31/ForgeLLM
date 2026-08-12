from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.schemas import SQLGenerationRequest, SQLGenerationResponse

router = APIRouter(prefix="/serve", tags=["Inference & SQL Serving"])


@router.post(
    "/generate",
    response_model=SQLGenerationResponse,
)
async def generate_sql(request: SQLGenerationRequest):
    """Generates a text-to-SQL query from natural language with schema grounding & live execution."""
    from app.services.inference_engine import inference_engine

    if request.stream:
        return StreamingResponse(
            inference_engine.generate_sql_stream(request),
            media_type="text/event-stream"
        )

    return await inference_engine.generate_sql(request)


@router.post(
    "/generate/stream",
)
async def generate_sql_stream(request: SQLGenerationRequest):
    """Streams generated SQL query tokens over Server-Sent Events (SSE)."""
    from app.services.inference_engine import inference_engine

    return StreamingResponse(
        inference_engine.generate_sql_stream(request),
        media_type="text/event-stream"
    )

