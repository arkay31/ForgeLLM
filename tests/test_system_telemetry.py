import psutil
import pytest
from app.api.routes_system import get_system_metrics
from app.services.inference_engine import inference_engine


@pytest.mark.anyio
async def test_get_system_metrics():
    """Verify real system metrics endpoint returns accurate hardware and process metrics."""
    metrics = await get_system_metrics()

    assert metrics.timestamp is not None
    assert isinstance(metrics.cpu_usage_percent, float)
    assert 0.0 <= metrics.cpu_usage_percent <= 100.0
    assert isinstance(metrics.memory_used_gb, float)
    assert metrics.memory_used_gb >= 0.0
    assert metrics.memory_total_gb > 0.0
    assert isinstance(metrics.process_cpu_percent, float)
    assert isinstance(metrics.process_memory_used_gb, float)
    assert metrics.process_memory_used_gb >= 0.0
    assert metrics.active_model is not None


def test_inference_telemetry_counters():
    """Verify inference engine latency percentiles and request success/fail counters."""
    inference_engine.latency_history.clear()
    inference_engine.successful_requests = 10
    inference_engine.failed_requests = 2
    inference_engine.inference_count = 12

    # Mock latency entries
    for lat in [10.0, 20.0, 30.0, 40.0, 50.0]:
        inference_engine.latency_history.append({"latency_ms": lat})

    assert inference_engine.get_avg_latency() == 30.0
    assert inference_engine.get_p50_latency() == 30.0
    assert inference_engine.get_p95_latency() == 48.0

