"""Query classifier for semantic memory."""

from typing import Any


class QueryClassifier:
    """Classifies queries into engineering categories."""

    QUERY_PATTERNS: dict[str, list[str]] = {
        "architecture": ["architecture", "structure", "design", "pattern", "layout", "organization"],
        "api": ["api", "endpoint", "route", "rest", "http", "request", "response", "controller"],
        "database": ["database", "model", "schema", "table", "migration", "orm", "sql", "query"],
        "authentication": ["auth", "login", "jwt", "token", "permission", "role", "security", "password"],
        "configuration": ["config", "settings", "environment", "env", "variable", "constant"],
        "dependency": ["dependency", "package", "library", "import", "module", "require"],
        "documentation": ["documentation", "readme", "docs", "guide", "example"],
        "code": ["function", "class", "method", "implementation", "code", "logic", "algorithm"],
    }

    def classify(self, query: str) -> str:
        """Classify a query into a category."""
        query_lower = query.lower()
        scores: dict[str, int] = {}

        for category, keywords in self.QUERY_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[category] = score

        if max(scores.values()) == 0:
            return "general"

        return max(scores, key=scores.get)

    def get_search_hints(self, classification: str) -> dict[str, Any]:
        """Get search hints based on classification."""
        hints: dict[str, dict[str, Any]] = {
            "architecture": {"chunk_types": ["repository", "module"], "boost_architecture": True},
            "api": {"chunk_types": ["route", "class", "function"], "boost_routes": True},
            "database": {"chunk_types": ["database", "class"], "boost_database": True},
            "authentication": {"chunk_types": ["route", "class", "config"], "tags": ["auth", "security"]},
            "configuration": {"chunk_types": ["config", "repository"]},
            "dependency": {"chunk_types": ["repository", "module"]},
            "documentation": {"chunk_types": ["documentation", "repository"]},
            "code": {"chunk_types": ["class", "function", "module"]},
            "general": {},
        }
        return hints.get(classification, {})
