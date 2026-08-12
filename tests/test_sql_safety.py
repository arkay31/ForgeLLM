import pytest
from app.services.sql_safety import sql_safety_validator
from app.services.schema_engine import schema_engine


def test_safe_select_query():
    """Verify safe SELECT queries with JOINs, WHERE, GROUP BY, and LIMIT are allowed."""
    sql = """
    SELECT T1.name, T1.country, T1.age
    FROM singer AS T1
    JOIN singer_in_concert AS T2 ON T1.singer_id = T2.singer_id
    JOIN concert AS T3 ON T2.concert_id = T3.concert_id
    WHERE T3.year > 2020
    GROUP BY T1.singer_id
    LIMIT 10;
    """
    db_schema = schema_engine.databases.get("concert_singer")
    res = sql_safety_validator.validate_sql(sql, db_schema)
    assert res["allowed"] is True
    assert len(res["violations"]) == 0
    assert "passed all safety" in res["reason"]


def test_safe_cte_query():
    """Verify CTE (WITH clause) SELECT queries are allowed."""
    sql = """
    WITH TopCustomers AS (
        SELECT customer_id, SUM(total_amount) AS total_spent
        FROM orders
        WHERE status = 'Completed'
        GROUP BY customer_id
    )
    SELECT c.first_name, c.last_name, tc.total_spent
    FROM customers c
    JOIN TopCustomers tc ON c.customer_id = tc.customer_id
    ORDER BY tc.total_spent DESC
    LIMIT 5;
    """
    db_schema = schema_engine.databases.get("ecommerce_store")
    res = sql_safety_validator.validate_sql(sql, db_schema)
    assert res["allowed"] is True
    assert len(res["violations"]) == 0


def test_block_drop_table():
    """Verify DROP TABLE statements are blocked."""
    sql = "DROP TABLE customers;"
    db_schema = schema_engine.databases.get("ecommerce_store")
    res = sql_safety_validator.validate_sql(sql, db_schema)
    assert res["allowed"] is False
    assert any("DROP" in v for v in res["violations"]) or any("Prohibited" in v for v in res["violations"])


def test_block_insert_into():
    """Verify INSERT statements are blocked."""
    sql = "INSERT INTO customers (customer_id, first_name) VALUES (99, 'Hacker');"
    db_schema = schema_engine.databases.get("ecommerce_store")
    res = sql_safety_validator.validate_sql(sql, db_schema)
    assert res["allowed"] is False
    assert any("INSERT" in v or "Prohibited" in v for v in res["violations"])


def test_block_update_query():
    """Verify UPDATE statements are blocked."""
    sql = "UPDATE customers SET email = 'hacked@malicious.com' WHERE customer_id = 1;"
    db_schema = schema_engine.databases.get("ecommerce_store")
    res = sql_safety_validator.validate_sql(sql, db_schema)
    assert res["allowed"] is False
    assert any("UPDATE" in v or "Prohibited" in v for v in res["violations"])


def test_block_delete_query():
    """Verify DELETE statements are blocked."""
    sql = "DELETE FROM orders WHERE total_amount > 0;"
    db_schema = schema_engine.databases.get("ecommerce_store")
    res = sql_safety_validator.validate_sql(sql, db_schema)
    assert res["allowed"] is False
    assert any("DELETE" in v or "Prohibited" in v for v in res["violations"])


def test_block_multi_statement_injection():
    """Verify multi-statement stacked SQL injection is blocked."""
    sql = "SELECT * FROM singer; DROP TABLE singer;"
    db_schema = schema_engine.databases.get("concert_singer")
    res = sql_safety_validator.validate_sql(sql, db_schema)
    assert res["allowed"] is False
    assert any("Multiple SQL statements" in v for v in res["violations"])


def test_block_pragma_execution():
    """Verify PRAGMA statements are blocked."""
    sql = "PRAGMA compile_options;"
    res = sql_safety_validator.validate_sql(sql)
    assert res["allowed"] is False
    assert any("PRAGMA" in v for v in res["violations"])


def test_block_invalid_unregistered_table():
    """Verify queries referencing non-existent/unregistered tables are blocked."""
    sql = "SELECT * FROM secret_passwords;"
    db_schema = schema_engine.databases.get("ecommerce_store")
    res = sql_safety_validator.validate_sql(sql, db_schema)
    assert res["allowed"] is False
    assert any("secret_passwords" in v for v in res["violations"])
