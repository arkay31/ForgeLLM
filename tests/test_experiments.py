import pytest
from app.models.schemas import ExperimentRecord
from app.services.experiment_service import experiment_service

def test_list_experiments():
    """Verify listing stored MLOps experiments."""
    exps = experiment_service.list_experiments()
    assert len(exps) >= 2
    ids = [e.experiment_id for e in exps]
    assert "exp-base-model-gemma" in ids
    assert "exp-qlora-v1-spider" in ids

def test_get_experiment():
    """Verify retrieving specific experiment details."""
    exp = experiment_service.get_experiment("exp-qlora-v1-spider")
    assert exp is not None
    assert exp.checkpoint_id == "forgellm-qlora-v1-spider"
    assert exp.lora_r == 16
    assert exp.exact_match_acc == 0.90
    assert exp.execution_acc == 0.96

def test_compare_experiments():
    """Verify side-by-side experiment comparison and metric diffs."""
    comp = experiment_service.compare_experiments("exp-base-model-gemma", "exp-qlora-v1-spider")
    assert comp.exp1.experiment_id == "exp-base-model-gemma"
    assert comp.exp2.experiment_id == "exp-qlora-v1-spider"
    assert comp.diff_exact_match_acc == 0.48  # 0.90 - 0.42
    assert comp.diff_execution_acc == 0.38    # 0.96 - 0.58
    assert comp.diff_p95_latency_ms == -112.0 # 48.0 - 160.0

def test_record_new_experiment():
    """Verify registering a new reproducible experiment."""
    new_exp = ExperimentRecord(
        experiment_id="exp-test-custom-run",
        timestamp="2026-08-12T19:00:00Z",
        job_id="job-custom-test",
        base_model="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        checkpoint_id="forgellm-custom-check",
        dataset_name="spider_sample.json",
        dataset_size=25,
        lora_r=32,
        lora_alpha=64,
        learning_rate=0.0001,
        epochs=5,
        batch_size=8,
        trainable_parameters=28000000,
        total_parameters=1540000000,
        training_time_seconds=120.0,
        final_train_loss=0.25,
        final_val_loss=0.29,
        exact_match_acc=0.92,
        execution_acc=0.98,
        avg_latency_ms=35.0,
        p50_latency_ms=30.0,
        p95_latency_ms=42.0,
        is_deployed=False,
        deployment_status="READY",
    )

    recorded = experiment_service.record_experiment(new_exp)
    assert recorded.experiment_id == "exp-test-custom-run"
    assert experiment_service.get_experiment("exp-test-custom-run") is not None
