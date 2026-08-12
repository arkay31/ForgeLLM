import time

import psutil
import torch

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    Gauge,
)

from app.models.schemas import SystemMetricsResponse, SystemMetricsHistoryResponse, SystemTelemetryPoint
from app.services.registry_service import registry_service
from app.services.inference_engine import inference_engine


router = APIRouter(
    prefix="/system",
    tags=["System Telemetry & Prometheus"],
)


START_TIME = time.time()
SYSTEM_METRICS_HISTORY = []
MAX_METRICS_HISTORY = 30

# Initialize psutil baseline
psutil.cpu_percent(interval=None)


# ============================================================
# PROMETHEUS METRICS
# ============================================================

PROMETHEUS_REQUESTS_TOTAL = Counter(
    "forgellm_requests_total",
    "Total HTTP API Requests",
    ["endpoint", "status"],
)

PROMETHEUS_LATENCY_HISTOGRAM = Histogram(
    "forgellm_latency_seconds",
    "Inference Latency seconds",
    ["model"],
)

PROMETHEUS_GPU_MEM_GAUGE = Gauge(
    "forgellm_gpu_memory_used_bytes",
    "GPU/MPS Memory Used in Bytes",
)


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""

    return {
        "status": "healthy",
        "service": "ForgeLLM Engine",
        "timestamp": time.time(),
    }


# ============================================================
# SYSTEM METRICS
# ============================================================

@router.get(
    "/metrics",
    response_model=SystemMetricsResponse,
)
async def get_system_metrics():
    """Returns real-time hardware telemetry, process metrics, and serving stats."""

    # 1. System & Process CPU / RAM via psutil
    system_cpu = psutil.cpu_percent(interval=None)
    
    try:
        proc = psutil.Process()
        proc_cpu = proc.cpu_percent(interval=None)
        proc_mem_gb = round(proc.memory_info().rss / (1024 ** 3), 2)
    except Exception:
        proc_cpu = 0.0
        proc_mem_gb = 0.0

    mem = psutil.virtual_memory()

    # 2. Hardware Accelerator (NVIDIA CUDA or Apple Silicon MPS)
    gpu_available = False
    gpu_name = "N/A"
    gpu_mem_used = 0.0
    gpu_mem_total = 0.0

    if torch.cuda.is_available():
        gpu_available = True
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem_used = round(torch.cuda.memory_allocated(0) / (1024 ** 3), 2)
        gpu_mem_total = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        gpu_available = True
        gpu_name = "Apple Silicon Neural Engine (MPS UMA)"
        # Apple Silicon utilizes Unified Memory Architecture (UMA) shared RAM
        gpu_mem_used = round(mem.used / (1024 ** 3), 2)
        gpu_mem_total = round(mem.total / (1024 ** 3), 2)

    # 3. Model Serving Metrics & Latency Statistics
    active_cp = registry_service.get_active_checkpoint()
    uptime = round(time.time() - START_TIME, 1)

    requests_per_sec = round(
        inference_engine.inference_count / (uptime if uptime > 0 else 1),
        2,
    )

    current_time_str = time.strftime("%H:%M:%S")
    cpu_val = round(system_cpu, 1)
    mem_val = round(mem.percent, 1)

    # Append to rolling history deque
    SYSTEM_METRICS_HISTORY.append(
        SystemTelemetryPoint(
            time=current_time_str,
            cpu_usage_percent=cpu_val,
            memory_usage_percent=mem_val,
            gpu_memory_used_gb=gpu_mem_used,
            active_requests_per_sec=requests_per_sec,
        )
    )
    if len(SYSTEM_METRICS_HISTORY) > MAX_METRICS_HISTORY:
        SYSTEM_METRICS_HISTORY.pop(0)

    return SystemMetricsResponse(
        timestamp=current_time_str,
        cpu_usage_percent=cpu_val,
        process_cpu_percent=round(proc_cpu, 1),
        memory_used_gb=round(mem.used / (1024 ** 3), 2),
        memory_total_gb=round(mem.total / (1024 ** 3), 2),
        memory_usage_percent=mem_val,
        process_memory_used_gb=proc_mem_gb,
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        gpu_memory_used_gb=gpu_mem_used,
        gpu_memory_total_gb=gpu_mem_total,
        active_model=active_cp.name,
        active_requests_per_sec=requests_per_sec,
        uptime_seconds=uptime,
        total_requests=inference_engine.inference_count,
        successful_requests=inference_engine.successful_requests,
        failed_requests=inference_engine.failed_requests,
        avg_latency_ms=inference_engine.get_avg_latency(),
        p50_latency_ms=inference_engine.get_p50_latency(),
        p95_latency_ms=inference_engine.get_p95_latency(),
    )



# ============================================================
# SYSTEM HISTORY
# ============================================================

@router.get(
    "/history",
    response_model=SystemMetricsHistoryResponse,
)
async def get_system_metrics_history():
    """Returns historical system telemetry data points for charting."""

    return SystemMetricsHistoryResponse(
        history=SYSTEM_METRICS_HISTORY
    )


# ============================================================
# REAL INFERENCE LATENCY HISTORY
# ============================================================

@router.get("/latency-history")
async def get_latency_history():
    """
    Returns the most recent real inference latency
    measurements collected by the inference engine.
    """

    return {
        "history": (
            inference_engine.latency_history
        )
    }


# ============================================================
# PROMETHEUS
# ============================================================

@router.get(
    "/prometheus",
    response_class=PlainTextResponse,
)
async def get_prometheus_metrics():
    """Exposes Prometheus text format metrics."""

    return PlainTextResponse(
        generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )