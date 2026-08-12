import pytest
from app.models.schemas import PerformanceBenchmarkRequest
from app.services.benchmarking_service import benchmarking_service


@pytest.mark.anyio
async def test_performance_benchmark_execution():
    """Verify performance benchmark executes concurrent requests and computes valid throughput & latencies."""
    req = PerformanceBenchmarkRequest(
        num_requests=4,
        concurrency=2,
        timeout_seconds=5.0,
        dataset_name="spider_sample.json",
        checkpoint_id="forgellm-qlora-v1-spider",
        compare_base=True,
    )

    res = await benchmarking_service.run_benchmark(req)

    assert res.benchmark_id.startswith("perf-")
    assert res.num_requests == 4
    assert res.concurrency == 2
    assert res.finetuned_metrics is not None
    assert res.finetuned_metrics.total_requests == 4
    assert res.finetuned_metrics.throughput_req_sec > 0.0
    assert res.finetuned_metrics.p50_latency_ms >= 0.0
    assert res.finetuned_metrics.p95_latency_ms >= 0.0
    assert res.base_metrics is not None
    assert res.base_metrics.total_requests == 4
    assert "machine-dependent" in res.hardware_notice
