#!/usr/bin/env python3
"""
ForgeLLM Inference Performance & Concurrency Benchmarking CLI Tool

Usage:
  python scripts/benchmark_inference.py --requests 20 --concurrency 4
  python scripts/benchmark_inference.py --requests 50 --concurrency 8 --dataset spider_sample.json --output storage/benchmark_results.json
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.models.schemas import PerformanceBenchmarkRequest
from app.services.benchmarking_service import benchmarking_service


def print_table_header():
    print("=" * 84)
    print(f"{'MODEL NAME':<32} | {'REQ/SEC':<8} | {'AVG(ms)':<8} | {'P50(ms)':<8} | {'P95(ms)':<8} | {'SUCCESS':<8}")
    print("=" * 84)


def print_metrics_row(metrics):
    name = metrics.model_name[:30]
    tput = f"{metrics.throughput_req_sec:.1f}"
    avg_l = f"{metrics.avg_latency_ms:.1f}"
    p50_l = f"{metrics.p50_latency_ms:.1f}"
    p95_l = f"{metrics.p95_latency_ms:.1f}"
    succ = f"{metrics.success_rate * 100:.0f}%"
    print(f"{name:<32} | {tput:<8} | {avg_l:<8} | {p50_l:<8} | {p95_l:<8} | {succ:<8}")


async def main():
    parser = argparse.ArgumentParser(
        description="ForgeLLM Concurrent Inference Load & Performance Benchmarking Tool"
    )
    parser.add_argument("--requests", type=int, default=20, help="Total number of requests to execute (default: 20)")
    parser.add_argument("--concurrency", type=int, default=4, help="Concurrency limit / parallel workers (default: 4)")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds (default: 10.0)")
    parser.add_argument("--dataset", type=str, default="spider_sample.json", help="Dataset name to sample prompts (default: spider_sample.json)")
    parser.add_argument("--checkpoint", type=str, default="forgellm-qlora-v1-spider", help="Checkpoint ID to test (default: forgellm-qlora-v1-spider)")
    parser.add_argument("--output", type=str, default="storage/benchmark_results.json", help="Output path for JSON results")

    args = parser.parse_args()

    print("\n🚀 Launching ForgeLLM Inference Performance Load Benchmark...")
    print(f"   Configuration: {args.requests} Requests | Concurrency={args.concurrency} | Timeout={args.timeout}s | Dataset={args.dataset}")
    print("-" * 84)

    req = PerformanceBenchmarkRequest(
        num_requests=args.requests,
        concurrency=args.concurrency,
        timeout_seconds=args.timeout,
        dataset_name=args.dataset,
        checkpoint_id=args.checkpoint,
        compare_base=True,
    )

    res = await benchmarking_service.run_benchmark(req)

    print("\n📊 BENCHMARK RESULTS SUMMARY:")
    print_table_header()
    if res.base_metrics:
        print_metrics_row(res.base_metrics)
    if res.finetuned_metrics:
        print_metrics_row(res.finetuned_metrics)
    print("=" * 84)

    print(f"\n⏱️ Total Test Duration: {res.total_duration_sec:.2f} seconds")
    print(f"{res.hardware_notice}\n")

    output_path = BASE_DIR / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(res.model_dump(), f, indent=2)


    print(f"📁 Benchmark JSON results saved to: {output_path.resolve()}\n")


if __name__ == "__main__":
    asyncio.run(main())
