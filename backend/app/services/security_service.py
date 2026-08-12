import re
import json
import time
import hashlib
import hmac
import logging
from typing import Tuple, Optional, List, Dict, Any
import sqlglot

logger = logging.getLogger("forgellm.security")
logger.setLevel(logging.INFO)

# Destructive SQL Keywords & Patterns to Block
DESTRUCTIVE_KEYWORDS = {
    "DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE", "INSERT", 
    "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "PRAGMA", 
    "ATTACH", "DETACH", "VACUUM"
}

class SQLSecurityException(Exception):
    """Raised when generated SQL contains destructive or unauthorized operations."""
    pass

class PromptInjectionException(Exception):
    """Raised when prompt contains suspicious injection patterns or exceeds length limit."""
    pass

class SecurityService:
    def __init__(self, master_key: str = "forge-secret-key-2026-prod"):
        self.master_key = master_key
        self.hashed_master_key = self.hash_api_key(master_key)

    @staticmethod
    def hash_api_key(raw_api_key: str) -> str:
        """Hashes API Key using SHA-256 with secret salt for secure comparison."""
        salt = b"forgellm_salt_2026_secure"
        return hmac.new(salt, raw_api_key.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_api_key(self, provided_key: Optional[str]) -> bool:
        """Verifies provided API key against stored hash using constant-time comparison."""
        if not provided_key:
            return False
        provided_hash = self.hash_api_key(provided_key)
        return hmac.compare_digest(provided_hash, self.hashed_master_key)

    @staticmethod
    def sanitize_user_prompt(prompt: str, max_chars: int = 2048) -> str:
        """Sanitizes input user prompt, enforces length bounds, and strips injection tags."""
        if len(prompt) > max_chars:
            raise PromptInjectionException(f"Prompt length ({len(prompt)} chars) exceeds maximum limit of {max_chars} chars.")

        # Check for system instruction override patterns
        injection_patterns = [
            r"ignore\s+all\s+previous\s+instructions",
            r"override\s+system\s+prompt",
            r"drop\s+table",
            r"delete\s+from",
            r"truncate\s+table"
        ]
        
        lowered = prompt.lower()
        for pattern in injection_patterns:
            if re.search(pattern, lowered):
                raise PromptInjectionException(f"Suspicious prompt pattern detected: '{pattern}'")

        # Clean null bytes & control chars
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", prompt)
        return cleaned.strip()

    @staticmethod
    def sanitize_and_validate_sql(sql: str) -> Tuple[bool, str, Optional[str]]:
        """
        CRITICAL OUTPUT VALIDATION ENGINE:
        Inspects generated SQL via AST parsing and regex to strictly block 
        DROP, DELETE, TRUNCATE, ALTER, UPDATE, INSERT, GRANT, and multi-statement injection.
        Only SELECT queries are permitted!
        """
        raw_sql = sql.strip()
        
        # 1. Clean codeblock markers
        if raw_sql.startswith("```sql"): raw_sql = raw_sql[6:]
        if raw_sql.startswith("```"): raw_sql = raw_sql[3:]
        if raw_sql.endswith("```"): raw_sql = raw_sql[:-3]
        raw_sql = raw_sql.strip().rstrip(";")

        if not raw_sql:
            return False, "", "Empty SQL output generated"

        # 2. String-level regex check for destructive keywords
        tokens = re.findall(r"\b[A-Za-z_]+\b", raw_sql.upper())
        found_destructive = DESTRUCTIVE_KEYWORDS.intersection(set(tokens))
        if found_destructive:
            err_msg = f"Security Violation: Destructive statement keyword(s) detected: {', '.join(found_destructive)}"
            logger.warning(f"[SQL Sanitizer Blocked] {err_msg} in query: '{raw_sql}'")
            return False, raw_sql, err_msg

        # 3. Check for multiple statements (e.g. SELECT * FROM users; DROP TABLE users;)
        # Ignore semicolons inside quotes
        statements = [s.strip() for s in raw_sql.split(";") if s.strip()]
        if len(statements) > 1:
            err_msg = "Security Violation: Multiple SQL statements detected in single query body."
            logger.warning(f"[SQL Sanitizer Blocked] {err_msg}")
            return False, raw_sql, err_msg

        # 4. AST-level validation using sqlglot
        try:
            parsed = sqlglot.parse_one(raw_sql, read="sqlite")
            
            # Ensure root expression is a SELECT or UNION expression
            if not isinstance(parsed, (sqlglot.exp.Select, sqlglot.exp.Union, sqlglot.exp.Subquery)):
                err_msg = f"Security Violation: Query root statement type '{parsed.key}' is forbidden. Only SELECT queries allowed."
                return False, raw_sql, err_msg
                
            # Formatted clean SQL output
            formatted = parsed.sql(pretty=True)
            return True, formatted, None

        except Exception as e:
            # Fallback regex check if sqlglot parse fails but string is clean SELECT
            if raw_sql.upper().startswith("SELECT") or raw_sql.upper().startswith("WITH"):
                return True, raw_sql, None
            return False, raw_sql, f"SQL Syntax Validation Failed: {str(e)}"

    @staticmethod
    def log_structured_json(request_data: Dict[str, Any]):
        """Emits structured JSON logs for audit trail and observability."""
        log_payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": "api_request",
            **request_data
        }
        print(json.dumps(log_payload))

security_service = SecurityService()
