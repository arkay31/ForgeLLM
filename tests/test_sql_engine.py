import pytest
from app.services.schema_engine import schema_engine


def test_sql_validation_and_formatting():
    """Verify sqlglot AST parsing, formatting, and table extraction."""
    raw_sql = "select name, country, age from singer where age > 25 order by age desc;"
    valid, formatted, err, tables = schema_engine.format_and_validate_sql(raw_sql)

    assert valid is True
    assert err is None
    assert "SELECT" in formatted
    assert "singer" in tables


def test_sql_execution_success():
    """Verify executing valid SELECT queries against SQLite in-memory databases."""
    sql = "SELECT singer_id, name, country, age FROM singer WHERE age > 20 ORDER BY singer_id ASC LIMIT 5;"
    result = schema_engine.execute_query("concert_singer", sql)

    assert result["executed"] is True
    assert result["error"] is None
    assert "singer_id" in result["columns"]
    assert "name" in result["columns"]
    assert isinstance(result["rows"], list)
    assert result["row_count"] >= 0


def test_sql_execution_empty_result_set():
    """Verify executing queries that return 0 matching rows."""
    sql = "SELECT * FROM singer WHERE country = 'NonExistentCountry999';"
    result = schema_engine.execute_query("concert_singer", sql)

    assert result["executed"] is True
    assert result["error"] is None
    assert result["row_count"] == 0
    assert result["rows"] == []


def test_malformed_sql_syntax_error():
    """Verify malformed SQL with invalid syntax returns structured execution error."""
    malformed_sql = "SELECT name FROM WHERE FROM singer;;;"
    result = schema_engine.execute_query("concert_singer", malformed_sql)

    assert result["executed"] is False
    assert result["rows"] == []
    assert result["error"] is not None
    assert "Syntax Error" in result["error"] or "Safety Violation" in result["error"] or "Error" in result["error"]


def test_failed_sql_execution_nonexistent_table():
    """Verify executing query on non-existent table returns structured error."""
    invalid_sql = "SELECT * FROM fake_nonexistent_table_xyz;"
    result = schema_engine.execute_query("ecommerce_store", invalid_sql)

    assert result["executed"] is False
    assert result["rows"] == []
    assert result["error"] is not None
    assert "Violation" in result["error"] or "no such table" in result["error"].lower()


def test_failed_sql_execution_nonexistent_column():
    """Verify executing query on non-existent column returns structured error."""
    invalid_col_sql = "SELECT fake_column_abc FROM customers;"
    result = schema_engine.execute_query("ecommerce_store", invalid_col_sql)

    assert result["executed"] is False
    assert result["error"] is not None
