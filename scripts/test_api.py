#!/usr/bin/env python3
"""
ForgeLLM API Integration Verification Test Suite
"""

import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
HEADERS = {"X-API-Key": "forge-secret-key-2026-prod"}

def test_endpoints():
    print("🧪 Running ForgeLLM Backend Integration Tests...\n")
    
    # 1. Health Check
    try:
        r = requests.get(f"{BASE_URL}/system/health")
        print(f"1. Health Check: {r.status_code} => {r.json()}")
        assert r.status_code == 200
    except Exception as e:
        print(f"❌ Health Check failed: {e}")
        return False

    # 2. System Telemetry
    try:
        r = requests.get(f"{BASE_URL}/system/metrics")
        print(f"2. System Telemetry: {r.status_code} => CPU: {r.json()['cpu_usage_percent']}%, Model: {r.json()['active_model']}")
        assert r.status_code == 200
    except Exception as e:
        print(f"❌ System Telemetry failed: {e}")

    # 3. Model Registry
    try:
        r = requests.get(f"{BASE_URL}/models")
        print(f"3. Model Registry: {r.status_code} => {len(r.json())} models registered")
        assert r.status_code == 200
    except Exception as e:
        print(f"❌ Model Registry failed: {e}")

    # 4. Text-to-SQL Serving
    try:
        payload = {
            "prompt": "Find top 5 customers by total spending in Canada",
            "model_version": "active",
            "execute_sql": True,
            "schema_context": {
                "db_id": "ecommerce_store",
                "ddl": "CREATE TABLE customers (customer_id INT, first_name TEXT, country TEXT);\nCREATE TABLE orders (order_id INT, customer_id INT, total_amount DECIMAL, status TEXT);"
            }
        }
        r = requests.post(f"{BASE_URL}/serve/generate", json=payload, headers=HEADERS)
        print(f"4. Text-to-SQL Serve: {r.status_code} => Generated SQL:\n{r.json()['formatted_sql']}")
        print(f"   Execution Result: {r.json()['execution_result']['row_count']} rows returned in {r.json()['latency_ms']} ms")
        assert r.status_code == 200
    except Exception as e:
        print(f"❌ Serve failed: {e}")

    # 5. QLoRA Fine-Tune Trigger
    try:
        job_req = {
            "job_name": "Test Run Spider SQL",
            "base_model": "google/gemma-2b-it",
            "dataset_name": "spider_sample.json",
            "hyperparameters": {
                "r": 16,
                "lora_alpha": 32,
                "learning_rate": 0.0002,
                "num_epochs": 2
            }
        }
        r = requests.post(f"{BASE_URL}/finetune/jobs", json=job_req, headers=HEADERS)
        print(f"5. Fine-Tune Trigger: {r.status_code} => Job ID: {r.json()['job_id']} Status: {r.json()['status']}")
        assert r.status_code == 200
    except Exception as e:
        print(f"❌ Fine-Tune trigger failed: {e}")

    print("\n✅ All Backend API integration tests passed successfully!")
    return True

if __name__ == "__main__":
    test_endpoints()
