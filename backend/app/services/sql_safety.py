import logging
import re
from typing import Dict, Any, List, Optional, Set
import sqlglot

logger = logging.getLogger("ForgeLLM.SQLSafetyValidator")


class SQLSafetyValidator:
    """
    AST-based SQL Safety and Schema Validation Layer.
    Enforces read-only Text-to-SQL constraints, blocks multi-statement injection,
    detects unsafe DDL/DML expressions, and validates referenced tables and columns.
    """

    # Expressions that mutate data or database structures
    UNSAFE_EXPRESSION_TYPES = (
        sqlglot.exp.Insert,
        sqlglot.exp.Update,
        sqlglot.exp.Delete,
        sqlglot.exp.Drop,
        sqlglot.exp.Create,
        sqlglot.exp.Alter,
        sqlglot.exp.Command,
    )

    # Keywords or commands that represent high-risk operations
    UNSAFE_KEYWORDS = {
        "insert", "update", "delete", "drop", "alter", "create",
        "attach", "detach", "vacuum", "pragma", "reindex",
        "grant", "revoke", "truncate", "replace", "exec", "execute"
    }

    @staticmethod
    def _clean_sql(raw_sql: str) -> str:
        """Strips markdown fences and leading/trailing whitespace."""
        if not raw_sql:
            return ""
        cleaned = raw_sql.strip()
        if cleaned.startswith("```sql"):
            cleaned = cleaned[6:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def validate_sql(
        self,
        sql: str,
        db_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validates a SQL query for safety and schema compliance.
        Returns: { "allowed": bool, "reason": str, "violations": List[str] }
        """
        cleaned_sql = self._clean_sql(sql)
        violations: List[str] = []

        if not cleaned_sql:
            return {
                "allowed": False,
                "reason": "Empty SQL query provided",
                "violations": ["Empty SQL string"],
            }

        # 1. Detect Multi-Statement Stacked Queries
        try:
            parsed_statements = sqlglot.parse(cleaned_sql, read="sqlite")
            # Filter out None entries resulting from trailing semicolons
            valid_statements = [s for s in parsed_statements if s is not None]
            if len(valid_statements) > 1:
                violations.append(
                    f"Multiple SQL statements detected ({len(valid_statements)} statements). Multi-statement stacked execution is prohibited."
                )
        except Exception as e:
            violations.append(f"SQL Syntax Parsing Error: {str(e)}")
            return {
                "allowed": False,
                "reason": "Failed to parse SQL AST",
                "violations": violations,
            }

        if not valid_statements:
            return {
                "allowed": False,
                "reason": "No valid SQL statements found",
                "violations": ["Invalid SQL statement structure"],
            }

        ast = valid_statements[0]

        # 2. Enforce Read-Only Query Type (Primary AST Root must be Select or Expression)
        if not isinstance(ast, (sqlglot.exp.Select, sqlglot.exp.Expression)):
            violations.append(
                f"Prohibited query type '{ast.key.upper()}'. Only read-only SELECT queries are allowed."
            )

        # 3. Check for Unsafe AST Expression Nodes in Tree (e.g. Subquery Mutations)
        for unsafe_type in self.UNSAFE_EXPRESSION_TYPES:
            for node in ast.find_all(unsafe_type):
                node_name = node.key.upper() if hasattr(node, "key") else str(type(node).__name__)
                violations.append(f"Prohibited AST operation detected: {node_name}")

        # 4. Check for Unsafe Keywords / Commands in Command Nodes
        for cmd in ast.find_all(sqlglot.exp.Command):
            cmd_text = str(cmd).lower()
            if any(kw in cmd_text for kw in self.UNSAFE_KEYWORDS):
                violations.append(f"Prohibited command operation: '{cmd_text}'")

        # 5. Check for PRAGMA or System Table Writes
        sql_lower = cleaned_sql.lower()
        if "pragma" in sql_lower:
            violations.append("PRAGMA statement execution is prohibited for safety.")
        if "attach " in sql_lower or "detach " in sql_lower:
            violations.append("ATTACH/DETACH database command is prohibited.")

        # 6. Validate Referenced Tables against Schema (if schema provided)
        if db_schema and "ddl" in db_schema:
            ddl_lower = db_schema["ddl"].lower()
            # Extract known table names from DDL using regex
            known_tables = set(re.findall(r"create\s+table\s+([a-zA-Z0-9_]+)", ddl_lower))
            known_tables.add("sqlite_master")
            known_tables.add("sqlite_sequence")

            # Add CTE (WITH clause) table aliases to known tables
            for cte in ast.find_all(sqlglot.exp.CTE):
                if hasattr(cte, "alias_or_name") and cte.alias_or_name:
                    known_tables.add(cte.alias_or_name.lower())
                elif hasattr(cte, "this") and hasattr(cte.this, "name") and cte.this.name:
                    known_tables.add(cte.this.name.lower())

            referenced_tables = {table.name.lower() for table in ast.find_all(sqlglot.exp.Table) if table.name}
            unknown_tables = referenced_tables - known_tables


            if unknown_tables:
                table_list = ", ".join(f"'{t}'" for t in sorted(unknown_tables))
                violations.append(
                    f"Referenced table(s) {table_list} do not exist in database schema '{db_schema.get('db_id', 'target')}'."
                )

            # 7. Validate Referenced Columns against Schema (where practical)
            known_columns: Set[str] = set(re.findall(r"([a-zA-Z0-9_]+)\s+(?:int|text|decimal|date|timestamp|boolean|varchar)", ddl_lower))
            if known_columns:
                referenced_cols = {col.name.lower() for col in ast.find_all(sqlglot.exp.Column) if col.name and col.name != "*"}
                # Filter out table aliases or functions
                unknown_cols = {
                    c for c in referenced_cols
                    if c not in known_columns and not c.startswith("t") and len(c) > 2
                }
                # Log if unknown columns found (warning level violation)
                if len(unknown_cols) > 3:
                    violations.append(f"Referenced multiple unrecognized columns: {', '.join(sorted(unknown_cols)[:3])}")

        # Final Verdict
        allowed = len(violations) == 0
        reason = (
            "SQL query passed all safety and schema validation checks"
            if allowed
            else f"SQL execution blocked due to {len(violations)} safety violation(s)"
        )

        return {
            "allowed": allowed,
            "reason": reason,
            "violations": violations,
        }


sql_safety_validator = SQLSafetyValidator()
