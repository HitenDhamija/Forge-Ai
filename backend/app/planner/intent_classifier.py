"""Intent classification for the Planning Engine."""

from __future__ import annotations

import re
from typing import Any

from app.core.logging import get_logger
from app.planner.config import get_planner_settings
from app.planner.exceptions import IntentClassificationException
from app.planner.schemas.planner import IntentClassification, IntentType

logger = get_logger(__name__)

INTENT_PATTERNS: dict[IntentType, list[str]] = {
    IntentType.FEATURE_DEVELOPMENT: [
        r"\b(add|create|implement|build|develop|new|feature|extend)\b",
        r"\b(endpoint|api|route|function|class|component|module)\b",
        r"\b(support|handle|integrate|enable)\b",
    ],
    IntentType.BUG_FIX: [
        r"\b(fix|bug|error|issue|broken|crash|failing|debug)\b",
        r"\b(resolve|correct|repair|patch)\b",
        r"\b(not working|doesn't work|won't start|fails)\b",
    ],
    IntentType.REFACTORING: [
        r"\b(refactor|reorganize|restructure|clean|improve|optimize)\b",
        r"\b(extract|move|rename|simplify|consolidate)\b",
        r"\b(code quality|technical debt|maintainability)\b",
    ],
    IntentType.DOCUMENTATION: [
        r"\b(document|docstring|readme|comment|guide|tutorial)\b",
        r"\b(explain|describe|document|annotation)\b",
        r"\b(changelog|release notes|api docs)\b",
    ],
    IntentType.TESTING: [
        r"\b(test|spec|assert|verify|validate|coverage)\b",
        r"\b(unittest|pytest|integration test|e2e)\b",
        r"\b(mock|fixture|test case|test suite)\b",
    ],
    IntentType.DEPLOYMENT: [
        r"\b(deploy|release|publish|ship|launch)\b",
        r"\b(docker|kubernetes|ci/cd|pipeline|container)\b",
        r"\b(production|staging|environment)\b",
    ],
    IntentType.CONFIGURATION: [
        r"\b(config|configure|setting|setup|env|environment)\b",
        r"\b(dependency|package|install|update)\b",
        r"\b(property|option|parameter|variable)\b",
    ],
    IntentType.RESEARCH: [
        r"\b(research|investigate|explore|evaluate|compare)\b",
        r"\b(what is|how does|explain|understand|learn)\b",
        r"\b(analyze|study|review|assess)\b",
    ],
}

KEYWORD_WEIGHTS: dict[str, float] = {
    "urgent": 0.3,
    "critical": 0.3,
    "asap": 0.25,
    "quick": -0.1,
    "simple": -0.2,
    "complex": 0.2,
    "security": 0.2,
    "performance": 0.15,
    "breaking": 0.25,
    "migration": 0.2,
}


class IntentClassifier:
    """Classifies user input into development intent categories.

    Uses pattern matching and keyword analysis to determine the primary
    intent behind a user's request, along with confidence scores and
    optional sub-intents.
    """

    def __init__(self) -> None:
        self._settings = get_planner_settings()
        self._compiled_patterns: dict[IntentType, list[re.Pattern[str]]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for intent, patterns in INTENT_PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def classify(self, user_input: str) -> IntentClassification:
        """Classify user input into an intent type.

        Args:
            user_input: The user's request text.

        Returns:
            IntentClassification with intent type, confidence, and reasoning.

        Raises:
            IntentClassificationException: If classification fails.
        """
        if not user_input or not user_input.strip():
            raise IntentClassificationException("Input cannot be empty")

        text = user_input.strip().lower()

        scores: dict[IntentType, float] = {}
        matched_keywords: dict[IntentType, list[str]] = {}

        for intent, patterns in self._compiled_patterns.items():
            intent_score = 0.0
            intent_keywords: list[str] = []

            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    intent_score += len(matches) * 0.15
                    intent_keywords.extend(matches)

            if intent_keywords:
                scores[intent] = min(intent_score, 1.0)
                matched_keywords[intent] = list(set(intent_keywords))

        keyword_adjustment = self._calculate_keyword_adjustment(text)
        for intent in scores:
            scores[intent] = min(max(scores[intent] + keyword_adjustment, 0.0), 1.0)

        if not scores:
            return IntentClassification(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning="No matching patterns found",
                keywords=[],
            )

        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent, primary_score = sorted_intents[0]

        sub_intents = [
            intent for intent, score in sorted_intents[1:3] if score > 0.3
        ]

        confidence = self._calculate_confidence(primary_score, len(text))

        reasoning = self._build_reasoning(
            primary_intent, primary_score, matched_keywords.get(primary_intent, [])
        )

        return IntentClassification(
            intent=primary_intent,
            confidence=confidence,
            sub_intents=sub_intents,
            reasoning=reasoning,
            keywords=matched_keywords.get(primary_intent, []),
        )

    def classify_batch(self, inputs: list[str]) -> list[IntentClassification]:
        """Classify multiple inputs.

        Args:
            inputs: List of user request texts.

        Returns:
            List of IntentClassification results.
        """
        return [self.classify(text) for text in inputs]

    def _calculate_keyword_adjustment(self, text: str) -> float:
        """Calculate score adjustment based on special keywords."""
        adjustment = 0.0
        for keyword, weight in KEYWORD_WEIGHTS.items():
            if re.search(rf"\b{keyword}\b", text, re.IGNORECASE):
                adjustment += weight
        return adjustment

    def _calculate_confidence(self, raw_score: float, text_length: int) -> float:
        """Calculate final confidence score.

        Factors in raw pattern score and text length (longer inputs
        tend to be more specific).
        """
        length_bonus = min(text_length / 200, 0.1)
        confidence = min(raw_score + length_bonus, 1.0)
        return round(confidence, 2)

    def _build_reasoning(
        self, intent: IntentType, score: float, keywords: list[str]
    ) -> str:
        """Build human-readable reasoning for classification."""
        keyword_str = ", ".join(keywords[:5]) if keywords else "none"
        return (
            f"Classified as {intent.value} "
            f"(score: {score:.2f}) "
            f"based on keywords: {keyword_str}"
        )

    def get_supported_intents(self) -> list[IntentType]:
        """Return list of all supported intent types."""
        return list(IntentType)

    def get_intent_description(self, intent: IntentType) -> str:
        """Return human-readable description for an intent type."""
        descriptions = {
            IntentType.FEATURE_DEVELOPMENT: "Adding new features or functionality",
            IntentType.BUG_FIX: "Fixing bugs, errors, or broken functionality",
            IntentType.REFACTORING: "Improving code structure without changing behavior",
            IntentType.DOCUMENTATION: "Writing or updating documentation",
            IntentType.TESTING: "Adding or improving tests",
            IntentType.DEPLOYMENT: "Deployment and release operations",
            IntentType.CONFIGURATION: "Configuration and setup changes",
            IntentType.RESEARCH: "Research, investigation, or exploration",
            IntentType.UNKNOWN: "Unable to determine specific intent",
        }
        return descriptions.get(intent, "Unknown intent")
