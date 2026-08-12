import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from app.config import settings, STORAGE_DIR
from app.models.schemas import ExperimentRecord, ExperimentComparisonResponse

logger = logging.getLogger("forgellm.experiments")

EXPERIMENTS_FILE = STORAGE_DIR / "experiments" / "experiments_metadata.json"


class ExperimentService:
    def __init__(self):
        self.experiments: Dict[str, ExperimentRecord] = {}
        self._ensure_storage_and_defaults()

    def _ensure_storage_and_defaults(self):
        EXPERIMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if EXPERIMENTS_FILE.exists():
            try:
                with open(EXPERIMENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        exp = ExperimentRecord(**item)
                        self.experiments[exp.experiment_id] = exp
                logger.info(f"Loaded {len(self.experiments)} experiments from storage.")
                return
            except Exception as err:
                logger.warning(f"Error reading experiments metadata: {err}. Re-initializing defaults.")

        # Seed baseline reproducible experiments for complete MLOps lifecycle
        default_experiments = [
            ExperimentRecord(
                experiment_id="exp-base-model-gemma",
                timestamp="2026-08-10T12:00:00Z",
                job_id="job-base-zero-tune",
                base_model="Qwen/Qwen2.5-Coder-1.5B-Instruct",
                checkpoint_id="base-model",
                dataset_name="spider_sample.json",
                dataset_size=50,
                lora_r=0,
                lora_alpha=0,
                learning_rate=0.0,
                epochs=0,
                batch_size=0,
                trainable_parameters=0,
                total_parameters=1540000000,
                training_time_seconds=0.0,
                final_train_loss=2.85,
                final_val_loss=3.10,
                exact_match_acc=0.42,
                execution_acc=0.58,
                avg_latency_ms=125.0,
                p50_latency_ms=115.0,
                p95_latency_ms=160.0,
                is_deployed=False,
                deployment_status="READY",
            ),
            ExperimentRecord(
                experiment_id="exp-qlora-v1-spider",
                timestamp="2026-08-12T14:30:00Z",
                job_id="job-qlora-prod-v1",
                base_model="Qwen/Qwen2.5-Coder-1.5B-Instruct",
                checkpoint_id="forgellm-qlora-v1-spider",
                dataset_name="spider_sample.json",
                dataset_size=50,
                lora_r=16,
                lora_alpha=32,
                learning_rate=0.0002,
                epochs=3,
                batch_size=4,
                trainable_parameters=14100000,
                total_parameters=1540000000,
                training_time_seconds=94.5,
                final_train_loss=0.342,
                final_val_loss=0.389,
                exact_match_acc=0.90,
                execution_acc=0.96,
                avg_latency_ms=38.5,
                p50_latency_ms=32.0,
                p95_latency_ms=48.0,
                is_deployed=True,
                deployment_status="ACTIVE",
            ),
        ]

        for exp in default_experiments:
            self.experiments[exp.experiment_id] = exp
        self._save_experiments()

    def _save_experiments(self):
        try:
            with open(EXPERIMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump([exp.model_dump() for exp in self.experiments.values()], f, indent=2)
        except Exception as err:
            logger.error(f"Failed to save experiments metadata: {err}")


    def list_experiments(self) -> List[ExperimentRecord]:
        return list(self.experiments.values())

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentRecord]:
        return self.experiments.get(experiment_id)

    def record_experiment(self, record: ExperimentRecord) -> ExperimentRecord:
        self.experiments[record.experiment_id] = record
        self._save_experiments()
        return record

    def compare_experiments(self, exp1_id: str, exp2_id: str) -> ExperimentComparisonResponse:
        e1 = self.get_experiment(exp1_id)
        e2 = self.get_experiment(exp2_id)

        if not e1 or not e2:
            raise ValueError(f"One or both experiment IDs not found: {exp1_id}, {exp2_id}")

        return ExperimentComparisonResponse(
            exp1=e1,
            exp2=e2,
            diff_exact_match_acc=round(e2.exact_match_acc - e1.exact_match_acc, 4),
            diff_execution_acc=round(e2.execution_acc - e1.execution_acc, 4),
            diff_avg_latency_ms=round(e2.avg_latency_ms - e1.avg_latency_ms, 2),
            diff_p50_latency_ms=round(e2.p50_latency_ms - e1.p50_latency_ms, 2),
            diff_p95_latency_ms=round(e2.p95_latency_ms - e1.p95_latency_ms, 2),
            diff_final_val_loss=round(e2.final_val_loss - e1.final_val_loss, 4),
        )

experiment_service = ExperimentService()
