import gc
import logging
import os
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import torch
from app.config import settings

logger = logging.getLogger("ForgeLLM.ModelManager")
logging.basicConfig(level=logging.INFO)


class LocalModelManager:
    """
    Manages local LLM model and adapter loading for Text-to-SQL inference.
    Implements a load-once-and-reuse caching strategy to avoid reloading
    large weights on every HTTP request.
    Supports Apple Silicon (MPS) and CPU execution.
    """

    def __init__(self):
        self.current_base_model_name: Optional[str] = None
        self.current_checkpoint_id: Optional[str] = None
        self.current_adapter_path: Optional[str] = None

        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.device: Optional[torch.device] = None
        self.torch_dtype: Optional[torch.dtype] = None
        
        self.last_load_time_ms: float = 0.0
        self.load_error: Optional[str] = None

        self._determine_device()

    def _determine_device(self):
        requested_device = settings.DEVICE.lower()

        if requested_device == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.torch_dtype = torch.float16
            logger.info("⚡ NVIDIA CUDA GPU detected and active.")
        elif requested_device == "mps" and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            self.device = torch.device("mps")
            self.torch_dtype = torch.float16
            logger.info("🍏 Apple Silicon MPS (Metal Performance Shaders) detected and active.")
        elif requested_device == "cpu":
            self.device = torch.device("cpu")
            self.torch_dtype = torch.float32
            logger.info("💻 CPU device active for PyTorch inference.")
        else:
            # Auto detection: CUDA > MPS > CPU
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                self.torch_dtype = torch.float16
                logger.info("⚡ NVIDIA CUDA GPU detected and active.")
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                self.device = torch.device("mps")
                self.torch_dtype = torch.float16
                logger.info("🍏 Apple Silicon MPS (Metal Performance Shaders) detected and active.")
            else:
                self.device = torch.device("cpu")
                self.torch_dtype = torch.float32
                logger.info("💻 CPU device active for PyTorch inference.")


    def load_model(
        self,
        base_model_name: str,
        checkpoint_id: str,
        adapter_path: Optional[str] = None,
    ) -> Tuple[Any, Any]:
        """
        Loads base model and tokenizer (and optional PEFT adapter).
        If the model is already loaded in memory, returns immediately.
        """
        # Check if already cached in memory
        if (
            self.model is not None
            and self.tokenizer is not None
            and self.current_base_model_name == base_model_name
            and self.current_checkpoint_id == checkpoint_id
        ):
            return self.model, self.tokenizer

        start_time = time.time()
        logger.info(f"🔄 Loading model: base='{base_model_name}', checkpoint='{checkpoint_id}', adapter='{adapter_path}'...")

        try:
            # Import transformers & peft dynamically to prevent startup slowdown if unused
            from transformers import AutoTokenizer, AutoModelForCausalLM
            from peft import PeftModel

            # Unload previous model from RAM/VRAM if changing
            self.unload_model()

            # 1. Load Tokenizer
            logger.info(f"Downloading/Loading tokenizer for '{base_model_name}'...")
            tokenizer = AutoTokenizer.from_pretrained(
                base_model_name,
                trust_remote_code=True,
            )
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # 2. Load Base Model
            logger.info(f"Downloading/Loading base model weights for '{base_model_name}' on {self.device}...")
            model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                dtype=self.torch_dtype,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )


            # Move model to selected device (MPS or CPU)
            model = model.to(self.device)

            # 3. Load PEFT Adapter if available
            has_real_adapter = False
            if adapter_path:
                adapter_dir = Path(adapter_path)
                # Verify real adapter weight binary exists
                weights_exist = (
                    (adapter_dir / "adapter_model.safetensors").exists()
                    or (adapter_dir / "adapter_model.bin").exists()
                )
                if weights_exist:
                    logger.info(f"Attaching real PEFT LoRA adapter from '{adapter_path}'...")
                    model = PeftModel.from_pretrained(model, adapter_path)
                    has_real_adapter = True
                else:
                    logger.info(f"Adapter dir '{adapter_path}' contains config metadata but no weight tensors. Operating with base model.")

            model.eval()

            # Cache in singleton state
            self.model = model
            self.tokenizer = tokenizer
            self.current_base_model_name = base_model_name
            self.current_checkpoint_id = checkpoint_id
            self.current_adapter_path = adapter_path if has_real_adapter else None
            self.load_error = None

            self.last_load_time_ms = round((time.time() - start_time) * 1000, 2)
            logger.info(f"✅ Model loaded successfully in {self.last_load_time_ms} ms!")
            return self.model, self.tokenizer

        except Exception as e:
            self.load_error = str(e)
            logger.error(f"❌ Failed to load model '{base_model_name}': {e}", exc_info=True)
            self.unload_model()
            raise e

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
    ) -> Tuple[str, float, int, int]:
        """
        Executes model text generation.
        Returns: (generated_text, generation_time_ms, prompt_tokens, completion_tokens)
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model is not loaded. Call load_model() first.")

        start_time = time.time()

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        prompt_tokens = inputs.input_ids.shape[1]

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if temperature > 0.0 else 0.01,
                do_sample=temperature > 0.0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Slice generated output tokens (excluding prompt)
        generated_ids = outputs[0][prompt_tokens:]
        completion_tokens = len(generated_ids)
        generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        gen_time_ms = round((time.time() - start_time) * 1000, 2)
        return generated_text, gen_time_ms, prompt_tokens, completion_tokens

    def unload_model(self):
        """Frees GPU / RAM memory."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None

        self.current_base_model_name = None
        self.current_checkpoint_id = None
        self.current_adapter_path = None

        gc.collect()
        if getattr(torch, "mps", None) and hasattr(torch.mps, "empty_cache"):
            try:
                torch.mps.empty_cache()
            except Exception:
                pass


model_manager = LocalModelManager()
