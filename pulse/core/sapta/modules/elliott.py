"""
Elliott Wave Module (Advanced).

Detects Elliott Wave patterns and current wave position.
Best entries are at end of Wave 2 or Wave 4 corrections.

Uses:
- Fibonacci retracement levels
- Wave structure validation
- ABC corrective pattern detection
"""

from typing import Any

import pandas as pd

from pulse.core.sapta.models import ModuleScore, WavePhase
from pulse.core.sapta.modules.base import BaseModule


class ElliottModule(BaseModule):
    """
    Advanced Elliott Wave analysis.

    Key rules:
    1. Wave 2 never retraces more than 100% of Wave 1
    2. Wave 3 is never the shortest
    3. Wave 4 doesn't overlap Wave 1 territory
    4. Alternation: If Wave 2 is sharp, Wave 4 is flat

    Best entry: End of Wave 2 (38-61% retracement) or Wave 4

    Max Score: 20
    """

    name = "elliott"
    max_score = 20.0

    # Fibonacci levels
    FIB_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0]

    def analyze(
        self,
        df: pd.DataFrame,
        lookback: int = 60,
        swing_lookback: int = 5,
    ) -> ModuleScore:
        """
        Analyze Elliott Wave context.

        Args:
            df: OHLCV DataFrame
            lookback: Number of candles for wave analysis
            swing_lookback: Bars for swing point detection
        """
        if len(df) < lookback:
            return self._create_score(0, False, "Insufficient data", [])

        score = 0.0
        signals = []
        features = {}
        wave_phase = WavePhase.UNKNOWN

        recent = df.tail(lookback)

        # Find swing points
        swings = self._find_swing_points(recent, swing_lookback)
        features["swing_count"] = len(swings)

        if len(swings) < 3:
            return self._create_score(0, False, "Not enough swing points", [], features)

        # === Calculate retracement from last major move ===
        # Find the last significant high and low
        swing_high = recent["high"].max()
        swing_low = recent["low"].min()
        current_price = recent["close"].iloc[-1]

        # Determine if we're in an uptrend or downtrend context
        high_idx = recent["high"].idxmax()
        low_idx = recent["low"].idxmin()

        wave_range = swing_high - swing_low

        if wave_range > 0:
            if high_idx > low_idx:
                # Uptrend: low came first, then high
                # We might be in Wave 2 or 4 (retracing from high)
                retrace_from_high = (swing_high - current_price) / wave_range
                features["retracement"] = float(retrace_from_high)
                features["trend_context"] = "uptrend"

                # Check Fibonacci retracement levels
                fib_score, fib_signal, phase = self._score_retracement(
                    retrace_from_high, "correction_down"
                )
                score += fib_score
                if fib_signal:
                    signals.append(fib_signal)
                wave_phase = phase

            else:
                # Downtrend: high came first, then low
                # We might be in corrective bounce
                retrace_from_low = (current_price - swing_low) / wave_range
                features["retracement"] = float(retrace_from_low)
                features["trend_context"] = "downtrend"

                fib_score, fib_signal, phase = self._score_retracement(
                    retrace_from_low, "correction_up"
                )
                score += fib_score
                if fib_signal:
                    signals.append(fib_signal)
                wave_phase = phase

        # === Check for ABC pattern ===
        abc_detected, abc_details = self._detect_abc_pattern(swings)
        features["abc_pattern"] = float(abc_detected)

        if abc_detected:
            score += 6
            signals.append(f"ABC corrective pattern: {abc_details}")
            if wave_phase == WavePhase.UNKNOWN:
                wave_phase = WavePhase.WAVE_C

        # === Validate Elliott rules ===
        violations = self._check_elliott_rules(swings)
        features["rule_violations"] = len(violations)

        if violations:
            score -= len(violations) * 2
            for v in violations:
                signals.append(f"Warning: {v}")

        # === Check momentum confirmation ===
        # RSI divergence at potential wave end
        if len(recent) >= 14:
            rsi_div = self._check_rsi_divergence(recent)
            features["rsi_divergence"] = float(rsi_div)

            if rsi_div:
                score += 4
                signals.append("RSI divergence confirms wave end")

        # Set wave phase in features
        features["wave_phase"] = wave_phase.value
        features["fib_retracement"] = features.get("retracement", 0)

        # Determine status
        status = score >= 12
        details = f"Elliott: {wave_phase.value}" if status else "No clear Elliott pattern"

        return self._create_score(score, status, details, signals, features)

    def _score_retracement(
        self,
        retrace: float,
        direction: str,
    ) -> tuple[float, str | None, WavePhase]:
        """Score based on Fibonacci retracement level."""

        # Golden zone: 38.2% - 61.8% (best for Wave 2)
        if 0.382 <= retrace <= 0.618:
            if 0.5 <= retrace <= 0.618:
                return 10, f"Golden zone retracement ({retrace:.1%})", WavePhase.WAVE_2
            else:
                return 8, f"Fibonacci retracement ({retrace:.1%})", WavePhase.WAVE_2

        # Shallow retracement: 23.6% - 38.2% (typical Wave 4)
        elif 0.236 <= retrace < 0.382:
            return 6, f"Shallow retracement ({retrace:.1%})", WavePhase.WAVE_4

        # Deep retracement: 61.8% - 78.6% (still valid but risky)
        elif 0.618 < retrace <= 0.786:
            return 4, f"Deep retracement ({retrace:.1%})", WavePhase.WAVE_2

        # Too deep (>78.6%) - likely invalidates wave count
        elif retrace > 0.786:
            return 0, f"Over-retracement ({retrace:.1%})", WavePhase.UNKNOWN

        # Too shallow (<23.6%) - correction may not be complete
        else:
            return 2, f"Minimal retracement ({retrace:.1%})", WavePhase.UNKNOWN

    def _detect_abc_pattern(
        self,
        swings: list[dict[str, Any]],
    ) -> tuple[bool, str]:
        """
        Detect ABC corrective pattern.

        ABC pattern:
        - A: Initial move against trend
        - B: Partial retracement of A
        - C: Final move, often equals A in length
        """
        if len(swings) < 4:
            return False, ""

        # Get last 4 swing points
        last_swings = swings[-4:]

        # Check for zigzag pattern
        types = [s["type"] for s in last_swings]
        prices = [s["price"] for s in last_swings]

        # Pattern: high-low-high-low or low-high-low-high
        if types == ["high", "low", "high", "low"]:
            # Potential ABC down
            a_move = prices[0] - prices[1]  # A down
            b_move = prices[2] - prices[1]  # B up (retracement)
            c_move = prices[2] - prices[3]  # C down

            if a_move > 0 and b_move > 0 and c_move > 0:
                # B should retrace 38-78% of A
                b_retrace = b_move / a_move if a_move > 0 else 0
                if 0.38 <= b_retrace <= 0.78:
                    # C often equals A or 1.618*A
                    c_ratio = c_move / a_move if a_move > 0 else 0
                    if 0.8 <= c_ratio <= 1.8:
                        return True, f"ABC down (B retrace: {b_retrace:.0%}, C/A: {c_ratio:.1f})"

        elif types == ["low", "high", "low", "high"]:
            # Potential ABC up
            a_move = prices[1] - prices[0]  # A up
            b_move = prices[1] - prices[2]  # B down (retracement)
            c_move = prices[3] - prices[2]  # C up

            if a_move > 0 and b_move > 0 and c_move > 0:
                b_retrace = b_move / a_move if a_move > 0 else 0
                if 0.38 <= b_retrace <= 0.78:
                    c_ratio = c_move / a_move if a_move > 0 else 0
                    if 0.8 <= c_ratio <= 1.8:
                        return True, f"ABC up (B retrace: {b_retrace:.0%}, C/A: {c_ratio:.1f})"

        return False, ""

    def _check_elliott_rules(
        self,
        swings: list[dict[str, Any]],
    ) -> list[str]:
        """Check for Elliott Wave rule violations."""
        violations = []

        if len(swings) < 5:
            return violations

        # This is a simplified check
        # Full implementation would require proper wave labeling

        # Get prices
        prices = [s["price"] for s in swings[-5:]]
        types = [s["type"] for s in swings[-5:]]

        # Check for potential Wave 4 overlapping Wave 1
        # (simplified: check if any low goes below first swing)
        if types[0] == "low":
            wave1_territory = prices[0]
            for i, (t, p) in enumerate(zip(types[1:], prices[1:]), 1):
                if t == "low" and i >= 3 and p < wave1_territory:
                    violations.append("Wave 4 overlaps Wave 1 territory")
                    break

        return violations

    def _check_rsi_divergence(self, df: pd.DataFrame) -> bool:
        """Check for RSI divergence (bullish or bearish)."""
        try:
            from ta.momentum import RSIIndicator

            rsi = RSIIndicator(df["close"], window=14).rsi()

            # Check last 10 bars for divergence
            recent_price = df["close"].tail(10)
            recent_rsi = rsi.tail(10)

            # Bullish divergence: price lower low, RSI higher low

            # Find previous low
            first_half = recent_price.iloc[:5]
            second_half = recent_price.iloc[5:]

            if len(first_half) > 0 and len(second_half) > 0:
                if (
                    second_half.min() < first_half.min()
                    and recent_rsi.loc[second_half.idxmin()] > recent_rsi.loc[first_half.idxmin()]
                ):
                    return True  # Bullish divergence

                if (
                    second_half.max() > first_half.max()
                    and recent_rsi.loc[second_half.idxmax()] < recent_rsi.loc[first_half.idxmax()]
                ):
                    return True  # Bearish divergence

            return False

        except Exception:
            return False
