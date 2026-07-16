"""Learning Engine for long-term experience memory and pattern extraction.

Processes completed workflows to extract engineering knowledge,
store reusable patterns, analyze failures, and generate recommendations.
"""

from app.learning.learning_service import LearningService
from app.learning.experience_collector import ExperienceCollector
from app.learning.pattern_extractor import PatternExtractor
from app.learning.knowledge_compressor import KnowledgeCompressor
from app.learning.failure_analyzer import FailureAnalyzer
from app.learning.recommendation_engine import RecommendationEngine
from app.learning.experience_memory import ExperienceMemory

__all__ = [
    "LearningService",
    "ExperienceCollector",
    "PatternExtractor",
    "KnowledgeCompressor",
    "FailureAnalyzer",
    "RecommendationEngine",
    "ExperienceMemory",
]
