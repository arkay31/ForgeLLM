from locust import HttpUser, task, between, events
import random

class ForgeLLMUser(HttpUser):
    wait_time = between(1, 3)
    headers = {"X-API-Key": "forge-secret-key-2026-prod", "Content-Type": "application/json"}

    @task(3)
    def test_text_to_sql_inference(self):
        prompts = [
            "Find top 5 customers by spending in Canada",
            "What is the average salary of employees in AI Research?",
            "List all products with review rating greater than 4.0",
            "Get total deposit volume for checking accounts in the last 30 days"
        ]
        payload = {
            "prompt": random.choice(prompts),
            "model_version": "active",
            "execute_sql": True,
            "schema_context": {
                "db_id": "ecommerce_store",
                "ddl": "CREATE TABLE customers (customer_id INT, first_name TEXT, country TEXT);"
            }
        }
        self.client.post("/api/v1/serve/generate", json=payload, headers=self.headers, name="POST /serve/generate")

    @task(2)
    def test_system_metrics(self):
        self.client.get("/api/v1/system/metrics", name="GET /system/metrics")

    @task(1)
    def test_models_list(self):
        self.client.get("/api/v1/models", name="GET /models")
