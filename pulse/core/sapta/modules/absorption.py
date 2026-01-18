"""
Supply Absorption Module.

Detects when supply (selling pressure) is being absorbed by demand,
indicating accumulation phase before markup.

Signals:
- High volume without price breakdown
- Failed lower lows
- Strong closes after volume spikes
"""

import numpy as np
import pandas as pd

from pulse.core.sapta.models import ModuleScore
from pulse.core.sapta.modules.base import BaseModule


class SupplyAbsorptionModule(BaseModule):
    """
    Detect supply absorption pattern.

    Key signals:
    1. Volume spike without price breakdown
    2. Higher lows forming (demand absorbing supply)
    3. Close in upper half of candle range

    Max Score: 20
    """

    name = "absorption"
    max_score = 20.0

    def analyze(
        self,
        df: pd.DataFrame,
        lookback: int = 20,
        volume_spike_threshold: float = 1.5,
    ) -> ModuleScore:
        """
        Analyze supply absorption.

        Args:
            df: OHLCV DataFrame
            lookback: Number of recent candles to analyze
            volume_spike_threshold: Volume must be X times average
        """
        if len(df) < lookback + 50:
            return self._create_score(0, False, "Insufficient data", [])

        score = 0.0
        signals = []
        features = {}

        recent = df.tail(lookback)

        # Calculate average volume (50-day)
        avg_volume = df["volume"].rolling(50).mean()

        # === Check 1: Volume spike absorbed ===
        # Find if there was a volume spike and price held
        recent_max_vol_idx = recent["volume"].idxmax()
        spike_volume = recent.loc[recent_max_vol_idx, "volume"]
        avg_vol_at_spike = avg_volume.loc[recent_max_vol_idx]

        volume_ratio = spike_volume / avg_vol_at_spike if avg_vol_at_spike > 0 else 0
        features["volume_spike_ratio"] = float(volume_ratio)

        if volume_ratio >= volume_spike_threshold:
            # Check if price held after spike (no new low)
            spike_pos = df.index.get_loc(recent_max_vol_idx)
            after_spike = df.iloc[spike_pos:]

            spike_low = df.loc[recent_max_vol_idx, "low"]
            subsequent_low = after_spike["low"].min()

            price_held = subsequent_low >= spike_low * 0.99  # Allow 1% tolerance
            features["price_held_after_spike"] = float(price_held)

            if price_held:
                score += 8
                signals.append(f"Volume spike {volume_ratio:.1f}x absorbed, price held")
            else:
                score += 3
                signals.append(f"Volume spike {volume_ratio:.1f}x but price broke down")

        # === Check 2: Higher lows forming ===
        lows = recent["low"].values
        higher_lows = self._count_higher_lows(lows)
        features["higher_lows_count"] = int(higher_lows)

        if higher_lows >= 3:
            score += 6
            signals.append(f"Higher lows forming ({higher_lows} consecutive)")
        elif higher_lows >= 2:
            score += 3
            signals.append(f"Higher lows emerging ({higher_lows})")

        # === Check 3: Close strength ===
        # Average close position in last N candles
        close_strengths = []
        for i in range(-min(5, len(recent)), 0):
            candle = df.iloc[i]
            candle_range = candle["high"] - candle["low"]
            if candle_range > 0:
                close_pos = (candle["close"] - candle["low"]) / candle_range
                close_strengths.append(close_pos)

        avg_close_strength = np.mean(close_strengths) if close_strengths else 0.5
        features["avg_close_strength"] = float(avg_close_strength)

        if avg_close_strength >= 0.6:
            score += 6
            signals.append(f"Strong closes ({avg_close_strength:.0%} avg)")
        elif avg_close_strength >= 0.5:
            score += 3
            signals.append(f"Moderate close strength ({avg_close_strength:.0%})")

        # === Check 4: No distribution candles ===
        # Distribution = high volume + weak close
        dist_candles = 0
        for i in range(-lookback, 0):
            vol = df["volume"].iloc[i]
            avg_vol = avg_volume.iloc[i]
            if vol > avg_vol * 1.5:
                candle = df.iloc[i]
                rng = candle["high"] - candle["low"]
                if rng > 0:
                    close_pos = (candle["close"] - candle["low"]) / rng
                    if close_pos < 0.3:  # Weak close
                        dist_candles += 1

        features["distribution_candles"] = int(dist_candles)

        if dist_candles == 0:
            # No distribution detected - bonus
            pass  # Already counted in other checks
        elif dist_candles >= 2:
            score -= 4
            signals.append(f"Warning: {dist_candles} distribution candles detected")

        # Determine status
        status = score >= 10
        details = "Supply being absorbed" if status else "No clear absorption pattern"

        return self._create_score(score, status, details, signals, features)

    def _count_higher_lows(self, lows: np.ndarray) -> int:
        """Count maximum consecutive higher lows."""
        max_count = 0
        current_count = 0

        for i in range(1, len(lows)):
            if lows[i] > lows[i - 1]:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        return max_count
