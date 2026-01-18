"""
SAPTA - Decision Engine for PRE-MARKUP Detection.

SAPTA is a hybrid rule-based + ML scoring system that detects
stocks in the PRE-MARKUP phase (before breakout).

Components:
- 6 Analysis Modules (rule-based feature extraction)
- ML Model (learned thresholds and weights)
- Scoring Engine (aggregate scores to decision)
- Planetary Module (Astronacci time projections)

Usage:
    from pulse.core.sapta import SaptaEngine

    engine = SaptaEngine()
    result = await engine.analyze("BBCA")

    print(result.status)  # PRE-MARKUP, SIAP, WATCHLIST, ABAIKAN
    print(result.score)   # 0-100
    print(result.notes)   # Explainability
"""

from pulse.core.sapta.engine import SaptaEngine
from pulse.core.sapta.models import (
    ConfidenceLevel,
    ModuleScore,
    SaptaConfig,
    SaptaResult,
    SaptaStatus,
)

__all__ = [
    "SaptaEngine",
    "SaptaStatus",
    "ConfidenceLevel",
    "ModuleScore",
    "SaptaResult",
    "SaptaConfig",
]
