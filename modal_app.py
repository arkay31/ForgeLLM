import os
import sys
from pathlib import Path
import modal

# -----------------------------------------------------------------------------
# Modal App & Image Specification
# -----------------------------------------------------------------------------
app = modal.App("forgellm-backend")

# Step function to pre-download base model during image build (avoids runtime cold-start download)
def download_base_model():
    from transformers import AutoTokenizer, AutoModelForCausalLM
    model_name = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    print(f"📦 Pre-downloading base model '{model_name}' into Modal image cache...")
    AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)


# Define Linux container image with PyTorch CUDA & dependencies
# NOTE: All build steps (.pip_install, .run_function) MUST occur BEFORE .add_local_dir
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch",
        "transformers>=4.40.0",
        "peft>=0.10.0",
        "sqlglot>=23.0.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.28.0",
        "psutil>=5.9.0",
        "pydantic>=2.6.0",
        "pydantic-settings>=2.2.0",
        "prometheus_client>=0.20.0",
        "requests>=2.31.0",
        "accelerate>=0.28.0",
        "safetensors>=0.4.0",
        "httpx>=0.27.0",
    )
    # Pre-download Qwen base model during image build BEFORE adding local directories
    .run_function(download_base_model)
    # Package backend application source code & target SQLite database seeds LAST
    .add_local_dir("backend", remote_path="/app/backend")
    # Package storage directory containing PEFT adapter artifacts & experiment metadata LAST
    .add_local_dir("storage", remote_path="/app/storage")
)


# -----------------------------------------------------------------------------
# Serverless GPU Service Class
# -----------------------------------------------------------------------------
@app.cls(
    gpu="T4",  # Cost-effective NVIDIA T4 GPU (16GB VRAM) suitable for 1.5B PEFT LLM
    image=image,
    scaledown_window=300,  # 5 min idle timeout for cost control
    min_containers=0,  # Scale to 0 when idle to eliminate idle costs
)
class ForgeLLMServer:
    @modal.enter()
    def setup(self):
        """Executes once per GPU container initialization to load model weights into VRAM."""
        sys.path.insert(0, "/app/backend")

        # Set environment for production real GPU inference
        os.environ["FORGELLM_ENV"] = "production"
        os.environ["FORGELLM_INFERENCE_MODE"] = "real"
        os.environ["FORGELLM_DEVICE"] = "cuda"
        os.environ["FORGELLM_BASE_MODEL"] = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

        from app.config import settings
        settings.INFERENCE_MODE = "real"
        settings.DEVICE = "cuda"

        from app.services.model_manager import model_manager
        from app.services.registry_service import registry_service

        active_cp = registry_service.get_checkpoint("job-e6d16293")
        adapter_path = active_cp.path if (active_cp and active_cp.path) else "/app/storage/checkpoints/job-e6d16293"

        print(f"🚀 [Modal Container Setup] Pre-loading Base Model + PEFT Adapter onto CUDA GPU...")
        model_manager.load_model(
            base_model_name="Qwen/Qwen2.5-Coder-1.5B-Instruct",
            checkpoint_id="job-e6d16293",
            adapter_path=adapter_path,
        )
        print(f"✅ [Modal Container Setup] Model successfully cached on device: {model_manager.device}")

    @modal.asgi_app()
    def fastapi_app(self):
        """Serves the complete FastAPI web application as a Modal web endpoint."""
        sys.path.insert(0, "/app/backend")
        from app.main import app as fastapi_application
        return fastapi_application
