"""
SAPTA Engine - Main orchestrator for PRE-MARKUP detection.

Runs all 6 analysis modules, aggregates scores, and determines status.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any

import pandas as pd

from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.sapta.models import (
    ConfidenceLevel,
    ModuleScore,
    SaptaConfig,
    SaptaResult,
    SaptaStatus,
)
from pulse.core.sapta.modules import (
    AntiDistributionModule,
    BBSqueezeModule,
    CompressionModule,
    ElliottModule,
    SupplyAbsorptionModule,
    TimeProjectionModule,
)
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class SaptaEngine:
    """
    SAPTA Decision Engine.
    
    Orchestrates 6 analysis modules to detect PRE-MARKUP phase:
    1. Supply Absorption - Detects smart money accumulation
    2. Compression - Volatility contraction before expansion
    3. BB Squeeze - Bollinger Band squeeze detection
    4. Elliott Wave - Wave position and Fibonacci retracement
    5. Time Projection - Fibonacci time windows + planetary aspects
    6. Anti-Distribution - Filters out distribution patterns
    
    Output: Score 0-100 with status (PRE-MARKUP, SIAP, WATCHLIST, ABAIKAN)
    """

    def __init__(self, config: SaptaConfig | None = None, auto_load_model: bool = True):
        """
        Initialize SAPTA Engine.
        
        Args:
            config: Optional configuration (uses defaults if not provided)
            auto_load_model: Whether to auto-load trained model if available
        """
        self.config = config or SaptaConfig()
        self.fetcher = YFinanceFetcher()

        # Initialize all modules
        self.modules = {
            "absorption": SupplyAbsorptionModule(),
            "compression": CompressionModule(),
            "bb_squeeze": BBSqueezeModule(),
            "elliott": ElliottModule(),
            "time_projection": TimeProjectionModule(),
            "anti_distribution": AntiDistributionModule(),
        }

        # Module weights (from config, can be learned by ML)
        self.weights = {
            "absorption": self.config.weight_absorption,
            "compression": self.config.weight_compression,
            "bb_squeeze": self.config.weight_bb_squeeze,
            "elliott": self.config.weight_elliott,
            "time_projection": self.config.weight_time_projection,
            "anti_distribution": self.config.weight_anti_distribution,
        }

        # ML model (will be loaded if available)
        self._ml_model = None
        self._ml_loaded = False

        # Auto-load trained model if available
        if auto_load_model:
            self._auto_load_model()

    async def analyze(
        self,
        ticker: str,
        timeframe: str = "D",
        df: pd.DataFrame | None = None,
    ) -> SaptaResult | None:
        """
        Analyze a stock for PRE-MARKUP signals.
        
        Args:
            ticker: Stock ticker (e.g., "BBCA")
            timeframe: Timeframe for analysis (default: "D" for daily)
            df: Optional pre-fetched DataFrame (for batch processing)
            
        Returns:
            SaptaResult with scores, status, and explainability
        """
        ticker = ticker.upper().strip()

        try:
            # Fetch data if not provided
            if df is None:
                df = self.fetcher.get_history_df(ticker, period="1y")

            if df is None or len(df) < self.config.min_history_days:
                log.warning(f"Insufficient data for {ticker}: need {self.config.min_history_days} days")
                return None

            # Run all modules
            module_scores = await self._run_modules(df)

            # Aggregate scores
            result = self._aggregate_scores(ticker, timeframe, module_scores, df)

            # Apply ML model if available
            if self._ml_model is not None:
                result = self._apply_ml_prediction(result)

            # Determine final status
            result = self._determine_status(result)

            return result

        except Exception as e:
            log.error(f"SAPTA analysis failed for {ticker}: {e}")
            return None

    async def scan(
        self,
        tickers: list[str],
        min_status: SaptaStatus = SaptaStatus.WATCHLIST,
        batch_fetch: bool = True,
        progress_callback: Callable | None = None,
    ) -> list[SaptaResult]:
        """
        Scan multiple stocks and filter by minimum status.
        
        Args:
            tickers: List of stock tickers to scan
            min_status: Minimum status to include in results
            batch_fetch: Pre-fetch data in batches for speed
            progress_callback: Optional callback(current, total) for progress
            
        Returns:
            List of SaptaResult for stocks meeting criteria
        """
        results = []
        status_order = [
            SaptaStatus.ABAIKAN,
            SaptaStatus.WATCHLIST,
            SaptaStatus.SIAP,
            SaptaStatus.PRE_MARKUP,
        ]
        min_index = status_order.index(min_status)

        # Pre-fetch data in batches using yfinance
        data_cache: dict[str, pd.DataFrame] = {}
        if batch_fetch and len(tickers) > 10:
            try:
                from pulse.core.sapta.ml.data_loader import SaptaDataLoader
                loader = SaptaDataLoader()
                data_cache = loader.get_multiple_stocks(
                    tickers,
                    period="1y",
                    min_rows=self.config.min_history_days
                )
                log.info(f"Pre-fetched {len(data_cache)} stocks for scanning")
            except Exception as e:
                log.debug(f"Batch fetch failed, will fetch individually: {e}")

        total = len(tickers)
        for i, ticker in enumerate(tickers):
            try:
                # Use cached data if available
                df = data_cache.get(ticker)
                result = await self.analyze(ticker, df=df)

                if result:
                    result_index = status_order.index(result.status)
                    if result_index >= min_index:
                        results.append(result)

                # Progress callback
                if progress_callback and (i + 1) % 50 == 0:
                    progress_callback(i + 1, total)

            except Exception as e:
                log.debug(f"Scan failed for {ticker}: {e}")
                continue

        # Sort by score descending
        results.sort(key=lambda x: x.final_score, reverse=True)

        return results

    async def _run_modules(self, df: pd.DataFrame) -> dict[str, ModuleScore]:
        """Run all analysis modules on the data."""
        scores = {}

        for name, module in self.modules.items():
            try:
                score = module.analyze(df)
                scores[name] = score
            except Exception as e:
                log.debug(f"Module {name} failed: {e}")
                # Create empty score on failure
                scores[name] = ModuleScore(
                    module_name=name,
                    score=0.0,
                    max_score=module.max_score,
                    status=False,
                    details=f"Analysis failed: {str(e)[:50]}",
                    signals=[],
                    raw_features={},
                )

        return scores

    def _aggregate_scores(
        self,
        ticker: str,
        timeframe: str,
        module_scores: dict[str, ModuleScore],
        df: pd.DataFrame,
    ) -> SaptaResult:
        """Aggregate module scores into final result."""
        # Calculate weighted total
        total_score = 0.0
        total_weight = 0.0

        for name, score in module_scores.items():
            weight = self.weights.get(name, 1.0)
            total_score += score.score * weight
            total_weight += score.max_score * weight

        # Normalize to 0-100 scale
        if total_weight > 0:
            weighted_score = (total_score / total_weight) * 100
        else:
            weighted_score = 0.0

        # Collect notes and signals from modules
        notes = []
        warnings = []
        all_features = {}

        for name, score in module_scores.items():
            # Add signals as notes
            for signal in score.signals:
                notes.append(signal)

            # Collect raw features with module prefix
            for feat_name, feat_val in score.raw_features.items():
                all_features[f"{name}_{feat_name}"] = feat_val

            # Check for warnings (failed modules)
            if not score.status and score.score == 0:
                warnings.append(f"{name}: {score.details}")

        # Get Elliott wave info if available
        elliott_score = module_scores.get("elliott")
        wave_phase = None
        fib_retracement = None
        if elliott_score:
            wave_phase = elliott_score.raw_features.get("wave_phase")
            fib_retracement = elliott_score.raw_features.get("fib_retracement")

        # Get time projection info if available
        time_score = module_scores.get("time_projection")
        projected_window = None
        projected_dates = None
        days_to_window = None
        if time_score:
            projected_window = time_score.raw_features.get("projected_window")
            days_since_low = time_score.raw_features.get("days_since_significant_low", 0)
            nearest_fib = time_score.raw_features.get("nearest_fib")
            if nearest_fib is not None and days_since_low is not None and nearest_fib > days_since_low:
                days_to_window = int(nearest_fib) - int(days_since_low)

        # Check for false breakout penalty
        penalties = []
        penalty_score = 0.0
        anti_dist = module_scores.get("anti_distribution")
        if anti_dist and anti_dist.raw_features.get("false_breakout", False):
            penalties.append("False breakout detected")
            penalty_score += self.config.false_break_penalty

        # Build result
        result = SaptaResult(
            ticker=ticker,
            timeframe=timeframe,
            analyzed_at=datetime.now(),
            total_score=total_score,
            weighted_score=weighted_score,
            max_possible_score=100.0,
            absorption=self._score_to_dict(module_scores.get("absorption")),
            compression=self._score_to_dict(module_scores.get("compression")),
            bb_squeeze=self._score_to_dict(module_scores.get("bb_squeeze")),
            elliott=self._score_to_dict(module_scores.get("elliott")),
            time_projection=self._score_to_dict(module_scores.get("time_projection")),
            anti_distribution=self._score_to_dict(module_scores.get("anti_distribution")),
            status=SaptaStatus.ABAIKAN,  # Will be set in _determine_status
            confidence=ConfidenceLevel.LOW,
            projected_breakout_window=projected_window,
            projected_dates=projected_dates,
            days_to_window=days_to_window,
            wave_phase=wave_phase,
            fib_retracement=fib_retracement,
            notes=notes[:10],  # Limit notes
            reasons=[],
            warnings=warnings,
            penalties=penalties,
            penalty_score=penalty_score,
            features=all_features,
        )

        return result

    def _score_to_dict(self, score: ModuleScore | None) -> dict[str, Any] | None:
        """Convert ModuleScore to dict for serialization."""
        if score is None:
            return None
        return {
            "score": round(score.score, 2),
            "max_score": score.max_score,
            "status": score.status,
            "details": score.details,
            "signals": score.signals,
        }

    def _determine_status(self, result: SaptaResult) -> SaptaResult:
        """Determine final status based on score thresholds."""
        final = result.final_score

        # Determine status
        if final >= self.config.threshold_pre_markup:
            result.status = SaptaStatus.PRE_MARKUP
            result.confidence = ConfidenceLevel.HIGH
            result.reasons.append(f"Score {final:.1f} >= {self.config.threshold_pre_markup} (PRE-MARKUP threshold)")
        elif final >= self.config.threshold_siap:
            result.status = SaptaStatus.SIAP
            result.confidence = ConfidenceLevel.MEDIUM
            result.reasons.append(f"Score {final:.1f} >= {self.config.threshold_siap} (SIAP threshold)")
        elif final >= self.config.threshold_watchlist:
            result.status = SaptaStatus.WATCHLIST
            result.confidence = ConfidenceLevel.LOW
            result.reasons.append(f"Score {final:.1f} >= {self.config.threshold_watchlist} (WATCHLIST threshold)")
        else:
            result.status = SaptaStatus.ABAIKAN
            result.confidence = ConfidenceLevel.LOW
            result.reasons.append(f"Score {final:.1f} < {self.config.threshold_watchlist} (below threshold)")

        # Boost confidence if multiple modules agree
        active_modules = sum(
            1 for m in [result.absorption, result.compression, result.bb_squeeze,
                       result.elliott, result.time_projection, result.anti_distribution]
            if m and m.get("status", False)
        )

        if active_modules >= 5:
            if result.confidence == ConfidenceLevel.MEDIUM:
                result.confidence = ConfidenceLevel.HIGH
            result.reasons.append(f"{active_modules}/6 modules confirm pattern")
        elif active_modules >= 4:
            result.reasons.append(f"{active_modules}/6 modules confirm pattern")

        return result

    def _apply_ml_prediction(self, result: SaptaResult) -> SaptaResult:
        """Apply ML model prediction if available."""
        if self._ml_model is None:
            return result

        try:
            # Extract features in correct order
            feature_vector = self._extract_feature_vector(result.features)

            # Get prediction probability
            proba = self._ml_model.predict_proba([feature_vector])[0][1]
            result.ml_probability = float(proba)

            # Adjust confidence based on ML prediction
            if proba >= 0.7:
                result.confidence = ConfidenceLevel.HIGH
                result.notes.append(f"ML confidence: {proba:.0%}")
            elif proba >= 0.5:
                result.notes.append(f"ML confidence: {proba:.0%}")
            else:
                result.warnings.append(f"ML confidence low: {proba:.0%}")

        except Exception as e:
            log.debug(f"ML prediction failed: {e}")

        return result

    def _extract_feature_vector(self, features: dict[str, float]) -> list[float]:
        """Extract feature vector in consistent order for ML model."""
        # Define expected feature order (must match training)
        feature_names = sorted(features.keys())
        return [features.get(name, 0.0) for name in feature_names]

    def _auto_load_model(self) -> None:
        """Auto-load trained model and thresholds if available."""
        import json
        from pathlib import Path

        data_dir = Path(__file__).parent / "data"
        model_path = data_dir / "sapta_model.pkl"
        thresholds_path = data_dir / "thresholds.json"

        # Load model
        if model_path.exists():
            self.load_ml_model(str(model_path))

        # Load learned thresholds
        if thresholds_path.exists():
            try:
                with open(thresholds_path) as f:
                    thresholds = json.load(f)

                self.config.threshold_pre_markup = thresholds.get("pre_markup", 80.0)
                self.config.threshold_siap = thresholds.get("siap", 65.0)
                self.config.threshold_watchlist = thresholds.get("watchlist", 50.0)

                log.info(f"Loaded learned thresholds: PRE-MARKUP>={self.config.threshold_pre_markup:.1f}, "
                        f"SIAP>={self.config.threshold_siap:.1f}, WATCHLIST>={self.config.threshold_watchlist:.1f}")
            except Exception as e:
                log.debug(f"Could not load thresholds: {e}")

    def load_ml_model(self, model_path: str) -> bool:
        """Load trained ML model from disk."""
        try:
            import joblib
            self._ml_model = joblib.load(model_path)
            self._ml_loaded = True
            log.info(f"Loaded ML model from {model_path}")
            return True
        except Exception as e:
            log.warning(f"Could not load ML model: {e}")
            return False

    def format_result(
        self,
        result: SaptaResult,
        detailed: bool = False,
    ) -> str:
        """
        Format SaptaResult for display.
        
        Args:
            result: SAPTA analysis result
            detailed: Whether to show detailed module breakdown
            
        Returns:
            Formatted string for terminal display
        """
        # Status emoji/indicator
        status_icons = {
            SaptaStatus.PRE_MARKUP: "[PRE-MARKUP]",
            SaptaStatus.SIAP: "[SIAP]",
            SaptaStatus.WATCHLIST: "[WATCHLIST]",
            SaptaStatus.ABAIKAN: "[ABAIKAN]",
        }

        confidence_icons = {
            ConfidenceLevel.HIGH: "HIGH",
            ConfidenceLevel.MEDIUM: "MEDIUM",
            ConfidenceLevel.LOW: "LOW",
        }

        lines = []

        # Header
        lines.append(f"SAPTA Analysis: {result.ticker}")
        lines.append("=" * 40)

        # Main result
        lines.append(f"Status: {status_icons.get(result.status, result.status.value)}")
        lines.append(f"Score: {result.final_score:.1f}/100")
        lines.append(f"Confidence: {confidence_icons.get(result.confidence, result.confidence.value)}")

        if result.ml_probability is not None:
            lines.append(f"ML Probability: {result.ml_probability:.1%}")

        # Wave phase
        if result.wave_phase:
            lines.append(f"Wave Phase: {result.wave_phase}")

        if result.fib_retracement:
            lines.append(f"Fib Retracement: {result.fib_retracement:.1%}")

        # Time projection
        if result.projected_breakout_window:
            lines.append(f"Projected Window: {result.projected_breakout_window}")
        if result.days_to_window:
            lines.append(f"Days to Window: {result.days_to_window}")

        # Module breakdown (if detailed)
        if detailed:
            lines.append("")
            lines.append("Module Breakdown")
            lines.append("-" * 30)

            modules = [
                ("Absorption", result.absorption),
                ("Compression", result.compression),
                ("BB Squeeze", result.bb_squeeze),
                ("Elliott", result.elliott),
                ("Time Projection", result.time_projection),
                ("Anti-Distribution", result.anti_distribution),
            ]

            for name, data in modules:
                if data:
                    status_mark = "+" if data.get("status") else "-"
                    score = data.get("score", 0)
                    max_score = data.get("max_score", 0)
                    lines.append(f"  [{status_mark}] {name}: {score:.1f}/{max_score}")

        # Notes (signals)
        if result.notes:
            lines.append("")
            lines.append("Signals")
            lines.append("-" * 30)
            for note in result.notes[:7]:
                lines.append(f"  - {note}")

        # Warnings
        if result.warnings:
            lines.append("")
            lines.append("Warnings")
            for warning in result.warnings[:3]:
                lines.append(f"  ! {warning}")

        # Penalties
        if result.penalties:
            lines.append("")
            lines.append(f"Penalties: -{result.penalty_score:.1f}")
            for penalty in result.penalties:
                lines.append(f"  - {penalty}")

        return "\n".join(lines)

    def format_scan_results(
        self,
        results: list[SaptaResult],
        title: str = "SAPTA Scan Results",
    ) -> str:
        """Format scan results as a table."""
        if not results:
            return "No stocks found matching SAPTA criteria."

        lines = [title, "=" * 60]

        # Header
        lines.append(f"{'Ticker':<8} {'Status':<12} {'Score':>8} {'Confidence':<10} {'Wave':<8}")
        lines.append("-" * 60)

        for r in results:
            wave = r.wave_phase[:7] if r.wave_phase else "-"
            lines.append(
                f"{r.ticker:<8} {r.status.value:<12} {r.final_score:>7.1f} "
                f"{r.confidence.value:<10} {wave:<8}"
            )

        lines.append("-" * 60)
        lines.append(f"Total: {len(results)} stocks")

        return "\n".join(lines)
