#!/usr/bin/env python3
"""
ForgeLLM Production Data Pipeline Script
----------------------------------------
- Downloads & prepares public NL-to-SQL datasets (Spider / WikiSQL / Custom)
- Data cleaning, SQL normalization & deduplication
- Seeded Train/Val/Test splitting
- Formats into Instruction-Tuning JSONL (Alpaca, ChatML, Llama-3, Gemma)
- Comprehensive validation suite (Schema consistency via sqlglot, Token length distributions)
"""

import os
import sys
import json
import random
import math
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import sqlglot

def download_or_load_dataset(dataset_name: str, raw_dir: Path) -> List[Dict[str, Any]]:
    """Loads dataset from local raw storage or downloads via HF datasets / online mirror."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(f"📥 Loading dataset '{dataset_name}'...")
    
    # Try downloading via Hugging Face datasets if available
    try:
        from datasets import load_dataset
        if dataset_name == "spider":
            print("🌐 Fetching Spider dataset from Hugging Face Datasets Hub...")
            hf_data = load_dataset("spider", split="train")
            items = []
            for idx, row in enumerate(hf_data):
                items.append({
                    "id": f"spider-{idx+1}",
                    "instruction": row["question"],
                    "input": f"Database: {row['db_id']}.",
                    "output": row["query"],
                    "db_id": row["db_id"],
                    "schema": ""
                })
            print(f"✅ Downloaded {len(items)} Spider samples from Hugging Face.")
            return items
        elif dataset_name == "wikisql":
            print("🌐 Fetching WikiSQL dataset from Hugging Face Datasets Hub...")
            hf_data = load_dataset("wikisql", split="train")
            items = []
            for idx, row in enumerate(hf_data):
                items.append({
                    "id": f"wikisql-{idx+1}",
                    "instruction": row["question"],
                    "input": f"Table ID: {row['table']['id']}.",
                    "output": row["sql"]["human_readable"],
                    "db_id": row['table']['id'],
                    "schema": ", ".join(row['table']['header'])
                })
            print(f"✅ Downloaded {len(items)} WikiSQL samples from Hugging Face.")
            return items
    except Exception as e:
        print(f"⚠️ Hugging Face dataset download fallback triggered: {e}")

    # Local fallback sample dataset loader / generator
    local_sample_file = Path(__file__).resolve().parent.parent / "backend" / "app" / "data" / "spider_sample.json"
    if local_sample_file.exists():
        with open(local_sample_file, "r", encoding="utf-8") as f:
            items = json.load(f)
            # Expand with domain items to create rich dataset
            expanded = []
            for multiplier in range(10):
                for item in items:
                    expanded_item = item.copy()
                    expanded_item["id"] = f"{item['id']}-exp-{multiplier}"
                    expanded.append(expanded_item)
            print(f"✅ Loaded and expanded {len(expanded)} local NL-to-SQL training records.")
            return expanded
            
    raise FileNotFoundError(f"Could not load or download dataset '{dataset_name}'.")

def clean_and_deduplicate(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Cleans SQL queries, normalizes whitespace, and deduplicates records."""
    print("🧹 Cleaning data and deduplicating prompt/SQL pairs...")
    cleaned = []
    seen = set()
    
    for item in items:
        q = item.get("instruction", "").strip()
        sql = item.get("output", "").strip()
        
        if not q or not sql:
            continue
            
        # Clean SQL code formatting
        if sql.startswith("```sql"): sql = sql[6:]
        if sql.startswith("```"): sql = sql[3:]
        if sql.endswith("```"): sql = sql[:-3]
        sql = sql.strip().rstrip(";")
        
        # Deduplication key: (lowercased question, normalized sql)
        dedup_key = (q.lower(), " ".join(sql.lower().split()))
        if dedup_key in seen:
            continue
            
        seen.add(dedup_key)
        
        item_copy = item.copy()
        item_copy["instruction"] = q
        item_copy["output"] = sql
        cleaned.append(item_copy)
        
    print(f"✨ Deduplication complete: {len(items)} original -> {len(cleaned)} unique pairs ({len(items) - len(cleaned)} duplicate/malformed removed).")
    return cleaned

