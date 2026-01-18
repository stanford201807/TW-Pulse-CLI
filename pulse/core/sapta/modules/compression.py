"""
Compression Module.

Detects price compression (volatility contraction) which often
precedes explosive moves.

Signals:
- ATR decreasing
- Range narrowing
- Higher lows + lower highs (triangle pattern)
"""

import numpy as np
import pandas as pd

from pulse.core.sapta.models import ModuleScore
from pulse.core.sapta.modules.base import BaseModule


class CompressionModule(BaseModule):
    """
    Detect price compression (volatility contraction).

    Key signals:
    1. ATR decreasing over time
    2. Range narrowing (recent range < past range)
    3. Converging highs and lows (triangle formation)

    Max Score: 15
    """

    name = "compression"
    max_score = 15.0

    def analyze(
        self,
        df: pd.DataFrame,
        lookback: int = 20,
        atr_period: int = 14,
    ) -> ModuleScore:
        """
        Analyze price compression.

        Args:
            df: OHLCV DataFrame
            lookback: Number of candles for analysis
            atr_period: ATR calculation period
        """
        if len(df) < lookback + atr_period:
            return self._create_score(0, False, "Insufficient data", [])

        score = 0.0
        signals = []
        features = {}

        recent = df.tail(lookback)

        # === Calculate ATR ===
        atr = self._calculate_atr(df, atr_period)

        # === Check 1: ATR slope (decreasing = compression) ===
        atr_slope = self._calculate_slope(atr, lookback)
        features["atr_slope"] = float(atr_slope)

        if atr_slope < -0.15:  # ATR decreased by 15%+
            score += 6
            signals.append(f"ATR strongly contracting ({atr_slope:.1%})")
        elif atr_slope < -0.08:
            score += 4
            signals.append(f"ATR contracting ({atr_slope:.1%})")
        elif atr_slope < 0:
            score += 2
            signals.append(f"ATR slightly decreasing ({atr_slope:.1%})")

        # === Check 2: Range narrowing ===
        # Compare first half range vs second half
        first_half = recent.iloc[: lookback // 2]
        second_half = recent.iloc[lookback // 2 :]

        range_first = first_half["high"].max() - first_half["low"].min()
        range_second = second_half["high"].max() - second_half["low"].min()

        range_ratio = range_second / range_first if range_first > 0 else 1.0
        features["range_contraction"] = float(range_ratio)

        if range_ratio < 0.5:
            score += 5
            signals.append(f"Range contracted to {range_ratio:.0%}")
        elif range_ratio < 0.7:
            score += 3
            signals.append(f"Range narrowing ({range_ratio:.0%})")

        # === Check 3: Higher lows + Lower highs (triangle) ===
        lows = recent["low"].values
        highs = recent["high"].values

        has_higher_lows = self._has_higher_lows(lows, min_count=2)
        has_lower_highs = self._has_lower_highs(highs, min_count=2)

        features["higher_lows"] = float(has_higher_lows)
        features["lower_highs"] = float(has_lower_highs)

        if has_higher_lows and has_lower_highs:
            score += 4
            signals.append("Triangle pattern (higher lows + lower highs)")
        elif has_higher_lows:
            score += 2
            signals.append("Ascending triangle (higher lows)")
        elif has_lower_highs:
            score += 1
            signals.append("Descending triangle (lower highs)")

        # === Check 4: Candle body shrinking ===
        bodies = []
        for i in range(-lookback, 0):
            candle = df.iloc[i]
            body = abs(candle["close"] - candle["open"])
            rng = candle["high"] - candle["low"]
            if rng > 0:
                bodies.append(body / rng)

        avg_body_ratio = np.mean(bodies[-5:]) if len(bodies) >= 5 else 0.5
        features["avg_body_ratio"] = float(avg_body_ratio)

        if avg_body_ratio < 0.3:
            score += 2
            signals.append(f"Small candle bodies ({avg_body_ratio:.0%})")

        # Determine status
        status = score >= 8
        details = "Price compressing" if status else "No significant compression"

        return self._create_score(score, status, details, signals, features)
