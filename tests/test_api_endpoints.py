import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)
API_HEADERS = {"X-API-Key": settings.ADMIN_API_KEY}


def test_health_endpoint():
    """Verify system health endpoint returns healthy status."""
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_metrics_endpoint():
    """Verify system metrics endpoint returns real hardware & process telemetry."""
    response = client.get("/api/v1/system/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cpu_usage_percent" in data
    assert "process_cpu_percent" in data
    assert "memory_used_gb" in data
    assert "process_memory_used_gb" in data
    assert "active_model" in data


def test_models_registry_endpoints():
    """Verify listing models, fetching active model, and deployment history endpoints."""
    # List all registered checkpoints
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert len(models) >= 1

    # Get active checkpoint
    response_active = client.get("/api/v1/models/active")
    assert response_active.status_code == 200
    active_cp = response_active.json()
    assert "checkpoint_id" in active_cp

    # Fetch deployment history
    response_history = client.get("/api/v1/models/deployments/history")
    assert response_history.status_code == 200
    history = response_history.json()
    assert isinstance(history, list)


def test_model_deploy_and_rollback_api_endpoints():
    """Verify deploy and rollback REST API endpoints."""
    models = client.get("/api/v1/models").json()
    target_cp = models[0]["checkpoint_id"]

    # Deploy checkpoint
    res_deploy = client.post(f"/api/v1/models/{target_cp}/deploy", headers=API_HEADERS)
    assert res_deploy.status_code in [200, 400]

    # Rollback checkpoint
    res_rollback = client.post("/api/v1/models/rollback", headers=API_HEADERS)
    assert res_rollback.status_code == 200
    assert "rolled back" in res_rollback.json()["message"].lower()


def test_serve_generate_endpoint():
    """Verify text-to-SQL SQL generation endpoint with schema context and execution."""
    payload = {
        "prompt": "Find top 5 customers by spending in Canada",
        "model_version": "active",
        "execute_sql": True,
        "schema_context": {
            "db_id": "ecommerce_store",
            "ddl": "CREATE TABLE customers (customer_id INT, first_name TEXT, country TEXT);",
        },
    }
    response = client.post("/api/v1/serve/generate", json=payload, headers=API_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "formatted_sql" in data
    assert "SELECT" in data["formatted_sql"]
    assert data["execution_result"] is not None
    assert "safety_result" in data
    assert data["safety_result"]["allowed"] is True


def test_eval_benchmark_endpoints():
    """Verify evaluation accuracy benchmark and performance load benchmark endpoints."""
    # Accuracy benchmark endpoint
    res_acc = client.post("/api/v1/eval/benchmark?limit=2", headers=API_HEADERS)
    assert res_acc.status_code == 200
    data_acc = res_acc.json()
    assert "base_exact_match_acc" in data_acc

    # Performance load benchmark endpoint
    perf_payload = {
        "num_requests": 2,
        "concurrency": 1,
        "timeout_seconds": 5.0,
        "dataset_name": "spider_sample.json",
        "checkpoint_id": "forgellm-qlora-v1-spider",
        "compare_base": True,
    }
    res_perf = client.post("/api/v1/eval/performance-benchmark", json=perf_payload, headers=API_HEADERS)
    assert res_perf.status_code == 200
    data_perf = res_perf.json()
    assert "throughput_req_sec" in data_perf["finetuned_metrics"]


def test_unauthenticated_demo_inference():
    """Verify demo inference endpoint succeeds without API key."""
    payload = {"prompt": "Test query"}
    response = client.post("/api/v1/serve/generate", json=payload)
    assert response.status_code == 200
    assert "formatted_sql" in response.json()


def test_unauthorized_access_protected_endpoint():
    """Verify API key authentication protection on protected admin endpoints."""
    bad_headers = {"X-API-Key": "invalid-secret-key"}
    response = client.post("/api/v1/models/active/swap", json={"checkpoint_id": "test"}, headers=bad_headers)
    assert response.status_code == 401

    # Protected endpoint without any API key header
    response_no_key = client.post("/api/v1/models/active/swap", json={"checkpoint_id": "test"})
    assert response_no_key.status_code == 401

