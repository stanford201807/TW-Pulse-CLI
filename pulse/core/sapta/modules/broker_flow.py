"""
Broker Flow Module for SAPTA - Module 7.

Integrates Bandarmology analysis into SAPTA decision engine.
Analyzes broker flow patterns to detect smart money accumulation.
"""

from typing import Any, Optional

import pandas as pd

from pulse.core.sapta.models import ModuleScore
from pulse.core.sapta.modules.base import BaseModule
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class BrokerFlowModule(BaseModule):
    """
    SAPTA Module 7: Broker Flow Analysis.

    Integrates Bandarmology analysis to detect:
    - Smart money accumulation patterns
    - Retail vs institutional flow divergence
    - Broker consistency over multiple days
    - Accumulation phase detection

    Max Score: 15 points

    Scoring:
    - Smart money net positive: +5
    - Retail net negative (contrarian): +3
    - Accumulation streak >= 5 days: +4
    - Markup-ready phase detected: +3
    """

    name = "broker_flow"
    max_score = 15.0

    def __init__(self, days: int = 10):
        """
        Initialize broker flow module.

        Args:
            days: Number of days for broker analysis
        """
        self.days = days
        self._engine = None
        self._last_result = None

    def _get_engine(self):
        """Lazy load bandarmology engine."""
        if self._engine is None:
            try:
                from pulse.core.analysis.bandarmology import BandarmologyEngine

                self._engine = BandarmologyEngine()
            except ImportError:
                log.warning("Bandarmology module not available")
                return None
        return self._engine

    def analyze(self, df: pd.DataFrame, **kwargs) -> ModuleScore:
        """
        Analyze broker flow (sync wrapper).

        Note: This is a sync method but bandarmology requires async.
        For SAPTA integration, use analyze_async instead.

        Returns minimal score if async analysis not available.
        """
        # Check if we have cached result from async analysis
        ticker = kwargs.get("ticker", "")

        if self._last_result and self._last_result.get("ticker") == ticker:
            return self._create_score_from_result(self._last_result)

        # Return neutral score if no cached result
        return self._create_score(
            score=0,
            status=False,
            details="Broker flow analysis requires async (use analyze_async)",
            signals=[],
            raw_features={"broker_flow_available": False},
        )

    async def analyze_async(self, ticker: str, days: Optional[int] = None) -> ModuleScore:
        """
        Analyze broker flow asynchronously.

        Args:
            ticker: Stock ticker
            days: Number of days to analyze (default: self.days)

        Returns:
            ModuleScore with broker flow analysis
        """
        days = days or self.days
        engine = self._get_engine()

        if engine is None:
            return self._create_score(
                score=0,
                status=False,
                details="Bandarmology engine not available",
                signals=[],
                raw_features={"broker_flow_available": False},
            )

        try:
            # Run bandarmology analysis
            result = await engine.analyze(ticker, days=days)

            if result is None:
                return self._create_score(
                    score=0,
                    status=False,
                    details="No broker data available (check Stockbit token)",
                    signals=["No broker data"],
                    raw_features={"broker_flow_available": False},
                )

            # Cache result for sync access
            self._last_result = {
                "ticker": ticker,
                "result": result,
            }

            return self._create_score_from_bandarmology(result)

        except Exception as e:
            log.warning(f"Broker flow analysis failed for {ticker}: {e}")
            return self._create_score(
                score=0,
                status=False,
                details=f"Analysis failed: {str(e)}",
                signals=[],
                raw_features={"broker_flow_available": False, "error": str(e)},
            )

    def _create_score_from_bandarmology(self, result) -> ModuleScore:
        """Create ModuleScore from BandarmologyResult."""
        score = 0.0
        signals = []

        # 1. Smart money net positive: +5 points
        if result.smart_money_net_total > 0:
            sm_score = min(5.0, 5.0 * (result.smart_money_net_total / 50_000_000_000))
            score += sm_score
            signals.append(f"Smart money NET BUY (+{sm_score:.1f})")
        elif result.smart_money_net_total < 0:
            signals.append("Smart money NET SELL (0)")

        # 2. Retail net negative (contrarian bullish): +3 points
        if result.retail_net_total < 0:
            contrarian_score = min(3.0, 3.0 * (abs(result.retail_net_total) / 20_000_000_000))
            score += contrarian_score
            signals.append(f"Retail selling (contrarian +{contrarian_score:.1f})")
        elif result.retail_net_total > 0 and result.smart_money_net_total < 0:
            signals.append("RETAIL TRAP warning")

        # 3. Accumulation streak: +4 points
        streak = result.accumulation_streak
        if streak >= 7:
            score += 4.0
            signals.append(f"Strong accumulation streak {streak} days (+4)")
        elif streak >= 5:
            score += 3.0
            signals.append(f"Accumulation streak {streak} days (+3)")
        elif streak >= 3:
            score += 1.5
            signals.append(f"Accumulation streak {streak} days (+1.5)")
        elif streak <= -3:
            signals.append(f"Distribution streak {abs(streak)} days")

        # 4. Phase detection: +3 points
        from pulse.core.analysis.bandarmology.models import AccumulationPhase

        phase_scores = {
            AccumulationPhase.MARKUP_READY: 3.0,
            AccumulationPhase.LATE_ACCUMULATION: 2.0,
            AccumulationPhase.MID_ACCUMULATION: 1.0,
            AccumulationPhase.EARLY_ACCUMULATION: 0.5,
        }
        phase_score = phase_scores.get(result.accumulation_phase, 0.0)
        if phase_score > 0:
            score += phase_score
            signals.append(f"{result.accumulation_phase.value} (+{phase_score})")

        # Distribution warning penalty
        if result.distribution_warning:
            score = max(0, score - 3.0)
            signals.append("DISTRIBUTION WARNING (-3)")

        # Cap at max score
        score = min(score, self.max_score)

        # Determine status
        status = score >= (self.max_score * 0.5)  # 50% threshold

        # Details
        details = f"Broker Flow: {result.accumulation_phase.value}, SM Net: {result.smart_money_net_total / 1e9:.1f}B"

        # Raw features for ML
        raw_features = {
            "broker_flow_available": True,
            "smart_money_net": result.smart_money_net_total,
            "retail_net": result.retail_net_total,
            "foreign_net": result.foreign_net_total,
            "accumulation_streak": result.accumulation_streak,
            "phase": result.accumulation_phase.value,
            "flow_momentum_score": result.flow_momentum_score,
            "markup_readiness_score": result.markup_readiness_score,
            "top5_consistency": result.top5_consistency_score,
            "distribution_warning": result.distribution_warning,
            "pattern_count": len(result.patterns),
        }

        return self._create_score(
            score=score,
            status=status,
            details=details,
            signals=signals,
            raw_features=raw_features,
        )

    def _create_score_from_result(self, cached: dict) -> ModuleScore:
        """Create ModuleScore from cached result."""
        result = cached.get("result")
        if result:
            return self._create_score_from_bandarmology(result)
        return self._create_score(
            score=0,
            status=False,
            details="No cached result",
            signals=[],
            raw_features={},
        )
