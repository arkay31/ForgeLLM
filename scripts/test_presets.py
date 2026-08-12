#!/usr/bin/env python3
"""
ForgeLLM Preset Verification Suite
----------------------------------
Tests all 4 Text-to-SQL Studio presets against the schema engine & inference API
and confirms zero execution errors across all databases.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.models.schemas import SQLGenerationRequest, DatabaseSchemaContext
from app.services.inference_engine import inference_engine
from app.services.schema_engine import schema_engine

async def test_all_presets():
    print("🧪 Testing All 4 Text-to-SQL Studio Presets against SQLite Databases...\n")
    
    presets = [
        {
            "name": "Preset 1: E-Commerce Top Customers",
            "prompt": "Find top 5 customers by total spending in Canada or Germany",
            "db_id": "ecommerce_store",
            "ddl": """CREATE TABLE customers (customer_id INT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, country TEXT, created_at TIMESTAMP);
CREATE TABLE products (product_id INT PRIMARY KEY, name TEXT, category TEXT, price DECIMAL, stock_quantity INT);
CREATE TABLE orders (order_id INT PRIMARY KEY, customer_id INT, order_date DATE, total_amount DECIMAL, status TEXT);
CREATE TABLE order_items (item_id INT PRIMARY KEY, order_id INT, product_id INT, quantity INT, unit_price DECIMAL);
CREATE TABLE reviews (review_id INT PRIMARY KEY, product_id INT, customer_id INT, rating INT, comment TEXT, review_date DATE);"""
        },
        {
            "name": "Preset 2: Concert Singers (>2020)",
            "prompt": "Find the names, country, and age of all singers who have sung in concerts after 2020",
            "db_id": "concert_singer",
            "ddl": """CREATE TABLE singer (singer_id INT PRIMARY KEY, name TEXT, country TEXT, song_name TEXT, song_release_year TEXT, age INT, is_male BOOLEAN);
CREATE TABLE concert (concert_id INT PRIMARY KEY, concert_name TEXT, theme TEXT, stadium_id INT, year INT);
CREATE TABLE singer_in_concert (concert_id INT, singer_id INT);"""
        },
        {
            "name": "Preset 3: HR Average Salary by Dept",
            "prompt": "List all departments with total number of employees and average salary",
            "db_id": "hr_analytics",
            "ddl": """CREATE TABLE departments (dept_id INT PRIMARY KEY, dept_name TEXT, location TEXT, budget DECIMAL);
CREATE TABLE employees (emp_id INT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, role TEXT, dept_id INT, hire_date DATE);
CREATE TABLE salaries (salary_id INT PRIMARY KEY, emp_id INT, base_salary DECIMAL, bonus DECIMAL, effective_date DATE);
CREATE TABLE performance_reviews (review_id INT PRIMARY KEY, emp_id INT, review_year INT, rating INT, notes TEXT);"""
        },
        {
            "name": "Preset 4: Top Rated Products",
            "prompt": "Show products with average review rating greater than 4.0",
            "db_id": "ecommerce_store",
            "ddl": """CREATE TABLE customers (customer_id INT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, country TEXT, created_at TIMESTAMP);
CREATE TABLE products (product_id INT PRIMARY KEY, name TEXT, category TEXT, price DECIMAL, stock_quantity INT);
CREATE TABLE orders (order_id INT PRIMARY KEY, customer_id INT, order_date DATE, total_amount DECIMAL, status TEXT);
CREATE TABLE order_items (item_id INT PRIMARY KEY, order_id INT, product_id INT, quantity INT, unit_price DECIMAL);
CREATE TABLE reviews (review_id INT PRIMARY KEY, product_id INT, customer_id INT, rating INT, comment TEXT, review_date DATE);"""
        }
    ]

    all_passed = True
    for idx, p in enumerate(presets, 1):
        print(f"--------------------------------------------------")
        print(f"▶ Testing {p['name']} [DB: {p['db_id']}]")
        print(f"  Question: '{p['prompt']}'")
        
        ctx = DatabaseSchemaContext(db_id=p['db_id'], ddl=p['ddl'])
        req = SQLGenerationRequest(
            prompt=p['prompt'],
            schema_context=ctx,
            model_version="active",
            execute_sql=True
        )
        
        res = await inference_engine.generate_sql(req)
        print(f"  Generated SQL:\n{res.formatted_sql}")
        
        exec_res = res.execution_result
        if exec_res and exec_res.executed and exec_res.error is None:
            print(f"  ✅ SUCCESS: Executed in {exec_res.execution_time_ms} ms | Returned {exec_res.row_count} rows | Columns: {exec_res.columns}")
            if exec_res.rows:
                print(f"  Sample Row 1: {exec_res.rows[0]}")
        else:
            all_passed = False
            err_msg = exec_res.error if exec_res else "No execution result"
            print(f"  ❌ FAILED: {err_msg}")
            
    print(f"--------------------------------------------------")
    if all_passed:
        print("\n🎉 ALL 4 PRESETS EXECUTED CLEANLY WITH ZERO ERRORS!")
    else:
        print("\n❌ SOME PRESETS FAILED EXECUTION!")

if __name__ == "__main__":
    asyncio.run(test_all_presets())
