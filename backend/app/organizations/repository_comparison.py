from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ComparisonType(str, Enum):
    ARCHITECTURE = "architecture"
    DEPENDENCIES = "dependencies"
    API = "api"
    DATABASE = "database"
    FULL = "full"


@dataclass
class ComparisonResult:
    repository_a: str
    repository_b: str
    comparison_type: str
    differences: list[dict[str, Any]] = field(default_factory=list)
    similarities: list[dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    recommendations: list[str] = field(default_factory=list)


class RepositoryComparison:
    async def compare_repositories(
        self,
        repo_a: dict[str, Any],
        repo_b: dict[str, Any],
        comparison_type: ComparisonType,
    ) -> ComparisonResult:
        if comparison_type == ComparisonType.ARCHITECTURE:
            details = await self.compare_architecture(repo_a, repo_b)
        elif comparison_type == ComparisonType.DEPENDENCIES:
            details = await self.compare_dependencies(repo_a, repo_b)
        elif comparison_type == ComparisonType.API:
            details = await self.compare_apis(repo_a, repo_b)
        elif comparison_type == ComparisonType.DATABASE:
            details = await self.compare_databases(repo_a, repo_b)
        else:
            arch = await self.compare_architecture(repo_a, repo_b)
            deps = await self.compare_dependencies(repo_a, repo_b)
            api = await self.compare_apis(repo_a, repo_b)
            db = await self.compare_databases(repo_a, repo_b)
            details = {
                "architecture": arch,
                "dependencies": deps,
                "api": api,
                "database": db,
            }

        score = self._calculate_similarity(repo_a, repo_b)
        return ComparisonResult(
            repository_a=repo_a.get("id", ""),
            repository_b=repo_b.get("id", ""),
            comparison_type=comparison_type.value,
            differences=details.get("differences", []),
            similarities=details.get("similarities", []),
            score=score,
            recommendations=details.get("recommendations", []),
        )

    async def compare_architecture(
        self, repo_a: dict[str, Any], repo_b: dict[str, Any]
    ) -> dict[str, Any]:
        arch_a = repo_a.get("architecture", {})
        arch_b = repo_b.get("architecture", {})
        similarities = []
        differences = []
        for key in set(arch_a.keys()) | set(arch_b.keys()):
            if arch_a.get(key) == arch_b.get(key):
                similarities.append({"key": key, "value": arch_a.get(key)})
            else:
                differences.append({
                    "key": key,
                    "repo_a": arch_a.get(key),
                    "repo_b": arch_b.get(key),
                })
        return {"similarities": similarities, "differences": differences, "recommendations": []}

    async def compare_dependencies(
        self, repo_a: dict[str, Any], repo_b: dict[str, Any]
    ) -> dict[str, Any]:
        deps_a = set(repo_a.get("dependencies", []))
        deps_b = set(repo_b.get("dependencies", []))
        shared = deps_a & deps_b
        only_a = deps_a - deps_b
        only_b = deps_b - deps_a
        similarities = [{"name": d} for d in shared]
        differences = (
            [{"dependency": d, "only_in": "repo_a"} for d in only_a]
            + [{"dependency": d, "only_in": "repo_b"} for d in only_b]
        )
        return {"similarities": similarities, "differences": differences, "recommendations": []}

    async def compare_apis(
        self, repo_a: dict[str, Any], repo_b: dict[str, Any]
    ) -> dict[str, Any]:
        endpoints_a = set(repo_a.get("endpoints", []))
        endpoints_b = set(repo_b.get("endpoints", []))
        shared = endpoints_a & endpoints_b
        similarities = [{"endpoint": e} for e in shared]
        differences = [
            {"endpoint": e, "only_in": "repo_a"} for e in endpoints_a - endpoints_b
        ] + [
            {"endpoint": e, "only_in": "repo_b"} for e in endpoints_b - endpoints_a
        ]
        return {"similarities": similarities, "differences": differences, "recommendations": []}

    async def compare_databases(
        self, repo_a: dict[str, Any], repo_b: dict[str, Any]
    ) -> dict[str, Any]:
        tables_a = set(repo_a.get("tables", []))
        tables_b = set(repo_b.get("tables", []))
        shared = tables_a & tables_b
        similarities = [{"table": t} for t in shared]
        differences = [
            {"table": t, "only_in": "repo_a"} for t in tables_a - tables_b
        ] + [
            {"table": t, "only_in": "repo_b"} for t in tables_b - tables_a
        ]
        return {"similarities": similarities, "differences": differences, "recommendations": []}

    async def find_shared_components(
        self, repos: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if not repos:
            return []
        all_deps: dict[str, list[str]] = {}
        for repo in repos:
            rid = repo.get("id", "")
            for dep in repo.get("dependencies", []):
                all_deps.setdefault(dep, []).append(rid)
        shared = [
            {"component": dep, "used_by": repos_list}
            for dep, repos_list in all_deps.items()
            if len(repos_list) > 1
        ]
        return shared

    async def find_duplicates(
        self, repos: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        duplicates: list[dict[str, Any]] = []
        for i, a in enumerate(repos):
            for b in repos[i + 1 :]:
                score = self._calculate_similarity(a, b)
                if score > 0.8:
                    duplicates.append({
                        "repo_a": a.get("id", ""),
                        "repo_b": b.get("id", ""),
                        "similarity_score": score,
                    })
        return duplicates

    def _calculate_similarity(self, a: dict[str, Any], b: dict[str, Any]) -> float:
        deps_a = set(a.get("dependencies", []))
        deps_b = set(b.get("dependencies", []))
        endpoints_a = set(a.get("endpoints", []))
        endpoints_b = set(b.get("endpoints", []))
        tables_a = set(a.get("tables", []))
        tables_b = set(b.get("tables", []))

        all_items = deps_a | deps_b | endpoints_a | endpoints_b | tables_a | tables_b
        if not all_items:
            return 0.0

        shared = (deps_a & deps_b) | (endpoints_a & endpoints_b) | (tables_a & tables_b)
        return len(shared) / len(all_items) if all_items else 0.0
