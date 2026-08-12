import pytest
from app.models.schemas import SQLGenerationRequest, DatabaseSchemaContext
from app.services.inference_engine import inference_engine
from app.services.registry_service import registry_service


@pytest.mark.anyio
async def test_inference_request_schema_and_prompt_builder():
    """Verify inference request construction and prompt formatting."""
    ctx = DatabaseSchemaContext(
        db_id="ecommerce_store",
        ddl="CREATE TABLE customers (customer_id INT, country TEXT);",
    )
    req = SQLGenerationRequest(
        prompt="Find all customers in Canada",
        schema_context=ctx,
        model_version="active",
        execute_sql=True,
    )

    assert req.prompt == "Find all customers in Canada"
    assert req.model_version == "active"
    assert req.execute_sql is True
    assert req.schema_context.db_id == "ecommerce_store"

    prompt, db_id = inference_engine._build_prompt(req)
    assert "Find all customers in Canada" in prompt
    assert "CREATE TABLE customers" in prompt
    assert db_id == "ecommerce_store"


@pytest.mark.anyio
async def test_inference_model_selection_base_vs_checkpoint():
    """Verify inference engine dispatches to requested model checkpoint."""
    ctx = DatabaseSchemaContext(db_id="concert_singer", ddl="CREATE TABLE singer (singer_id INT, name TEXT);")

    # 1. Base Model Selection
    req_base = SQLGenerationRequest(
        prompt="List all singers",
        schema_context=ctx,
        model_version="base",
        execute_sql=True,
    )
    res_base = await inference_engine.generate_sql(req_base)
    assert res_base.is_finetuned is False
    assert "Base" in res_base.model_used
    assert res_base.execution_result is not None

    # 2. Active Fine-Tuned Model Selection
    active_cp = registry_service.get_active_checkpoint()
    req_ft = SQLGenerationRequest(
        prompt="List all singers",
        schema_context=ctx,
        model_version=active_cp.checkpoint_id,
        execute_sql=True,
    )
    res_ft = await inference_engine.generate_sql(req_ft)
    assert res_ft.execution_result is not None

