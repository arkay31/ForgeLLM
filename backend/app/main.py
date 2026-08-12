import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings, STORAGE_DIR
from app.api import (
    routes_fine_tune,
    routes_serve,
    routes_models,
    routes_datasets,
    routes_eval,
    routes_system,
    routes_feedback,
    routes_experiments
)

from app.services.model_manager import model_manager
from app.services.registry_service import registry_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup initialization
    print(f"🚀 [ForgeLLM v{settings.VERSION}] Platform Engine starting...")
    print(f"📁 Storage Dir: {STORAGE_DIR}")
    print(f"⚙️  Inference Mode: {settings.INFERENCE_MODE}")
    print(f"🔑 Admin API Key Active: {settings.ADMIN_API_KEY[:8]}...")
    yield
    print("🛑 [ForgeLLM] Platform Engine shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-Grade LLM Fine-Tuning & Serving Platform for Text-to-SQL",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for explicit allowed origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api/v1
prefix = settings.API_PREFIX
app.include_router(routes_system.router, prefix=prefix)
app.include_router(routes_fine_tune.router, prefix=prefix)
app.include_router(routes_serve.router, prefix=prefix)
app.include_router(routes_models.router, prefix=prefix)
app.include_router(routes_datasets.router, prefix=prefix)
app.include_router(routes_eval.router, prefix=prefix)
app.include_router(routes_feedback.router, prefix=prefix)
app.include_router(routes_experiments.router, prefix=prefix)


# Root Endpoint
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
        "api_prefix": settings.API_PREFIX
    }


@app.get("/health")
async def health():
    """Lightweight deployment health check (does NOT load model weights)."""
    device_str = str(getattr(model_manager, "device", None) or settings.DEVICE)
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "inference_mode": settings.INFERENCE_MODE,
        "device": device_str,
    }


@app.get("/ready")
async def readiness():
    """Deployment readiness check reporting model cache status."""
    is_loaded = (model_manager.model is not None and model_manager.tokenizer is not None)
    device_str = str(getattr(model_manager, "device", None) or settings.DEVICE)
    return {
        "status": "ready" if is_loaded else "initializing",
        "model_loaded": is_loaded,
        "active_base_model": model_manager.current_base_model_name or settings.DEFAULT_BASE_MODEL,
        "active_checkpoint_id": model_manager.current_checkpoint_id or registry_service.active_checkpoint_id,
        "adapter_path": model_manager.current_adapter_path,
        "device": device_str,
    }

