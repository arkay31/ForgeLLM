import sqlite3
import time
import sqlglot
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
from app.config import settings
from app.services.sql_safety import sql_safety_validator


class SchemaEngine:
    def __init__(self):
        self.databases: Dict[str, Dict[str, Any]] = {}
        self._initialize_default_databases()

    def _initialize_default_databases(self):
        """Loads seed SQL files into in-memory SQLite connections with exact schema matching."""
        data_dir = settings.BASE_DIR / "backend" / "app" / "data"
        
        # 1. E-Commerce Store DB
        ecom_sql_path = data_dir / "ecommerce_db.sql"
        if ecom_sql_path.exists():
            with open(ecom_sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            conn.executescript(sql_script)
            self.databases["ecommerce_store"] = {
                "db_id": "ecommerce_store",
                "name": "E-Commerce Store DB",
                "conn": conn,
                "ddl": """CREATE TABLE customers (customer_id INT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, country TEXT, created_at TIMESTAMP);
CREATE TABLE products (product_id INT PRIMARY KEY, name TEXT, category TEXT, price DECIMAL, stock_quantity INT);
CREATE TABLE orders (order_id INT PRIMARY KEY, customer_id INT, order_date DATE, total_amount DECIMAL, status TEXT);
CREATE TABLE order_items (item_id INT PRIMARY KEY, order_id INT, product_id INT, quantity INT, unit_price DECIMAL);
CREATE TABLE reviews (review_id INT PRIMARY KEY, product_id INT, customer_id INT, rating INT, comment TEXT, review_date DATE);""",
                "description": "Online e-commerce platform with customers, orders, order items, product inventory, and customer reviews."
            }

        # 2. HR Analytics DB
        hr_sql_path = data_dir / "hr_db.sql"
        if hr_sql_path.exists():
            with open(hr_sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            conn.executescript(sql_script)
            self.databases["hr_analytics"] = {
                "db_id": "hr_analytics",
                "name": "HR & Compensation Analytics DB",
                "conn": conn,
                "ddl": """CREATE TABLE departments (dept_id INT PRIMARY KEY, dept_name TEXT, location TEXT, budget DECIMAL);
CREATE TABLE employees (emp_id INT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, role TEXT, dept_id INT, hire_date DATE);
CREATE TABLE salaries (salary_id INT PRIMARY KEY, emp_id INT, base_salary DECIMAL, bonus DECIMAL, effective_date DATE);
CREATE TABLE performance_reviews (review_id INT PRIMARY KEY, emp_id INT, review_year INT, rating INT, notes TEXT);""",
                "description": "Corporate HR management system tracking departments, employees, salary histories, and performance reviews."
            }

        # 3. Concert Singer DB
        singer_sql_path = data_dir / "concert_singer_db.sql"
        if singer_sql_path.exists():
            with open(singer_sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            conn.executescript(sql_script)
            self.databases["concert_singer"] = {
                "db_id": "concert_singer",
                "name": "Concert Singer DB",
                "conn": conn,
                "ddl": """CREATE TABLE singer (singer_id INT PRIMARY KEY, name TEXT, country TEXT, song_name TEXT, song_release_year TEXT, age INT, is_male BOOLEAN);
CREATE TABLE concert (concert_id INT PRIMARY KEY, concert_name TEXT, theme TEXT, stadium_id INT, year INT);
CREATE TABLE singer_in_concert (concert_id INT, singer_id INT);""",
                "description": "Music industry database tracking singers, concert tours, themes, and concert participation."
            }

        # 4. Finance Bank DB
        bank_sql_path = data_dir / "finance_bank_db.sql"
        if bank_sql_path.exists():
            with open(bank_sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            conn.executescript(sql_script)
            self.databases["finance_bank"] = {
                "db_id": "finance_bank",
                "name": "Finance & Banking DB",
                "conn": conn,
                "ddl": """CREATE TABLE accounts (account_id INT PRIMARY KEY, customer_id INT, account_type TEXT, balance DECIMAL);
CREATE TABLE transactions (tx_id INT PRIMARY KEY, account_id INT, tx_date DATE, amount DECIMAL, tx_type TEXT);""",
                "description": "Banking transaction system tracking customer accounts, deposits, withdrawals, and balances."
            }

        # Fallback default connection for dynamic testing
        self.default_conn = sqlite3.connect(":memory:", check_same_thread=False)

    def get_database_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "db_id": db["db_id"],
                "name": db["name"],
                "ddl": db["ddl"],
                "description": db["description"]
            }
            for db in self.databases.values()
        ]

    def format_and_validate_sql(self, raw_sql: str) -> Tuple[bool, str, Optional[str], List[str]]:
        """
        Cleans, normalizes, extracts SQL-only statements from LLM output (stripping markdown code fences
        and trailing conversational explanations), and parses SQL using sqlglot.
        """
        import re
        text = raw_sql.strip()

        # 1. Extract markdown code blocks if present (e.g. ```sql ... ```)
        code_block_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if code_block_match:
            text = code_block_match.group(1).strip()

        # 2. Strip leading conversational text before SELECT / WITH
        match_start = re.search(r"\b(SELECT|WITH)\b", text, re.IGNORECASE)
        if match_start:
            text = text[match_start.start():].strip()

        # 3. Try parsing the text directly with sqlglot
        try:
            parsed = sqlglot.parse_one(text, read="sqlite")
            formatted = parsed.sql(pretty=True)
            tables = [table.name for table in parsed.find_all(sqlglot.exp.Table)]
            return True, formatted, None, tables
        except Exception:
            pass

        # 4. Try parsing multi-statement expressions using sqlglot parser AST
        try:
            statements = sqlglot.parse(text, read="sqlite")
            for stmt in statements:
                if stmt and isinstance(stmt, (sqlglot.exp.Select, sqlglot.exp.Union, sqlglot.exp.Expression)):
                    tables = [table.name for table in stmt.find_all(sqlglot.exp.Table)]
                    return True, stmt.sql(pretty=True), None, tables
        except Exception:
            pass

        # 5. Semicolon boundary extraction (handles SQL statement terminating with ';' followed by conversational text)
        if ";" in text:
            accumulated = ""
            for part in text.split(";"):
                accumulated += part + ";"
                try:
                    parsed = sqlglot.parse_one(accumulated.strip(), read="sqlite")
                    if isinstance(parsed, (sqlglot.exp.Select, sqlglot.exp.Union, sqlglot.exp.Expression)):
                        tables = [table.name for table in parsed.find_all(sqlglot.exp.Table)]
                        return True, parsed.sql(pretty=True), None, tables
                except Exception:
                    continue

        return False, raw_sql.strip(), "Unable to extract or parse valid SQL AST statement from model generation output", []




    def execute_query(self, db_id: Optional[str], sql: str) -> Dict[str, Any]:


        """Executes a SQL query against target database and returns execution result."""
        db_schema = self.databases.get(db_id) if db_id and db_id in self.databases else None
        
        # 1. Run AST-based SQL Safety & Schema Validation
        safety = sql_safety_validator.validate_sql(sql, db_schema)
        if not safety["allowed"]:
            return {
                "executed": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
                "error": f"SQL Safety Violation: {safety['reason']} ({'; '.join(safety['violations'])})",
                "safety_result": safety
            }

        valid, formatted_sql, syntax_err, tables = self.format_and_validate_sql(sql)
        if not valid and syntax_err:
            return {
                "executed": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
                "error": f"SQL Syntax Error: {syntax_err}",
                "safety_result": safety
            }

        # Determine target connection
        conn = None
        if db_id and db_id in self.databases:
            conn = self.databases[db_id]["conn"]
        elif len(self.databases) > 0:
            conn = list(self.databases.values())[0]["conn"]
        else:
            conn = self.default_conn


        start_time = time.time()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            exec_time = round((time.time() - start_time) * 1000, 2)
            
            serializable_rows = [list(row) for row in rows[:50]]
            
            return {
                "executed": True,
                "columns": columns,
                "rows": serializable_rows,
                "row_count": len(rows),
                "execution_time_ms": exec_time,
                "error": None
            }
        except Exception as e:
            exec_time = round((time.time() - start_time) * 1000, 2)
            return {
                "executed": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": exec_time,
                "error": f"Execution Error: {str(e)}"
            }

schema_engine = SchemaEngine()
