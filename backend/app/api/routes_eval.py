from typing import Optional

from fastapi import APIRouter, Depends

from app.models.schemas import (
    BenchmarkRunResponse,
    PerformanceBenchmarkRequest,
    PerformanceBenchmarkResponse,
)
from app.services.auth_service import verify_api_key

router = APIRouter(prefix="/eval", tags=["Evaluation & Benchmarking"])


@router.post(
    "/benchmark",
    response_model=BenchmarkRunResponse,
    dependencies=[Depends(verify_api_key)],
)
async def run_benchmark(
    dataset_name: str = "spider_sample.json",
    checkpoint_id: str = "forgellm-qlora-v1-spider",
    limit: Optional[int] = 5,
):
    """
    Runs end-to-end benchmarking evaluation comparing Base Model vs Fine-Tuned Model.
    Supports dataset sample limit (e.g. 5, 25, 50, 0 for all available queries).
    """
    from app.services.eval_service import eval_service

    return await eval_service.run_benchmark(
        dataset_name=dataset_name,
        checkpoint_id=checkpoint_id,
        limit=limit if limit is not None else 5,
    )


@router.post(
    "/performance-benchmark",
    response_model=PerformanceBenchmarkResponse,
    dependencies=[Depends(verify_api_key)],
)
async def run_performance_benchmark(req: PerformanceBenchmarkRequest):
    """
    Runs concurrent inference load and throughput performance benchmark.
    Measures req/s throughput, P50, P95, P99 latencies, success/error rates.
    """
    from app.services.benchmarking_service import benchmarking_service

    return await benchmarking_service.run_benchmark(req)


@router.get("/history", response_model=list[BenchmarkRunResponse])
async def get_benchmark_history():
    """Returns past evaluation run metrics."""
    from app.services.eval_service import eval_service

    return eval_service.history
