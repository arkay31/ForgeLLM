import json
import logging
import os
import shutil
import time
import uuid
from datetime import datetime, timezone

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from app.config import settings
from app.models.schemas import ModelCheckpoint, DeploymentEvent

logger = logging.getLogger("ForgeLLM.RegistryService")


class RegistryService:
    """
    Model Lifecycle & Registry Service:
    - Supports model status lifecycle: REGISTERED, READY, ACTIVE, FAILED, ARCHIVED
    - Zero-downtime model deployment & rollback tracking
    - Maintains immutable deployment history audit logs
    - Prevents deletion/archiving of currently active serving model
    """

    def __init__(self):
        self.checkpoint_dir = settings.CHECKPOINT_DIR
        self.metadata_file = self.checkpoint_dir / "registry_metadata.json"
        self.active_checkpoint_id: str = "forgellm-qlora-v1-spider"
        self.checkpoints: Dict[str, ModelCheckpoint] = {}
        self.deployment_history: List[DeploymentEvent] = []
        self._load_registry()

    def _load_registry(self):
        # 1. Standard Base Model Checkpoint
        base_cp = ModelCheckpoint(
            checkpoint_id="base-model",
            name="Qwen-2.5-Coder-1.5B (Base)",
            version="base-v1.0",
            base_model=settings.DEFAULT_BASE_MODEL,
            dataset_used="N/A",
            created_at="2026-08-01T00:00:00Z",
            deployed_at=None,
            status="READY",
            metrics={"exact_match": 0.42, "exec_acc": 0.58, "latency_ms": 115.0},
            hyperparameters={},
            path=str(settings.MODEL_DIR / "base_model"),
            size_mb=2800.0,
        )
        self.checkpoints["base-model"] = base_cp

        # 2. Pre-seeded QLoRA Checkpoint
        pretrained_cp = ModelCheckpoint(
            checkpoint_id="forgellm-qlora-v1-spider",
            name="ForgeLLM QLoRA v1 (Spider-FineTuned)",
            version="v1.0.0",
            base_model=settings.DEFAULT_BASE_MODEL,
            dataset_used="spider_sample.json",
            created_at="2026-08-10T12:00:00Z",
            deployed_at="2026-08-10T12:05:00Z",
            status="ACTIVE",
            metrics={"exact_match": 0.88, "exec_acc": 0.94, "train_loss": 0.18, "latency_ms": 42.0},
            hyperparameters={"r": 16, "lora_alpha": 32, "learning_rate": 0.0002, "quantization": "4-bit QLoRA"},
            path=str(self.checkpoint_dir / "forgellm-qlora-v1-spider"),
            size_mb=42.5,
        )
        self.checkpoints["forgellm-qlora-v1-spider"] = pretrained_cp

        # Load persisted registry metadata if present
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.active_checkpoint_id = data.get("active_checkpoint_id", "forgellm-qlora-v1-spider")
                    for cp_dict in data.get("checkpoints", []):
                        cp = ModelCheckpoint(**cp_dict)
                        self.checkpoints[cp.checkpoint_id] = cp

                    for dep_dict in data.get("deployment_history", []):
                        self.deployment_history.append(DeploymentEvent(**dep_dict))
            except Exception as e:
                logger.warning(f"Error loading registry metadata: {e}")

        # Ensure correct active status consistency
                logger.warning(f"Failed to parse model registry metadata: {e}. Re-initializing.")

        if "forgellm-qlora-v1-spider" not in self.checkpoints:
            ft_cp = ModelCheckpoint(
                checkpoint_id="forgellm-qlora-v1-spider",
                name="ForgeLLM QLoRA Text-to-SQL",
                version="v1.0.0",
                base_model="Qwen/Qwen2.5-Coder-1.5B-Instruct",
                adapter_path="storage/checkpoints/forgellm-qlora-v1-spider",
                dataset_name="spider_sample.json",
                status="ACTIVE",
                lora_r=16,
                lora_alpha=32,
                learning_rate=2e-4,
                epochs=3,
                batch_size=4,
                exact_match_acc=0.9000,
                execution_acc=0.9600,
                avg_latency_ms=38.5,
                file_size_mb=14.5,
                created_at=datetime.now(timezone.utc).isoformat(),
                deployed_at=datetime.now(timezone.utc).isoformat(),
                description="Fine-tuned Text-to-SQL adapter model.",
            )
            self.checkpoints["forgellm-qlora-v1-spider"] = ft_cp
            self.active_checkpoint_id = "forgellm-qlora-v1-spider"

            self.deployment_history.append(
                DeploymentEvent(
                    event_id=f"dep-{uuid.uuid4().hex[:8]}",
                    checkpoint_id="forgellm-qlora-v1-spider",
                    model_name=ft_cp.name,
                    action="deploy",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    previous_checkpoint_id="base-model",
                    status="success",
                    details="Initial production deployment",
                )
            )
            self._save_registry()

    def _save_registry(self):
        try:
            data = {
                "active_checkpoint_id": self.active_checkpoint_id,
                "checkpoints": [cp.model_dump() for cp in self.checkpoints.values()],
                "deployment_history": [dep.model_dump() for dep in self.deployment_history],
            }
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving registry metadata: {e}")

    def list_checkpoints(self) -> List[ModelCheckpoint]:
        return list(self.checkpoints.values())

    def get_checkpoint(self, checkpoint_id: str) -> Optional[ModelCheckpoint]:
        cp = self.checkpoints.get(checkpoint_id)
        if cp and cp.path and not Path(cp.path).exists():
            candidate = self.checkpoint_dir / Path(cp.path).name
            if candidate.exists():
                cp.path = str(candidate)
        return cp


    def register_checkpoint(self, checkpoint: ModelCheckpoint):
        """Registers a new model checkpoint version in the registry."""
        if not checkpoint.status:
            checkpoint.status = "READY"
        self.checkpoints[checkpoint.checkpoint_id] = checkpoint
        self._save_registry()

    def deploy_checkpoint(self, checkpoint_id: str) -> Tuple[bool, str]:
        """Deploys a checkpoint version as the active serving model."""
        if checkpoint_id not in self.checkpoints:
            return False, f"Checkpoint ID '{checkpoint_id}' not found in model registry."

        previous_id = self.active_checkpoint_id
        target_cp = self.checkpoints[checkpoint_id]

        # Update lifecycle status flags
        for cp in self.checkpoints.values():
            if cp.status == "ACTIVE":
                cp.status = "READY"

        now_str = datetime.now(timezone.utc).isoformat()
        target_cp.status = "ACTIVE"
        target_cp.deployed_at = now_str
        self.active_checkpoint_id = checkpoint_id

        # Log deployment event
        dep_event = DeploymentEvent(
            event_id=f"dep-{uuid.uuid4().hex[:8]}",
            checkpoint_id=checkpoint_id,
            model_name=target_cp.name,
            action="deploy",
            timestamp=now_str,
            previous_checkpoint_id=previous_id,
            status="success",
            details=f"Deployed model version {target_cp.version}",
        )
        self.deployment_history.insert(0, dep_event)

        self._save_registry()
        return True, f"Model '{target_cp.name}' ({checkpoint_id}) successfully deployed to production traffic."

    def rollback(self) -> Tuple[bool, str, Optional[ModelCheckpoint]]:
        """Rolls back serving traffic to the previously active model checkpoint."""
        if not self.deployment_history:
            return False, "No previous deployment history available for rollback.", None

        # Search for previous active checkpoint in deployment history
        target_id = None
        for dep in self.deployment_history:
            if dep.previous_checkpoint_id and dep.previous_checkpoint_id != self.active_checkpoint_id:
                if dep.previous_checkpoint_id in self.checkpoints:
                    target_id = dep.previous_checkpoint_id
                    break

        if not target_id:
            target_id = "base-model" if self.active_checkpoint_id != "base-model" else None

        if not target_id or target_id not in self.checkpoints:
            return False, "No valid previous checkpoint found to rollback to.", None

        previous_id = self.active_checkpoint_id
        target_cp = self.checkpoints[target_id]

        # Perform deployment swap
        for cp in self.checkpoints.values():
            if cp.status == "ACTIVE":
                cp.status = "READY"

        now_str = datetime.now(timezone.utc).isoformat()
        target_cp.status = "ACTIVE"
        target_cp.deployed_at = now_str
        self.active_checkpoint_id = target_id

        # Record rollback audit event
        rollback_event = DeploymentEvent(
            event_id=f"dep-{uuid.uuid4().hex[:8]}",
            checkpoint_id=target_id,
            model_name=target_cp.name,
            action="rollback",
            timestamp=now_str,
            previous_checkpoint_id=previous_id,
            status="success",
            details=f"Rolled back from {previous_id} to {target_id}",
        )
        self.deployment_history.insert(0, rollback_event)

        self._save_registry()
        return True, f"Serving traffic successfully rolled back to '{target_cp.name}' ({target_id}).", target_cp

    def get_active_checkpoint(self) -> ModelCheckpoint:
        return self.checkpoints.get(self.active_checkpoint_id, self.checkpoints["base-model"])

    def get_deployment_history(self) -> List[DeploymentEvent]:
        return self.deployment_history

    def delete_checkpoint(self, checkpoint_id: str) -> Tuple[bool, str]:
        """Deletes a checkpoint from registry. Enforces safety: cannot delete active model."""
        if checkpoint_id not in self.checkpoints:
            return False, f"Checkpoint ID '{checkpoint_id}' not found in registry."

        if checkpoint_id == "base-model":
            return False, "Cannot delete standard base model checkpoint."

        if checkpoint_id == self.active_checkpoint_id or self.checkpoints[checkpoint_id].status == "ACTIVE":
            return False, f"Cannot delete or archive the currently active model '{checkpoint_id}'. Please deploy another model first."

        cp = self.checkpoints.pop(checkpoint_id)
        self._save_registry()

        # Delete artifact directory if it exists
        cp_path = Path(cp.path)
        if cp_path.exists() and cp_path.is_dir():
            shutil.rmtree(cp_path, ignore_errors=True)

        return True, f"Checkpoint '{checkpoint_id}' successfully deleted."


registry_service = RegistryService()
