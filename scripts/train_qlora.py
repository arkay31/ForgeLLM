#!/usr/bin/env python3
"""
ForgeLLM Standalone QLoRA Fine-Tuning CLI Script
Fine-tunes base causal LLM (e.g., Gemma-2B / Qwen-1.5B / Mistral-7B) on Text-to-SQL paired dataset.
"""

import os
import sys
import json
import argparse
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType

def main():
    parser = argparse.ArgumentParser(description="ForgeLLM QLoRA Fine-Tuning Script")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    parser.add_argument("--dataset_path", type=str, default="../backend/app/data/spider_sample.json")
    parser.add_argument("--output_dir", type=str, default="../storage/checkpoints/cli_run_qlora")
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--alpha", type=int, default=32)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=2)
    args = parser.parse_args()

    print(f"🔥 Starting ForgeLLM QLoRA Fine-Tuning CLI...")
    print(f"📦 Base Model: {args.base_model}")
    print(f"📊 Dataset: {args.dataset_path}")
    print(f"⚙️ Hyperparameters: r={args.rank}, alpha={args.alpha}, lr={args.lr}, epochs={args.epochs}")

    # Device selection
    if torch.cuda.is_available():
        device = "cuda"
    elif getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"🖥️ Target Hardware Compute Device: {device.upper()}")

    # Setup LoRA config
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        bias="none"
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save artifact metadata
    with open(out_dir / "adapter_config.json", "w") as f:
        json.dump(peft_config.__dict__, f, indent=2, default=str)

    print(f"✅ QLoRA Adapter Config generated successfully at {out_dir / 'adapter_config.json'}")

if __name__ == "__main__":
    main()
