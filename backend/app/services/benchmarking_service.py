import asyncio
import json
import logging
import math
import time
import uuid
from datetime import datetime, timezone

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from app.config import settings, BASE_DIR
from app.models.schemas import (
    PerformanceBenchmarkRequest,
    PerformanceBenchmarkResponse,
    ModelPerformanceMetrics,
    SQLGenerationRequest,
    DatabaseSchemaContext,
)
from app.services.inference_engine import inference_engine
from app.services.registry_service import registry_service

logger = logging.getLogger("ForgeLLM.BenchmarkingService")


class InferenceBenchmarkingService:
    """
    Inference Performance & Concurrency Benchmarking Engine:
    - Measures API throughput (req/s), latency percentiles (Avg, P50, P95, P99),
      success rate, and error rate under concurrent load.
    - Compares Base Foundation Model vs Fine-Tuned QLoRA Adapter under identical load.
    - Zero fake measurements: executes real async inference calls with bounded concurrency semaphores.
    """

    @staticmethod
    def _calculate_percentile(values: List[float], p: float) -> float:
        """Calculates exact percentile from sorted latencies array."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return round(sorted_vals[int(k)], 2)
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return round(d0 + d1, 2)

    def _load_dataset_prompts(self, dataset_name: str, num_requests: int) -> List[Dict[str, Any]]:
        """Loads dataset questions and loops/samples items to reach requested request count."""
        data_file = BASE_DIR / "backend" / "app" / "data" / dataset_name
        if not data_file.exists():
            data_file = BASE_DIR / "backend" / "app" / "data" / "spider_sample.json"

        with open(data_file, "r", encoding="utf-8") as f:
            items = json.load(f)

        if not items:
            items = [
                {
                    "instruction": "Find all singers",
                    "db_id": "concert_singer",
                    "schema": "CREATE TABLE singer (singer_id INT, name TEXT);",
                }
            ]

        # Loop items if num_requests > len(items)
        sampled = []
        for i in range(num_requests):
            sampled.append(items[i % len(items)])
        return sampled

    async def _run_model_load_test(
        self,
        items: List[Dict[str, Any]],
        model_version: str,
        model_name: str,
        concurrency: int,
        timeout_seconds: float,
    ) -> ModelPerformanceMetrics:
        """Executes concurrent load test against inference engine using asyncio semaphores."""
        semaphore = asyncio.Semaphore(concurrency)
        latencies: List[float] = []
        successful_count = 0
        failed_count = 0

        async def worker(item: Dict[str, Any]):
            nonlocal successful_count, failed_count
            async with semaphore:
                db_id = item.get("db_id", "ecommerce_store")
                schema_ddl = item.get("schema", "")
                ctx = DatabaseSchemaContext(db_id=db_id, ddl=schema_ddl)
                req = SQLGenerationRequest(
                    prompt=item["instruction"],
                    schema_context=ctx,
                    model_version=model_version,
                    execute_sql=True,
                )

                t0 = time.perf_counter()
                try:
                    res = await asyncio.wait_for(
                        inference_engine.generate_sql(req),
                        timeout=timeout_seconds,
                    )
                    lat_ms = (time.perf_counter() - t0) * 1000.0
                    latencies.append(lat_ms)

                    if res.execution_result and not res.execution_result.error:
                        successful_count += 1
                    else:
                        failed_count += 1
                except Exception as err:
                    lat_ms = (time.perf_counter() - t0) * 1000.0
                    latencies.append(lat_ms)
                    failed_count += 1
                    logger.warning(f"Benchmark worker request failed ({err})")

        t_start = time.perf_counter()
        tasks = [worker(item) for item in items]
        await asyncio.gather(*tasks)
        t_total = time.perf_counter() - t_start
        t_total = max(t_total, 0.001)

        total_reqs = len(items)
        throughput = round(total_reqs / t_total, 2)
        avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        p50 = self._calculate_percentile(latencies, 50)
        p95 = self._calculate_percentile(latencies, 95)
        p99 = self._calculate_percentile(latencies, 99)

        return ModelPerformanceMetrics(
            model_name=model_name,
            checkpoint_id=model_version,
            total_requests=total_reqs,
            successful_requests=successful_count,
            failed_requests=failed_count,
            throughput_req_sec=throughput,
            avg_latency_ms=avg_lat,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            success_rate=round(successful_count / total_reqs, 4),
            error_rate=round(failed_count / total_reqs, 4),
        )

    async def run_benchmark(
        self,
        req: PerformanceBenchmarkRequest,
    ) -> PerformanceBenchmarkResponse:
        """Runs automated concurrent inference load benchmark."""
        t_overall_start = time.perf_counter()
        items = self._load_dataset_prompts(req.dataset_name, req.num_requests)

        # 1. Fine-Tuned Model Load Test
        ft_cp = registry_service.get_checkpoint(req.checkpoint_id)
        ft_name = ft_cp.name if ft_cp else f"Fine-Tuned ({req.checkpoint_id})"
        ft_metrics = await self._run_model_load_test(
            items=items,
            model_version=req.checkpoint_id,
            model_name=ft_name,
            concurrency=req.concurrency,
            timeout_seconds=req.timeout_seconds,
        )

        # 2. Base Model Load Test (if compare_base enabled)
        base_metrics = None
        if req.compare_base:
            base_cp = registry_service.get_checkpoint("base-model")
            base_name = base_cp.name if base_cp else "Base Foundation Model"
            base_metrics = await self._run_model_load_test(
                items=items,
                model_version="base",
                model_name=base_name,
                concurrency=req.concurrency,
                timeout_seconds=req.timeout_seconds,
            )

        t_overall_duration = round(time.perf_counter() - t_overall_start, 2)
        now_iso = datetime.now(timezone.utc).isoformat()

        return PerformanceBenchmarkResponse(
            benchmark_id=f"perf-{uuid.uuid4().hex[:8]}",
            timestamp=now_iso,
            dataset_name=req.dataset_name,
            num_requests=req.num_requests,
            concurrency=req.concurrency,
            timeout_seconds=req.timeout_seconds,
            total_duration_sec=t_overall_duration,
            base_metrics=base_metrics,
            finetuned_metrics=ft_metrics,
            hardware_notice="ℹ️ Benchmark results are machine-dependent and reflect local hardware performance (Apple Silicon MPS / CPU / RAM).",
        )


benchmarking_service = InferenceBenchmarkingService()
