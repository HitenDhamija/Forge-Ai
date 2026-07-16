"""Compresses similar experiences into reusable engineering patterns.

Groups similar experiences by type, technology, and outcome, then merges
them into generalized patterns to avoid duplicate memories and create
higher-level knowledge.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExperienceType(str, Enum):
    """Categories of engineering experience."""

    ARCHITECTURE = "architecture"
    BUG_FIX = "bug_fix"
    DEPLOYMENT = "deployment"
    DATABASE = "database"
    TESTING = "testing"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"


class OutcomeType(str, Enum):
    """Possible outcomes of an experience."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


# ---------------------------------------------------------------------------
# Pydantic schemas (public API contracts)
# ---------------------------------------------------------------------------


class CompressionConfig(BaseModel):
    """Configuration for the knowledge compressor."""

    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score to consider experiences mergeable.",
    )
    type_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight given to experience-type match.",
    )
    tech_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight given to technology overlap.",
    )
    outcome_weight: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Weight given to outcome match.",
    )
    tag_weight: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Weight given to tag overlap.",
    )
    text_weight: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Weight given to textual similarity.",
    )
    min_group_size: int = Field(
        default=2,
        ge=1,
        description="Minimum experiences in a group to trigger compression.",
    )
    max_genericity: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Maximum allowed genericity score before detail loss is flagged.",
    )


class CompressedExperience(BaseModel):
    """A single compressed experience produced by the compressor."""

    id: str | None = None
    experience_type: str
    title: str
    description: str
    solution: str
    outcome: str
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    reuse_potential: float = 0.5
    generalization_score: float = 0.5
    source_ids: list[str] = Field(default_factory=list)
    source_count: int = 0
    metadata: dict = Field(default_factory=dict)


class CompressionResult(BaseModel):
    """Result of a full compression run."""

    compressed: list[CompressedExperience]
    total_input: int
    total_output: int
    groups_formed: int
    duplicates_removed: int


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


@dataclass
class _SimilarityPair:
    """Pair of experiences with a computed similarity score."""

    index_a: int
    index_b: int
    score: float


@dataclass
class _CompressionGroup:
    """A cluster of similar experiences pending merge."""

    indices: list[int]
    avg_similarity: float


# ---------------------------------------------------------------------------
# Helpers (module-level, pure functions)
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric tokens from text."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two token sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------------------
# KnowledgeCompressor
# ---------------------------------------------------------------------------


