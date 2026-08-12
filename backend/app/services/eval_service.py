import json
import logging
import math
import uuid
import time
from datetime import datetime, timezone

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import sqlglot
from app.config import settings, STORAGE_DIR, BASE_DIR
from app.models.schemas import (
    BenchmarkRunResponse,
    EvalItemResult,
    SQLGenerationRequest,
    DatabaseSchemaContext,
)
from app.services.inference_engine import inference_engine
from app.services.schema_engine import schema_engine

logger = logging.getLogger("ForgeLLM.EvalService")


class EvalService:
    """
    Rigorous, scientifically honest Text-to-SQL evaluation and benchmarking service.
    Computes: Exact Match (EM), Execution Accuracy (EX), Success/Fail rates,
    Average Latency, P50, P95, P99 Latency percentiles, and Case-by-Case Error Types.
    """

    def __init__(self):
        self.history_file = STORAGE_DIR / "eval_history.json"
        self.history: List[BenchmarkRunResponse] = []
        self._load_history()


    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for run_dict in data:
                        self.history.append(BenchmarkRunResponse(**run_dict))
            except Exception as e:
                logger.warning(f"Failed to load evaluation history: {e}")

    def _save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([h.model_dump() for h in self.history], f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save evaluation history: {e}")


    @staticmethod
    def _normalize_sql(sql: str) -> str:
        """
        Normalize SQL query using sqlglot AST parsing for exact-match comparison.
        Avoids dishonest string-matching heuristics.
        """
        if not sql:
            return ""

        cleaned = sql.strip()
        if cleaned.startswith("```sql"):
            cleaned = cleaned[6:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = sqlglot.parse_one(cleaned, read="sqlite")
            return parsed.sql(pretty=False).strip().lower()
        except Exception:
            # Fallback to whitespace & lowercase normalization if parsing fails
            return " ".join(cleaned.lower().split()).rstrip(";")

    @staticmethod
    def _normalize_row_value(val: Any) -> Any:
        """Normalizes individual row data values for semantic equivalence."""
        if val is None:
            return None
        if isinstance(val, float):
            return round(val, 4)
        if isinstance(val, int):
            return val
        s_val = str(val).strip()
        try:
            f_val = float(s_val)
            return round(f_val, 4)
        except ValueError:
            return s_val

    @classmethod
    def _normalize_rows(cls, rows: List[List[Any]]) -> List[Tuple[Any, ...]]:
        """Transforms raw database result rows into normalized tuples."""
        normalized = []
        for row in rows:
            norm_tuple = tuple(cls._normalize_row_value(v) for v in row)
            normalized.append(norm_tuple)
        return normalized

    @classmethod
    def _result_sets_match(
        cls,
        gt_sql: str,
        expected: Optional[Dict[str, Any]],
        actual: Optional[Dict[str, Any]],
    ) -> Tuple[bool, Optional[str]]:
        """
        Rigorously evaluates Execution Accuracy (EX) between Ground Truth DB execution
        and Generated Query DB execution.
        Handles: empty sets, NULLs, floats/ints, ORDER BY semantics, and error types.
        """
        if not actual:
            return False, "GenerationFailed"

        if not actual.get("executed") or actual.get("error") is not None:
            err_msg = str(actual.get("error", ""))
            if "syntax" in err_msg.lower():
                return False, "SyntaxError"
            if "no such table" in err_msg.lower():
                return False, "TableNotFound"
            if "no such column" in err_msg.lower():
                return False, "ColumnNotFound"
            return False, "ExecutionError"

        if not expected or not expected.get("executed") or expected.get("error") is not None:
            return False, "GroundTruthExecutionError"

        expected_rows = cls._normalize_rows(expected.get("rows", []))
        actual_rows = cls._normalize_rows(actual.get("rows", []))

        # Check if ORDER BY is semantically required
        has_order_by = "order by" in gt_sql.lower()

        if has_order_by:
            # Order matters strictly
            match = expected_rows == actual_rows
        else:
            # Set equivalence (order insensitive)
            match = sorted(expected_rows, key=lambda x: str(x)) == sorted(actual_rows, key=lambda x: str(x))

        if not match:
            return False, "ResultMismatch"

        return True, None

    @staticmethod
    def classify_sql_failure(gt_sql: str, generated_sql: str, actual_exec: Optional[Dict[str, Any]] = None) -> str:
        """
        Deterministically classifies Text-to-SQL failure category using sqlglot AST analysis.
        """
        import sqlglot.expressions as exp

        if not generated_sql or not generated_sql.strip():
            return "syntax error"

        # 1. Check runtime execution error
        if actual_exec and actual_exec.get("error"):
            err_msg = str(actual_exec["error"]).lower()
            if "syntax" in err_msg or "near" in err_msg:
                return "syntax error"
            if "no such table" in err_msg:
                return "wrong table"
            if "no such column" in err_msg:
                return "wrong column"
            return "execution error"

        # 2. Parse AST for GT and Generated SQL
        try:
            ast_gt = sqlglot.parse_one(gt_sql.strip(), read="sqlite")
        except Exception:
            ast_gt = None

        try:
            ast_gen = sqlglot.parse_one(generated_sql.strip(), read="sqlite")
        except Exception:
            return "syntax error"

        if not ast_gt or not ast_gen:
            return "syntax error"

        # 3. Compare JOINs
        joins_gt = list(ast_gt.find_all(exp.Join))
        joins_gen = list(ast_gen.find_all(exp.Join))
        if len(joins_gt) > 0 and len(joins_gen) == 0:
            return "missing JOIN"
        if len(joins_gt) != len(joins_gen):
            return "incorrect JOIN"
        if joins_gt and joins_gen:
            str_joins_gt = [j.sql().lower() for j in joins_gt]
            str_joins_gen = [j.sql().lower() for j in joins_gen]
            if str_joins_gt != str_joins_gen:
                return "incorrect JOIN"

        # 4. Compare Tables
        tables_gt = set(t.name.lower() for t in ast_gt.find_all(exp.Table) if t.name)
        tables_gen = set(t.name.lower() for t in ast_gen.find_all(exp.Table) if t.name)
        if tables_gt != tables_gen:
            return "wrong table"


        # 5. Compare Columns
        cols_gt = set(c.name.lower() for c in ast_gt.find_all(exp.Column) if c.name)
        cols_gen = set(c.name.lower() for c in ast_gen.find_all(exp.Column) if c.name)
        if cols_gt != cols_gen:
            return "wrong column"

        # 6. Compare Aggregations
        funcs_gt = sorted([f.key.lower() for f in ast_gt.find_all(exp.Func)])
        funcs_gen = sorted([f.key.lower() for f in ast_gen.find_all(exp.Func)])
        if funcs_gt != funcs_gen:
            return "incorrect aggregation"

        # 7. Compare WHERE/filter
        where_gt = ast_gt.find(exp.Where)
        where_gen = ast_gen.find(exp.Where)
        if bool(where_gt) != bool(where_gen):
            return "incorrect WHERE/filter"
        if where_gt and where_gen and where_gt.sql().lower() != where_gen.sql().lower():
            return "incorrect WHERE/filter"

        # 8. Compare GROUP BY
        group_gt = ast_gt.find(exp.Group)
        group_gen = ast_gen.find(exp.Group)
        if bool(group_gt) != bool(group_gen):
            return "incorrect GROUP BY"
        if group_gt and group_gen and group_gt.sql().lower() != group_gen.sql().lower():
            return "incorrect GROUP BY"

        # 9. Compare ORDER BY
        order_gt = ast_gt.find(exp.Order)
        order_gen = ast_gen.find(exp.Order)
        if bool(order_gt) != bool(order_gen):
            return "incorrect ORDER BY"
        if order_gt and order_gen and order_gt.sql().lower() != order_gen.sql().lower():
            return "incorrect ORDER BY"

        # 10. Compare LIMIT
        limit_gt = ast_gt.find(exp.Limit)
        limit_gen = ast_gen.find(exp.Limit)
        if bool(limit_gt) != bool(limit_gen):
            return "incorrect LIMIT"
        if limit_gt and limit_gen and limit_gt.sql().lower() != limit_gen.sql().lower():
            return "incorrect LIMIT"

        return "wrong result set"

    @staticmethod
    def _calculate_percentile(values: List[float], p: float) -> float:
        """Calculates exact percentile (P50, P95, P99) from a sorted list of latencies."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return round(sorted_vals[int(k)], 2)
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return round(d0 + d1, 2)

    async def run_benchmark(
        self,
        dataset_name: str = "spider_sample.json",
        checkpoint_id: str = "forgellm-qlora-v1-spider",
        limit: int = 5,
    ) -> BenchmarkRunResponse:
        """Runs automated evaluation benchmark comparing Base Model vs QLoRA Model."""

        data_file = BASE_DIR / "backend" / "app" / "data" / dataset_name
        if not data_file.exists():
            data_file = BASE_DIR / "backend" / "app" / "data" / "spider_sample.json"


        with open(data_file, "r", encoding="utf-8") as f:
            all_items = json.load(f)

        if limit and limit > 0:
            items = all_items[:limit]
        else:
            items = all_items

        details: List[EvalItemResult] = []
        failure_counts: Dict[str, int] = {}

        base_em_count = 0
        finetuned_em_count = 0

        base_ex_count = 0
        finetuned_ex_count = 0

        base_success_count = 0
        finetuned_success_count = 0

        base_latencies: List[float] = []
        finetuned_latencies: List[float] = []

        for item in items:
            q = item["instruction"]
            gt_sql = item["output"]
            db_id = item.get("db_id", "ecommerce_store")
            schema_ddl = item.get("schema", "")

            ctx = DatabaseSchemaContext(db_id=db_id, ddl=schema_ddl)

            # 1. Ground Truth DB Execution
            gt_execution = schema_engine.execute_query(db_id=db_id, sql=gt_sql)

            # 2. Base Model Generation
            req_base = SQLGenerationRequest(
                prompt=q,
                schema_context=ctx,
                model_version="base",
                execute_sql=True,
            )
            res_base = await inference_engine.generate_sql(req_base)

            # 3. Fine-Tuned Model Generation
            req_ft = SQLGenerationRequest(
                prompt=q,
                schema_context=ctx,
                model_version=checkpoint_id,
                execute_sql=True,
            )
            res_ft = await inference_engine.generate_sql(req_ft)

            # 4. Exact Match (EM) via AST Normalization
            gt_norm = self._normalize_sql(gt_sql)
            base_norm = self._normalize_sql(res_base.formatted_sql)
            ft_norm = self._normalize_sql(res_ft.formatted_sql)

            base_em = (gt_norm == base_norm)
            ft_em = (gt_norm == ft_norm)

            # 5. Execution Accuracy (EX) via Result Set Comparison
            base_execution = res_base.execution_result.model_dump() if res_base.execution_result else None
            ft_execution = res_ft.execution_result.model_dump() if res_ft.execution_result else None

            base_ex, base_err = self._result_sets_match(gt_sql, gt_execution, base_execution)
            ft_ex, ft_err = self._result_sets_match(gt_sql, gt_execution, ft_execution)

            # 6. AST Failure Classification
            fail_cat = None
            if not ft_ex:
                fail_cat = self.classify_sql_failure(gt_sql, res_ft.formatted_sql, ft_execution)
                failure_counts[fail_cat] = failure_counts.get(fail_cat, 0) + 1

            # Execution success flags (did execution run without syntax/table errors?)
            if base_execution and base_execution.get("executed") and base_execution.get("error") is None:
                base_success_count += 1
            if ft_execution and ft_execution.get("executed") and ft_execution.get("error") is None:
                finetuned_success_count += 1

            if base_em:
                base_em_count += 1
            if ft_em:
                finetuned_em_count += 1

            if base_ex:
                base_ex_count += 1
            if ft_ex:
                finetuned_ex_count += 1

            base_latencies.append(res_base.latency_ms)
            finetuned_latencies.append(res_ft.latency_ms)

            details.append(
                EvalItemResult(
                    id=item["id"],
                    question=q,
                    ground_truth_sql=gt_sql,
                    base_model_sql=res_base.formatted_sql,
                    finetuned_model_sql=res_ft.formatted_sql,
                    base_exact_match=base_em,
                    finetuned_exact_match=ft_em,
                    base_exec_match=base_ex,
                    finetuned_exec_match=ft_ex,
                    base_latency_ms=res_base.latency_ms,
                    finetuned_latency_ms=res_ft.latency_ms,
                    base_error_type=base_err,
                    finetuned_error_type=ft_err,
                    failure_category=fail_cat,
                )
            )

        total_samples = len(items)
        total_failures = sum(failure_counts.values())
        failure_analysis = {}
        if total_failures > 0:
            for cat, cnt in failure_counts.items():
                failure_analysis[cat] = round((cnt / total_failures) * 100, 1)

        result = BenchmarkRunResponse(
            eval_id=f"eval-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            dataset_name=dataset_name,
            checkpoint_id=checkpoint_id,
            total_samples=total_samples,
            base_exact_match_acc=round(base_em_count / total_samples, 4),
            finetuned_exact_match_acc=round(finetuned_em_count / total_samples, 4),
            base_exec_acc=round(base_ex_count / total_samples, 4),
            finetuned_exec_acc=round(finetuned_ex_count / total_samples, 4),
            base_success_rate=round(base_success_count / total_samples, 4),
            finetuned_success_rate=round(finetuned_success_count / total_samples, 4),
            base_fail_rate=round((total_samples - base_success_count) / total_samples, 4),
            finetuned_fail_rate=round((total_samples - finetuned_success_count) / total_samples, 4),
            base_avg_latency_ms=round(sum(base_latencies) / len(base_latencies), 2) if base_latencies else 0.0,
            finetuned_avg_latency_ms=round(sum(finetuned_latencies) / len(finetuned_latencies), 2) if finetuned_latencies else 0.0,
            base_p50_latency_ms=self._calculate_percentile(base_latencies, 50),
            finetuned_p50_latency_ms=self._calculate_percentile(finetuned_latencies, 50),
            base_p95_latency_ms=self._calculate_percentile(base_latencies, 95),
            finetuned_p95_latency_ms=self._calculate_percentile(finetuned_latencies, 95),
            base_p99_latency_ms=self._calculate_percentile(base_latencies, 99),
            finetuned_p99_latency_ms=self._calculate_percentile(finetuned_latencies, 99),
            failure_analysis=failure_analysis,
            failure_counts=failure_counts,
            details=details,
        )

        self.history.append(result)
        self._save_history()
        return result


eval_service = EvalService()