import pytest
from app.services.eval_service import eval_service
from app.services.schema_engine import schema_engine


def test_benchmark_exact_match_ast_normalization():
    """Verify AST-based SQL normalization for Exact Match evaluation."""
    sql1 = "SELECT singer_id, name FROM singer WHERE age > 25 ORDER BY age DESC;"
    sql2 = "   select singer_id, name  from  singer  where  age > 25  order by age desc  "
    sql_diff = "SELECT singer_id, name FROM singer WHERE age > 30 ORDER BY age DESC;"


    assert eval_service._normalize_sql(sql1) == eval_service._normalize_sql(sql2)
    assert eval_service._normalize_sql(sql1) != eval_service._normalize_sql(sql_diff)


def test_ast_failure_classification():
    """Verify sqlglot AST deterministic failure classification into categories."""
    gt_sql_join = "SELECT singer_id, name FROM singer JOIN concert ON singer.id = concert.id WHERE age > 25 ORDER BY age DESC LIMIT 5;"
    gt_sql_single = "SELECT singer_id, name FROM singer WHERE age > 25 ORDER BY age DESC LIMIT 5;"

    # 1. Missing JOIN
    assert eval_service.classify_sql_failure(gt_sql_join, "SELECT singer_id, name FROM singer WHERE age > 25 ORDER BY age DESC LIMIT 5;") == "missing JOIN"

    # 2. Wrong Table
    assert eval_service.classify_sql_failure(gt_sql_single, "SELECT singer_id, name FROM wrong_table WHERE age > 25 ORDER BY age DESC LIMIT 5;") == "wrong table"

    # 3. Wrong Column
    assert eval_service.classify_sql_failure(gt_sql_single, "SELECT wrong_col FROM singer WHERE age > 25 ORDER BY age DESC LIMIT 5;") == "wrong column"

    # 4. Incorrect WHERE/filter
    assert eval_service.classify_sql_failure(gt_sql_single, "SELECT singer_id, name FROM singer WHERE age > 50 ORDER BY age DESC LIMIT 5;") == "incorrect WHERE/filter"

    # 5. Incorrect LIMIT
    assert eval_service.classify_sql_failure(gt_sql_single, "SELECT singer_id, name FROM singer WHERE age > 25 ORDER BY age DESC LIMIT 100;") == "incorrect LIMIT"

    # 6. Syntax Error
    assert eval_service.classify_sql_failure(gt_sql_single, "SELECT FROM WHERE ;;;") == "syntax error"




def test_benchmark_execution_accuracy_matching_rows():
    """Verify semantic execution result set comparison."""
    gt_sql = "SELECT singer_id, name FROM singer ORDER BY singer_id;"
    model_sql = "SELECT singer_id, name FROM singer ORDER BY singer_id;"
    diff_sql = "SELECT singer_id, name FROM singer WHERE age > 100;"

    expected = schema_engine.execute_query("concert_singer", gt_sql)
    actual_matching = schema_engine.execute_query("concert_singer", model_sql)
    actual_diff = schema_engine.execute_query("concert_singer", diff_sql)

    matched, err_type = eval_service._result_sets_match(gt_sql, expected, actual_matching)
    assert matched is True
    assert err_type is None

    matched_diff, err_diff = eval_service._result_sets_match(gt_sql, expected, actual_diff)
    assert matched_diff is False


def test_benchmark_execution_accuracy_empty_result_sets():
    """Verify execution accuracy matching when queries return empty result sets."""
    gt_sql = "SELECT * FROM singer WHERE country = 'NonExistentCountry1';"
    model_sql = "SELECT * FROM singer WHERE country = 'NonExistentCountry2';"

    expected = schema_engine.execute_query("concert_singer", gt_sql)
    actual = schema_engine.execute_query("concert_singer", model_sql)

    matched, err_type = eval_service._result_sets_match(gt_sql, expected, actual)
    assert matched is True
    assert err_type is None


def test_benchmark_execution_accuracy_failed_sql_execution():
    """Verify handling failed model query execution during benchmark."""
    gt_sql = "SELECT singer_id FROM singer;"
    broken_sql = "SELECT non_existent_column_xyz FROM singer;"

    expected = schema_engine.execute_query("concert_singer", gt_sql)
    actual = schema_engine.execute_query("concert_singer", broken_sql)

    matched, err_type = eval_service._result_sets_match(gt_sql, expected, actual)
    assert matched is False
    assert err_type is not None


def test_benchmark_latency_percentile_statistics():
    """Verify latency calculation metrics (Avg, P50, P95, P99)."""
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

    p50 = eval_service._calculate_percentile(latencies, 50)
    p95 = eval_service._calculate_percentile(latencies, 95)
    p99 = eval_service._calculate_percentile(latencies, 99)

    assert 50.0 <= p50 <= 60.0
    assert p95 > p50
    assert p99 >= p95


@pytest.mark.anyio
async def test_full_benchmark_run_pipeline():
    """Verify full end-to-end evaluation benchmark pipeline."""
    res = await eval_service.run_benchmark(
        dataset_name="spider_sample.json",
        checkpoint_id="forgellm-qlora-v1-spider",
        limit=3,
    )

    assert res.total_samples == 3
    assert 0.0 <= res.base_exact_match_acc <= 1.0
    assert 0.0 <= res.finetuned_exact_match_acc <= 1.0
    assert 0.0 <= res.base_exec_acc <= 1.0
    assert 0.0 <= res.finetuned_exec_acc <= 1.0
    assert len(res.details) == 3