class KnowledgeCompressor:
    """Compresses similar experiences into reusable engineering patterns.

    The compressor groups experiences by type, technology, and outcome,
    then merges each group into a single generalized experience while
    preserving the most valuable information from every member.
    """

    def __init__(self, config: CompressionConfig | None = None) -> None:
        self.config = config or CompressionConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def compress_experiences(
        self,
        experiences: list[dict],
    ) -> list[dict]:
        """Compress a batch of similar experiences into generalized patterns.

        1. Find all pairs above the similarity threshold.
        2. Cluster them into groups.
        3. Merge each group.
        4. Return merged experiences plus untouched originals.
        """
        if len(experiences) < 2:
            return list(experiences)

        logger.info(
            "Starting compression",
            extra={"count": len(experiences)},
        )

        pairs = await self._find_all_pairs(experiences)
        groups = self._cluster_pairs(pairs, len(experiences))

        merged_indices: set[int] = set()
        compressed: list[dict] = []

        for group in groups:
            if len(group.indices) < self.config.min_group_size:
                continue
            group_experiences = [experiences[i] for i in group.indices]
            merged = await self.merge_experiences(group_experiences)
            compressed.append(merged)
            merged_indices.update(group.indices)
            logger.debug(
                "Merged group",
                extra={
                    "size": len(group.indices),
                    "avg_similarity": round(group.avg_similarity, 3),
                },
            )

        for i, exp in enumerate(experiences):
            if i not in merged_indices:
                compressed.append(exp)

        logger.info(
            "Compression complete",
            extra={
                "input": len(experiences),
                "output": len(compressed),
                "groups": len(
                    [g for g in groups if len(g.indices) >= self.config.min_group_size]
                ),
            },
        )
        return compressed

    async def find_similar_experiences(
        self,
        experience: dict,
        existing: list[dict],
    ) -> list[dict]:
        """Find experiences in *existing* similar to *experience*.

        Returns experiences whose similarity meets or exceeds the threshold,
        ordered from most to least similar.
        """
        results: list[tuple[dict, float]] = []
        for other in existing:
            score = self._calculate_similarity(experience, other)
            if score >= self.config.similarity_threshold:
                results.append((other, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return [exp for exp, _ in results]

    async def merge_experiences(self, experiences: list[dict]) -> dict:
        """Merge multiple experiences into a single generalized experience.

        Preserves the highest-confidence values, unions tags/technologies,
        and produces a merged solution description.
        """
        if not experiences:
            raise ValueError("Cannot merge an empty list of experiences")
        if len(experiences) == 1:
            return dict(experiences[0])

        # Pick the base (highest confidence) as the starting point.
        sorted_exp = sorted(
            experiences,
            key=lambda e: e.get("confidence", 0.5),
            reverse=True,
        )
        base = dict(sorted_exp[0])

        merged_tech = self._merge_tags(
            [e.get("technologies", []) for e in experiences]
        )
        merged_tags = self._merge_tags(
            [e.get("tags", []) for e in experiences]
        )
        merged_solution = self._merge_solutions(experiences)
        merged_confidence = self._update_confidence(base, experiences)

        # Preserve source provenance.
        source_ids: list[str] = []
        for e in experiences:
            sid = e.get("id")
            if sid:
                source_ids.append(sid)
            for s in e.get("source_ids", []):
                if s not in source_ids:
                    source_ids.append(s)

        # Generalization score rises when many diverse inputs converge.
        avg_gen = sum(
            e.get("generalization_score", 0.5) for e in experiences
        ) / len(experiences)
        diversity_bonus = min(0.15, 0.03 * (len(experiences) - 1))
        generalization = min(1.0, avg_gen + diversity_bonus)

        # Reuse potential is the max across the group.
        reuse = max(e.get("reuse_potential", 0.5) for e in experiences)

        merged: dict = {
            "experience_type": base.get("experience_type"),
            "title": _make_general_title(experiences),
            "description": _make_general_description(experiences),
            "solution": merged_solution,
            "outcome": _majority_outcome(experiences),
            "technologies": merged_tech,
            "tags": merged_tags,
            "confidence": merged_confidence,
            "reuse_potential": reuse,
            "generalization_score": generalization,
            "source_ids": source_ids,
            "source_count": len(experiences),
            "metadata": {
                "merged_from_count": len(experiences),
                "genericity": round(
                    1.0 - generalization, 3
                ),
                **base.get("metadata", {}),
            },
        }
        return merged

    async def deduplicate_patterns(self, patterns: list[dict]) -> list[dict]:
        """Remove duplicate patterns, keeping the highest-confidence variant."""
        if len(patterns) <= 1:
            return list(patterns)

        # Sort by confidence descending so we keep the best.
        ranked = sorted(
            patterns,
            key=lambda p: p.get("confidence", 0.5),
            reverse=True,
        )
        kept: list[dict] = []
        seen_tokens: list[set[str]] = []

        for pat in ranked:
            pat_text = f"{pat.get('name', '')} {pat.get('description', '')}"
            pat_tokens = _tokenize(pat_text)
            is_dup = False
            for existing_tokens in seen_tokens:
                if _jaccard(pat_tokens, existing_tokens) >= self.config.similarity_threshold:
                    is_dup = True
                    break
            if not is_dup:
                kept.append(pat)
                seen_tokens.append(pat_tokens)

        removed = len(patterns) - len(kept)
        if removed:
            logger.info(
                "Deduplicated patterns",
                extra={"removed": removed, "kept": len(kept)},
            )
        return kept

    # ------------------------------------------------------------------
    # Similarity
    # ------------------------------------------------------------------

    def _calculate_similarity(self, a: dict, b: dict) -> float:
        """Weighted similarity score between two experience dicts.

        Combines type match, technology overlap, outcome match,
        tag overlap, and textual similarity into a single [0, 1] score.
        """
        cfg = self.config

        # Type similarity (exact match).
        type_sim = 1.0 if a.get("experience_type") == b.get("experience_type") else 0.0

        # Technology overlap (Jaccard).
        tech_a = set(a.get("technologies", []))
        tech_b = set(b.get("technologies", []))
        tech_sim = _jaccard(tech_a, tech_b)

        # Outcome match.
        outcome_sim = (
            1.0 if a.get("outcome") == b.get("outcome") else 0.0
        )

        # Tag overlap (Jaccard).
        tag_a = set(a.get("tags", []))
        tag_b = set(b.get("tags", []))
        tag_sim = _jaccard(tag_a, tag_b)

        # Textual similarity over title + description + solution.
        text_a = _tokenize(
            f"{a.get('title', '')} {a.get('description', '')} {a.get('solution', '')}"
        )
        text_b = _tokenize(
            f"{b.get('title', '')} {b.get('description', '')} {b.get('solution', '')}"
        )
        text_sim = _jaccard(text_a, text_b)

        score = (
            cfg.type_weight * type_sim
            + cfg.tech_weight * tech_sim
            + cfg.outcome_weight * outcome_sim
            + cfg.tag_weight * tag_sim
            + cfg.text_weight * text_sim
        )
        return round(score, 4)

    def _should_compress(self, a: dict, b: dict) -> bool:
        """Decide whether two experiences should be compressed together."""
        return self._calculate_similarity(a, b) >= self.config.similarity_threshold

    # ------------------------------------------------------------------
    # Internal merge helpers
    # ------------------------------------------------------------------

    def _merge_solutions(self, experiences: list[dict]) -> str:
        """Merge solution descriptions into a single generalized text.

        The highest-confidence solution is used as the base, then
        unique details from other solutions are appended when they
        add non-redundant information.
        """
        sorted_exp = sorted(
            experiences,
            key=lambda e: e.get("confidence", 0.5),
            reverse=True,
        )
        base_solution = sorted_exp[0].get("solution", "")
        base_tokens = _tokenize(base_solution)

        additions: list[str] = []
        for exp in sorted_exp[1:]:
            sol = exp.get("solution", "")
            sol_tokens = _tokenize(sol)
            # Only append if this solution brings substantially new tokens.
            new_tokens = sol_tokens - base_tokens
            if len(new_tokens) > 0.3 * len(sol_tokens):
                # Summarize the delta: take the first sentence that contains new terms.
                for sentence in re.split(r"[.!?]+", sol):
                    sentence_tokens = _tokenize(sentence)
                    if sentence_tokens & new_tokens:
                        addition = sentence.strip()
                        if addition and addition not in base_solution:
                            additions.append(addition.rstrip("."))
                        break

        if additions:
            unique_additions = list(dict.fromkeys(additions))
            return f"{base_solution.rstrip('.')}. " + ". ".join(unique_additions) + "."
        return base_solution

    def _merge_tags(self, tag_lists: list[list[str]]) -> list[str]:
        """Union all tags, preserving order of first appearance."""
        seen: dict[str, None] = {}
        for tags in tag_lists:
            for tag in tags:
                if tag not in seen:
                    seen[tag] = None
        return list(seen.keys())

    def _update_confidence(self, merged: dict, originals: list[dict]) -> float:
        """Update confidence after merging.

        Confidence increases when multiple sources agree and the original
        confidence scores are consistently high.  It decreases when
        sources disagree on outcome or have low individual confidence.
        """
        if len(originals) <= 1:
            return merged.get("confidence", 0.5)

        avg_conf = sum(
            e.get("confidence", 0.5) for e in originals
        ) / len(originals)

        # Outcome agreement bonus.
        outcomes = [e.get("outcome", "success") for e in originals]
        most_common = max(set(outcomes), key=outcomes.count)
        agreement = outcomes.count(most_common) / len(outcomes)

        # More sources → more confidence, with diminishing returns.
        source_bonus = min(0.2, 0.04 * (len(originals) - 1))

        new_conf = avg_conf * 0.6 + agreement * 0.2 + source_bonus
        return round(min(1.0, max(0.0, new_conf)), 3)

    # ------------------------------------------------------------------
    # Pair-finding and clustering (private)
    # ------------------------------------------------------------------

    async def _find_all_pairs(
        self,
        experiences: list[dict],
    ) -> list[_SimilarityPair]:
        """Compute similarity for all unique pairs."""
        pairs: list[_SimilarityPair] = []
        n = len(experiences)
        for i in range(n):
            for j in range(i + 1, n):
                score = self._calculate_similarity(experiences[i], experiences[j])
                if score >= self.config.similarity_threshold:
                    pairs.append(_SimilarityPair(i, j, score))
        return pairs

    def _cluster_pairs(
        self,
        pairs: list[_SimilarityPair],
        total: int,
    ) -> list[_CompressionGroup]:
        """Union-find clustering over similarity pairs."""
        parent = list(range(total))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        for p in pairs:
            union(p.index_a, p.index_b)

        # Collect clusters.
        clusters: dict[int, list[int]] = {}
        for i in range(total):
            root = find(i)
            clusters.setdefault(root, []).append(i)

        # Build groups with average similarity.
        groups: list[_CompressionGroup] = []
        for members in clusters.values():
            member_set = set(members)
            relevant_scores = [
                p.score
                for p in pairs
                if p.index_a in member_set and p.index_b in member_set
            ]
            avg = sum(relevant_scores) / len(relevant_scores) if relevant_scores else 0.0
            groups.append(_CompressionGroup(indices=members, avg_similarity=avg))

        groups.sort(key=lambda g: g.avg_similarity, reverse=True)
        return groups


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _make_general_title(experiences: list[dict]) -> str:
    """Create a generalized title from a group of experiences."""
    if len(experiences) == 1:
        return experiences[0].get("title", "Untitled")
    # Use the first ~3 words shared across titles, or fall back.
    all_titles = [e.get("title", "") for e in experiences]
    first = all_titles[0]
    words = first.split()
    if len(words) <= 4:
        return f"Generalized: {first}"
    return " ".join(words[:4]) + " pattern"


def _make_general_description(experiences: list[dict]) -> str:
    """Create a generalized description from a group of experiences."""
    if len(experiences) == 1:
        return experiences[0].get("description", "")
    longest = max(experiences, key=lambda e: len(e.get("description", "")))
    base_desc = longest.get("description", "")
    count = len(experiences)
    prefix = f"Pattern observed across {count} experiences. "
    return prefix + base_desc


def _majority_outcome(experiences: list[dict]) -> str:
    """Return the most common outcome, defaulting to 'success'."""
    outcomes = [e.get("outcome", "success") for e in experiences]
    return max(set(outcomes), key=outcomes.count) if outcomes else "success"