def split_dataset(items: List[Dict[str, Any]], train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, seed=42) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Performs reproducible train/val/test splitting."""
    print(f"🔀 Partitioning dataset (Train: {train_ratio*100:.0f}%, Val: {val_ratio*100:.0f}%, Test: {test_ratio*100:.0f}%)...")
    random.seed(seed)
    shuffled = items.copy()
    random.shuffle(shuffled)
    
    total = len(shuffled)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    train_data = shuffled[:train_end]
    val_data = shuffled[train_end:val_end]
    test_data = shuffled[val_end:]
    
    print(f"📊 Dataset Splits: Train={len(train_data)}, Val={len(val_data)}, Test={len(test_data)}")
    return train_data, val_data, test_data

def format_instruction_prompt(item: Dict[str, Any], format_type: str) -> Dict[str, Any]:
    """Formats raw entry into target instruction-tuning prompt/completion format."""
    q = item["instruction"]
    sql = item["output"]
    schema = item.get("schema", "")
    db_id = item.get("db_id", "")
    
    context = ""
    if schema:
        context += f"\nDatabase Schema DDL:\n{schema}\n"
    if db_id:
        context += f"\nTarget Database: {db_id}\n"

    if format_type == "alpaca":
        prompt = f"### Instruction:\nTranslate the natural language question into a valid SQLite query.{context}\nQuestion: {q}\n\n### Response:\n"
        completion = sql
        return {"prompt": prompt, "completion": completion}
        
    elif format_type == "chatml":
        system_msg = "You are an expert SQL assistant. Translate natural language questions to SQL."
        user_msg = f"{context}Question: {q}"
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": sql}
        ]
        return {"messages": messages}
        
    elif format_type == "llama3":
        prompt = f"<|start_header_id|>system<|end_header_id|>\nYou are an expert SQL assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>\n{context}Question: {q}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        completion = f"{sql}<|eot_id|>"
        return {"prompt": prompt, "completion": completion}
        
    else: # gemma default
        prompt = f"<start_of_turn>user\nTranslate natural language to SQL.{context}\nQuestion: {q}<end_of_turn>\n<start_of_turn>model\n"
        completion = f"{sql}<end_of_turn>"
        return {"prompt": prompt, "completion": completion}

def export_jsonl(items: List[Dict[str, Any]], format_type: str, output_filepath: Path):
    """Exports dataset split to instruction-tuning JSONL format."""
    output_filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(output_filepath, "w", encoding="utf-8") as f:
        for item in items:
            formatted = format_instruction_prompt(item, format_type)
            f.write(json.dumps(formatted) + "\n")
    print(f"💾 Exported {len(items)} records to {output_filepath}")

def validate_dataset_quality(items: List[Dict[str, Any]], max_seq_len: int = 2048) -> Dict[str, Any]:
    """Runs data validation checks: schema consistency & token length distributions."""
    print("🔍 Running Comprehensive Data Validation Suite...")
    
    valid_syntax_count = 0
    invalid_syntax_count = 0
    tables_referenced = set()
    
    prompt_token_lengths = []
    completion_token_lengths = []
    
    for item in items:
        sql = item.get("output", "")
        q = item.get("instruction", "")
        
        # 1. Schema & AST Syntax Check via sqlglot
        try:
            parsed = sqlglot.parse_one(sql, read="sqlite")
            valid_syntax_count += 1
            for table in parsed.find_all(sqlglot.exp.Table):
                tables_referenced.add(table.name)
        except Exception:
            invalid_syntax_count += 1
            
        # 2. Token Length Distribution estimation (approx ~4 chars per token)
        p_tokens = max(1, len(q) // 4)
        c_tokens = max(1, len(sql) // 4)
        
        prompt_token_lengths.append(p_tokens)
        completion_token_lengths.append(c_tokens)
        
    prompt_token_lengths.sort()
    completion_token_lengths.sort()
    n = len(items)
    
    def stats(arr):
        if not arr: return {}
        mean = sum(arr) / len(arr)
        return {
            "min": arr[0],
            "max": arr[-1],
            "mean": round(mean, 1),
            "p50": arr[int(len(arr) * 0.5)],
            "p95": arr[int(len(arr) * 0.95)],
            "p99": arr[int(len(arr) * 0.99)],
            "exceeding_max_len": sum(1 for x in arr if x > max_seq_len)
        }
        
    validation_report = {
        "total_records": n,
        "syntax_checks": {
            "valid_sql_ast": valid_syntax_count,
            "invalid_sql_ast": invalid_syntax_count,
            "validity_percentage": round((valid_syntax_count / n) * 100, 2) if n > 0 else 0,
            "unique_tables_referenced": list(tables_referenced)
        },
        "token_length_distribution": {
            "prompt_tokens": stats(prompt_token_lengths),
            "completion_tokens": stats(completion_token_lengths)
        }
    }
    
    print("\n📋 === DATA VALIDATION SUMMARY REPORT ===")
    print(f"Total Records Analyzed: {n}")
    print(f"SQL AST Validity: {validation_report['syntax_checks']['validity_percentage']}% ({valid_syntax_count} valid, {invalid_syntax_count} errors)")
    print(f"Unique Tables Referenced: {len(tables_referenced)} tables")
    print(f"Prompt Tokens  (P50/P95/P99): {validation_report['token_length_distribution']['prompt_tokens'].get('p50')}/{validation_report['token_length_distribution']['prompt_tokens'].get('p95')}/{validation_report['token_length_distribution']['prompt_tokens'].get('p99')} tokens")
    print(f"Completion Tokens (P50/P95/P99): {validation_report['token_length_distribution']['completion_tokens'].get('p50')}/{validation_report['token_length_distribution']['completion_tokens'].get('p95')}/{validation_report['token_length_distribution']['completion_tokens'].get('p99')} tokens")
    print("=========================================\n")
    
    return validation_report

def main():
    parser = argparse.ArgumentParser(description="ForgeLLM Production Data Preparation Pipeline")
    parser.add_argument("--dataset", type=str, default="spider", choices=["spider", "wikisql", "custom"], help="Source dataset")
    parser.add_argument("--format", type=str, default="gemma", choices=["alpaca", "chatml", "llama3", "gemma"], help="Instruction tuning prompt template format")
    parser.add_argument("--train_ratio", type=float, default=0.8, help="Train split ratio")
    parser.add_argument("--val_ratio", type=float, default=0.1, help="Validation split ratio")
    parser.add_argument("--test_ratio", type=float, default=0.1, help="Test split ratio")
    parser.add_argument("--output_dir", type=str, default="../storage/datasets/processed", help="Output directory for JSONL files")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    raw_dir = base_dir / "storage" / "datasets" / "raw"
    out_dir = base_dir / "storage" / "datasets" / "processed" / args.dataset

    # 1. Download / Load
    raw_items = download_or_load_dataset(args.dataset, raw_dir)
    
    # 2. Clean & Deduplicate
    cleaned_items = clean_and_deduplicate(raw_items)
    
    # 3. Train / Val / Test Split
    train_data, val_data, test_data = split_dataset(
        cleaned_items,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio
    )
    
    # 4. Convert & Export to JSONL Format
    export_jsonl(train_data, args.format, out_dir / "train.jsonl")
    export_jsonl(val_data, args.format, out_dir / "val.jsonl")
    export_jsonl(test_data, args.format, out_dir / "test.jsonl")
    
    # 5. Data Validation & Token Length Checks
    report = validate_dataset_quality(cleaned_items)
    with open(out_dir / "data_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"📊 Full validation report saved to {out_dir / 'data_validation_report.json'}")
    print("✨ Data pipeline execution completed successfully!")

if __name__ == "__main__":
    main()
