from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# --- QLoRA Fine-Tuning Schemas ---
class QLoRAHyperparameters(BaseModel):
    r: int = Field(default=16, description="LoRA rank dimension")
    lora_alpha: int = Field(default=32, description="LoRA alpha scaling factor")
    lora_dropout: float = Field(default=0.05, description="LoRA dropout rate")
    target_modules: List[str] = Field(default=["q_proj", "v_proj", "k_proj", "o_proj"], description="Target linear layers")
    learning_rate: float = Field(default=2e-4, description="Learning rate")
    batch_size: int = Field(default=4, description="Per device batch size")
    gradient_accumulation_steps: int = Field(default=4, description="Gradient accumulation steps")
    num_epochs: int = Field(default=3, description="Number of training epochs")
    warmup_ratio: float = Field(default=0.05, description="Learning rate warmup ratio")
    weight_decay: float = Field(default=0.01, description="AdamW weight decay")
    optimizer: str = Field(default="adamw_torch", description="Optimizer choice")
    quantization_bits: int = Field(default=4, description="Bits for QLoRA quantization (4 or 8)")

class TrainingJobRequest(BaseModel):
    job_name: str = Field(..., description="Unique human-readable job name")
    base_model: str = Field(default="google/gemma-2b-it", description="HuggingFace base model ID")
    dataset_name: str = Field(default="spider_sample.json", description="Dataset identifier")
    hyperparameters: QLoRAHyperparameters = Field(default_factory=QLoRAHyperparameters)
    description: Optional[str] = Field(None, description="Optional job notes")

class LossPoint(BaseModel):
    step: int
    epoch: float
    train_loss: float
    val_loss: Optional[float] = None
    learning_rate: float
    grad_norm: Optional[float] = None
    timestamp: float

class TrainingJobStatus(BaseModel):
    job_id: str
    job_name: str
    status: str  # "pending", "training", "completed", "failed", "cancelled"
    base_model: str
    dataset_name: str
    current_step: int
    total_steps: int
    current_epoch: float
    total_epochs: int
    train_loss: float
    val_loss: Optional[float] = None
    perplexity: float
    tokens_per_second: float
    eta_seconds: float
    hyperparameters: QLoRAHyperparameters
    loss_history: List[LossPoint] = []
    logs: List[str] = []
    created_at: str
    completed_at: Optional[str] = None
    adapter_checkpoint_path: Optional[str] = None

# --- Serving & Inference Schemas ---
class DatabaseSchemaContext(BaseModel):
    db_id: str = Field(..., description="Database identifier e.g. ecommerce, hr")
    ddl: Optional[str] = Field(None, description="Table DDL creation statements")
    description: Optional[str] = Field(None, description="Description of database domain")

class SQLGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Natural language question to translate to SQL")
    schema_context: Optional[DatabaseSchemaContext] = Field(None, description="Database schema details")
    model_version: Optional[str] = Field(default="active", description="Model checkpoint ID or 'base' or 'active'")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=2048)
    execute_sql: bool = Field(default=True, description="Whether to execute SQL against target database")
    stream: bool = Field(default=False, description="Whether to stream tokens")

class SQLExecutionResult(BaseModel):
    executed: bool
    columns: List[str] = []
    rows: List[List[Any]] = []
    row_count: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None

class SQLSafetyResult(BaseModel):
    allowed: bool
    reason: str
    violations: List[str] = []

class SQLGenerationResponse(BaseModel):
    generation_id: str
    question: str
    generated_sql: str
    formatted_sql: str
    model_used: str
    is_finetuned: bool
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    execution_result: Optional[SQLExecutionResult] = None
    safety_result: Optional[SQLSafetyResult] = None
    confidence_score: float = 0.95


# --- Model Registry Schemas ---
class DeploymentEvent(BaseModel):
    event_id: str
    checkpoint_id: str
    model_name: str
    action: str  # "deploy" or "rollback"
    timestamp: str
    previous_checkpoint_id: Optional[str] = None
    status: str = "success"
    details: Optional[str] = None

class ModelCheckpoint(BaseModel):
    checkpoint_id: str
    name: str
    version: str = "v1.0.0"
    base_model: str
    dataset_used: str
    created_at: str
    deployed_at: Optional[str] = None
    status: str  # "REGISTERED", "READY", "ACTIVE", "FAILED", "ARCHIVED"
    metrics: Dict[str, float] = {}
    hyperparameters: Dict[str, Any] = {}
    path: str
    size_mb: float

class DynamicHotSwapRequest(BaseModel):
    checkpoint_id: str


# --- Dataset Schemas ---
class DatasetItem(BaseModel):
    id: str
    instruction: str
    input: Optional[str] = ""
    output: str
    db_schema: Optional[str] = Field(None, alias="schema")
    db_id: Optional[str] = None
    difficulty: Optional[str] = "medium"

