import pytest
from app.models.schemas import ModelCheckpoint
from app.services.registry_service import registry_service


def test_register_checkpoint():
    """Verify registering a new model checkpoint version."""
    new_cp = ModelCheckpoint(
        checkpoint_id="test-register-cp-v1",
        name="Test Model v1",
        version="v1.0.0",
        base_model="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        dataset_used="spider_sample.json",
        created_at="2026-08-12T10:00:00Z",
        status="READY",
        metrics={"exact_match": 0.85, "exec_acc": 0.90},
        hyperparameters={"r": 16},
        path="/tmp/test_cp_v1",
        size_mb=42.0,
    )
    registry_service.register_checkpoint(new_cp)

    retrieved = registry_service.get_checkpoint("test-register-cp-v1")
    assert retrieved is not None
    assert retrieved.name == "Test Model v1"
    assert retrieved.status == "READY"
    assert retrieved.version == "v1.0.0"


def test_deploy_checkpoint():
    """Verify deploying a checkpoint changes its status to ACTIVE and demotes old model."""
    success, msg = registry_service.deploy_checkpoint("test-register-cp-v1")
    assert success is True
    assert "successfully deployed" in msg

    active = registry_service.get_active_checkpoint()
    assert active.checkpoint_id == "test-register-cp-v1"
    assert active.status == "ACTIVE"


def test_active_model_deletion_protection():
    """Verify attempting to delete the currently active model is blocked."""
    active_cp = registry_service.get_active_checkpoint()
    success, msg = registry_service.delete_checkpoint(active_cp.checkpoint_id)
    assert success is False
    assert "Cannot delete or archive the currently active model" in msg


def test_rollback_checkpoint():
    """Verify rolling back restores the previous active model checkpoint."""
    # Ensure deployment history has a previous model
    current_active_id = registry_service.active_checkpoint_id

    success, msg, rolled_back_cp = registry_service.rollback()
    assert success is True
    assert rolled_back_cp is not None
    assert registry_service.active_checkpoint_id != current_active_id
    assert registry_service.get_active_checkpoint().status == "ACTIVE"


def test_invalid_checkpoint_deployment():
    """Verify deploying or deleting an invalid checkpoint ID fails gracefully."""
    success, msg = registry_service.deploy_checkpoint("non-existent-cp-id-999")
    assert success is False
    assert "not found" in msg.lower()

    del_success, del_msg = registry_service.delete_checkpoint("non-existent-cp-id-999")
    assert del_success is False
    assert "not found" in del_msg.lower()
