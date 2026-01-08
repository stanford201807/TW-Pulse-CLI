"""
Bollinger Band Squeeze Module.

Detects when Bollinger Bands are unusually tight, indicating
low volatility that often precedes explosive moves.

Signals:
- BB Width below historical percentile
- Extended squeeze duration
"""

import pandas as pd
from ta.volatility import BollingerBands

from pulse.core.sapta.models import ModuleScore
from pulse.core.sapta.modules.base import BaseModule


class BBSqueezeModule(BaseModule):
    """
    Detect Bollinger Band squeeze.
    
    A squeeze occurs when BB Width is at historical lows,
    indicating compressed volatility ready to expand.
    
    Max Score: 15
    """

    name = "bb_squeeze"
    max_score = 15.0

    def analyze(
        self,
        df: pd.DataFrame,
        bb_period: int = 20,
        bb_std: int = 2,
        squeeze_percentile: int = 20,
        min_squeeze_duration: int = 8,
    ) -> ModuleScore:
        """
        Analyze Bollinger Band squeeze.
        
        Args:
            df: OHLCV DataFrame
            bb_period: Bollinger Band period
            bb_std: Number of standard deviations
            squeeze_percentile: Width percentile to be considered squeeze
            min_squeeze_duration: Minimum candles in squeeze
        """
        if len(df) < bb_period + 100:
            return self._create_score(0, False, "Insufficient data", [])

        score = 0.0
        signals = []
        features = {}

        close = df['close']

        # Calculate Bollinger Bands
        bb = BollingerBands(close, window=bb_period, window_dev=bb_std)
        bb_width = bb.bollinger_wband()

        # === Check 1: Current width percentile ===
        current_width = bb_width.iloc[-1]

        # Calculate percentile over last 200 days
        lookback_width = bb_width.tail(200)
        width_percentile = (lookback_width < current_width).sum() / len(lookback_width) * 100

        features['bb_width_current'] = float(current_width)
        features['bb_width_percentile'] = float(width_percentile)

        if width_percentile <= 10:
            score += 8
            signals.append(f"BB Width at {width_percentile:.0f}th percentile (extreme squeeze)")
        elif width_percentile <= squeeze_percentile:
            score += 5
            signals.append(f"BB Width at {width_percentile:.0f}th percentile (squeeze)")
        elif width_percentile <= 30:
            score += 2
            signals.append(f"BB Width at {width_percentile:.0f}th percentile (mild compression)")

        # === Check 2: Squeeze duration ===
        # Count consecutive candles in squeeze
        threshold = lookback_width.quantile(squeeze_percentile / 100)

        squeeze_count = 0
        for i in range(-1, -min(50, len(bb_width)), -1):
            if bb_width.iloc[i] <= threshold:
                squeeze_count += 1
            else:
                break

        features['squeeze_duration'] = int(squeeze_count)

        if squeeze_count >= min_squeeze_duration * 2:
            score += 5
            signals.append(f"Extended squeeze: {squeeze_count} candles")
        elif squeeze_count >= min_squeeze_duration:
            score += 3
            signals.append(f"Squeeze duration: {squeeze_count} candles")
        elif squeeze_count >= min_squeeze_duration // 2:
            score += 1
            signals.append(f"Short squeeze: {squeeze_count} candles")

        # === Check 3: Price position in bands ===
        bb_upper = bb.bollinger_hband().iloc[-1]
        bb_lower = bb.bollinger_lband().iloc[-1]
        bb_mid = bb.bollinger_mavg().iloc[-1]
        current_price = close.iloc[-1]

        bb_range = bb_upper - bb_lower
        if bb_range > 0:
            price_position = (current_price - bb_lower) / bb_range
            features['price_position_in_bb'] = float(price_position)

            # Best for breakout: price near middle or upper half
            if 0.4 <= price_position <= 0.6:
                score += 2
                signals.append("Price at BB middle (balanced)")
            elif price_position > 0.6:
                score += 1
                signals.append("Price in upper BB zone")

        # Determine status
        status = score >= 8
        details = f"BB Squeeze active ({squeeze_count} candles)" if status else "No squeeze"

        return self._create_score(score, status, details, signals, features)