class SQLValidationRequest(BaseModel):
    sql: str
    dialect: str = "sqlite"

class SQLValidationResult(BaseModel):
    valid: bool
    formatted_sql: str
    tables_referenced: List[str] = []
    syntax_error: Optional[str] = None

# --- Evaluation Schemas ---
class EvalItemResult(BaseModel):
    id: str
    question: str
    ground_truth_sql: str
    base_model_sql: str
    finetuned_model_sql: str
    base_exact_match: bool
    finetuned_exact_match: bool
    base_exec_match: bool
    finetuned_exec_match: bool
    base_latency_ms: float
    finetuned_latency_ms: float
    base_error_type: Optional[str] = None
    finetuned_error_type: Optional[str] = None
    failure_category: Optional[str] = None

class BenchmarkRunResponse(BaseModel):
    eval_id: str
    timestamp: str
    dataset_name: str
    checkpoint_id: str
    total_samples: int
    
    # Exact Match Acc
    base_exact_match_acc: float
    finetuned_exact_match_acc: float
    
    # Execution Acc
    base_exec_acc: float
    finetuned_exec_acc: float
    
    # Execution Success / Fail Rates
    base_success_rate: float
    finetuned_success_rate: float
    base_fail_rate: float
    finetuned_fail_rate: float
    
    # Latencies & Percentiles
    base_avg_latency_ms: float
    finetuned_avg_latency_ms: float
    base_p50_latency_ms: float
    finetuned_p50_latency_ms: float
    base_p95_latency_ms: float
    finetuned_p95_latency_ms: float
    base_p99_latency_ms: float
    finetuned_p99_latency_ms: float
    
    failure_analysis: Dict[str, float] = {}
    failure_counts: Dict[str, int] = {}
    details: List[EvalItemResult]



# --- Load & Concurrency Performance Benchmark Schemas ---
class PerformanceBenchmarkRequest(BaseModel):
    num_requests: int = Field(default=20, ge=1, le=500)
    concurrency: int = Field(default=4, ge=1, le=50)
    timeout_seconds: float = Field(default=10.0, ge=1.0)
    dataset_name: str = "spider_sample.json"
    checkpoint_id: str = "forgellm-qlora-v1-spider"
    compare_base: bool = True

class ModelPerformanceMetrics(BaseModel):
    model_name: str
    checkpoint_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    throughput_req_sec: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    success_rate: float
    error_rate: float

class PerformanceBenchmarkResponse(BaseModel):
    benchmark_id: str
    timestamp: str
    dataset_name: str
    num_requests: int
    concurrency: int
    timeout_seconds: float
    total_duration_sec: float
    base_metrics: Optional[ModelPerformanceMetrics] = None
    finetuned_metrics: Optional[ModelPerformanceMetrics] = None
    hardware_notice: str = "ℹ️ Benchmark results are machine-dependent and reflect local hardware performance (Apple Silicon MPS / CPU / RAM)."



# --- MLOps Experiment Tracking Schemas ---
class ExperimentRecord(BaseModel):
    experiment_id: str
    timestamp: str
    job_id: Optional[str] = None
    base_model: str
    checkpoint_id: str
    dataset_name: str
    dataset_size: int
    lora_r: int
    lora_alpha: int
    learning_rate: float
    epochs: int
    batch_size: int
    trainable_parameters: int
    total_parameters: int
    training_time_seconds: float
    final_train_loss: float
    final_val_loss: float
    exact_match_acc: float
    execution_acc: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    is_deployed: bool = False
    deployment_status: Optional[str] = None

class ExperimentComparisonResponse(BaseModel):
    exp1: ExperimentRecord
    exp2: ExperimentRecord
    diff_exact_match_acc: float
    diff_execution_acc: float
    diff_avg_latency_ms: float
    diff_p50_latency_ms: float
    diff_p95_latency_ms: float
    diff_final_val_loss: float




# --- System Metrics ---
class SystemMetricsResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: time.strftime("%H:%M:%S"))
    cpu_usage_percent: float
    process_cpu_percent: float = 0.0
    memory_used_gb: float
    memory_total_gb: float
    memory_usage_percent: float
    process_memory_used_gb: float = 0.0
    gpu_available: bool
    gpu_name: str
    gpu_memory_used_gb: float
    gpu_memory_total_gb: float
    active_model: str
    active_requests_per_sec: float
    uptime_seconds: float
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0

class SystemTelemetryPoint(BaseModel):
    time: str
    cpu_usage_percent: float
    memory_usage_percent: float
    gpu_memory_used_gb: float
    active_requests_per_sec: float


class SystemMetricsHistoryResponse(BaseModel):
    history: List[SystemTelemetryPoint]

