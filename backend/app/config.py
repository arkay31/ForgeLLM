import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
CHECKPOINT_DIR = STORAGE_DIR / "checkpoints"
DATASET_DIR = STORAGE_DIR / "datasets"
MODEL_DIR = STORAGE_DIR / "models"

# Ensure directories exist
for folder in [STORAGE_DIR, CHECKPOINT_DIR, DATASET_DIR, MODEL_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    APP_NAME: str = "ForgeLLM"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("FORGELLM_ENV", os.getenv("ENVIRONMENT", "development"))
    API_PREFIX: str = "/api/v1"
    
    # Security & CORS
    ADMIN_API_KEY: str = os.getenv("FORGE_API_KEY", "forge-secret-key-2026-prod")
    RATE_LIMIT_PER_MINUTE: int = 60
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    )
    
    # Models & Paths
    DEFAULT_BASE_MODEL: str = os.getenv("FORGELLM_BASE_MODEL", os.getenv("DEFAULT_BASE_MODEL", "Qwen/Qwen2.5-Coder-1.5B-Instruct"))
    DEFAULT_DATASET: str = "spider_sample.json"
    
    # Real Inference / Demo Mode Configuration
    # Options: "demo" or "real"
    INFERENCE_MODE: str = os.getenv("FORGELLM_INFERENCE_MODE", os.getenv("INFERENCE_MODE", "demo"))
    TRAINING_MODE: str = os.getenv("FORGELLM_TRAINING_MODE", os.getenv("TRAINING_MODE", "real"))
    DEVICE: str = os.getenv("FORGELLM_DEVICE", os.getenv("DEVICE", "auto"))

    BASE_DIR: Path = BASE_DIR
    CHECKPOINT_DIR: Path = CHECKPOINT_DIR
    DATASET_DIR: Path = DATASET_DIR
    MODEL_DIR: Path = MODEL_DIR

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return ["http://localhost:5173"]
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()



