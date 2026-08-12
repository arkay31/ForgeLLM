import json
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.config import settings
from app.models.schemas import SQLValidationRequest, SQLValidationResult
from app.services.schema_engine import schema_engine

router = APIRouter(prefix="/datasets", tags=["Datasets & SQL Tools"])

@router.get("")
async def list_datasets():
    """Lists available datasets and database schemas."""
    data_dir = settings.BASE_DIR / "backend" / "app" / "data"
    files = list(data_dir.glob("*.json"))
    
    result = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fn:
            items = json.load(fn)
            result.append({
                "dataset_name": f.name,
                "path": str(f),
                "total_pairs": len(items),
                "domains": list(set(i.get("db_id", "unknown") for i in items))
            })
    
    databases = schema_engine.get_database_list()
    return {"datasets": result, "supported_databases": databases}

@router.get("/{dataset_name}/samples")
async def get_dataset_samples(dataset_name: str):
    """Returns sample prompt-SQL pairs for inspection."""
    data_file = settings.BASE_DIR / "backend" / "app" / "data" / dataset_name
    if not data_file.exists():
        data_file = settings.BASE_DIR / "backend" / "app" / "data" / "spider_sample.json"
    
    with open(data_file, "r", encoding="utf-8") as f:
        items = json.load(f)
    return items

@router.post("/validate-sql", response_model=SQLValidationResult)
async def validate_sql(req: SQLValidationRequest):
    """Lints, formats, and validates SQL syntax using sqlglot AST parser."""
    valid, formatted, err, tables = schema_engine.format_and_validate_sql(req.sql)
    return SQLValidationResult(
        valid=valid,
        formatted_sql=formatted,
        tables_referenced=tables,
        syntax_error=err
    )

@router.post("/prepare")
async def trigger_data_preparation(dataset: str = "spider", format_type: str = "gemma"):
    """Triggers dataset download, cleaning, deduplication, JSONL formatting, and validation suite."""
    from scripts.prepare_dataset import download_or_load_dataset, clean_and_deduplicate, split_dataset, export_jsonl, validate_dataset_quality
    from app.config import settings
    
    raw_dir = settings.STORAGE_DIR / "datasets" / "raw"
    out_dir = settings.STORAGE_DIR / "datasets" / "processed" / dataset
    
    raw_items = download_or_load_dataset(dataset, raw_dir)
    cleaned_items = clean_and_deduplicate(raw_items)
    train_data, val_data, test_data = split_dataset(cleaned_items)
    
    export_jsonl(train_data, format_type, out_dir / "train.jsonl")
    export_jsonl(val_data, format_type, out_dir / "val.jsonl")
    export_jsonl(test_data, format_type, out_dir / "test.jsonl")
    
    report = validate_dataset_quality(cleaned_items)
    return {
        "status": "success",
        "dataset": dataset,
        "format": format_type,
        "splits": {"train": len(train_data), "val": len(val_data), "test": len(test_data)},
        "validation_report": report
    }
