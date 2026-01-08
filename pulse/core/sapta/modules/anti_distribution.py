"""
Anti-Distribution Module.

Filters out stocks showing distribution patterns (smart money selling).
Penalizes stocks with signs of distribution.

Signals to avoid:
- Volume spike with weak close
- Fake breakouts
- Negative OBV divergence
"""

import pandas as pd

from pulse.core.sapta.models import ModuleScore
from pulse.core.sapta.modules.base import BaseModule


class AntiDistributionModule(BaseModule):
    """
    Filter out distribution patterns.
    
    Distribution signs (negative):
    1. High volume + weak close (smart money selling)
    2. Fake breakouts that fail quickly
    3. Negative OBV divergence (price up, OBV down)
    
    Starts with max score, deducts for distribution signs.
    
    Max Score: 15
    """

    name = "anti_distribution"
    max_score = 15.0

    def analyze(
        self,
        df: pd.DataFrame,
        lookback: int = 20,
        false_break_candles: int = 3,
    ) -> ModuleScore:
        """
        Analyze for distribution patterns.
        
        Args:
            df: OHLCV DataFrame
            lookback: Number of candles to analyze
            false_break_candles: Min candles to confirm false breakout
        """
        if len(df) < lookback + 50:
            return self._create_score(0, False, "Insufficient data", [])

        # Start with full score - deduct for distribution signs
        score = self.max_score
        signals = []
        features = {}

        recent = df.tail(lookback)
        avg_volume = df['volume'].rolling(50).mean()

        # === Check 1: Distribution candles ===
        # High volume + weak close = distribution
        dist_candles = 0

        for i in range(-lookback, 0):
            vol = df['volume'].iloc[i]
            avg_vol = avg_volume.iloc[i]

            if pd.isna(avg_vol) or avg_vol == 0:
                continue

            if vol > avg_vol * 1.8:  # Volume spike
                candle = df.iloc[i]
                candle_range = candle['high'] - candle['low']

                if candle_range > 0:
                    close_position = (candle['close'] - candle['low']) / candle_range

                    if close_position < 0.3:  # Weak close
                        dist_candles += 1

        features['distribution_candles'] = int(dist_candles)

        if dist_candles >= 3:
            score -= 6
            signals.append(f"Multiple distribution candles ({dist_candles})")
        elif dist_candles >= 2:
            score -= 4
            signals.append(f"Distribution candles detected ({dist_candles})")
        elif dist_candles == 1:
            score -= 2
            signals.append("Minor distribution signal")

        # === Check 2: False breakout ===
        # Price breaks resistance but fails to hold
        resistance = recent.iloc[:-false_break_candles]['high'].max()

        false_breakout = False
        for i in range(-false_break_candles - 5, -false_break_candles):
            if i >= -len(df):
                if df['high'].iloc[i] > resistance:
                    # Breakout occurred - check if it held
                    post_break = df.iloc[i:]
                    if post_break['close'].iloc[-1] < resistance:
                        false_breakout = True
                        break

        features['false_breakout'] = float(false_breakout)

        if false_breakout:
            score -= 5
            signals.append("Recent false breakout detected")

        # === Check 3: OBV divergence ===
        # Price making higher highs but OBV making lower highs = bearish
        obv = self._calculate_obv(df)

        price_trend = df['close'].iloc[-1] > df['close'].iloc[-20]
        obv_trend = obv.iloc[-1] > obv.iloc[-20]

        features['price_trend_up'] = float(price_trend)
        features['obv_trend_up'] = float(obv_trend)

        if price_trend and not obv_trend:
            score -= 4
            signals.append("Negative OBV divergence (bearish)")
            features['obv_divergence'] = 'bearish'
        elif not price_trend and obv_trend:
            # This is actually bullish - accumulation
            score += 2  # Bonus for hidden accumulation
            signals.append("Positive OBV divergence (hidden accumulation)")
            features['obv_divergence'] = 'bullish'
        else:
            features['obv_divergence'] = 'none'

        # === Check 4: Selling climax pattern ===
        # Very high volume with large down bar - could be capitulation (positive)
        last_5 = df.tail(5)
        for i in range(len(last_5)):
            candle = last_5.iloc[i]
            vol = candle['volume']
            avg_vol = avg_volume.iloc[-(5-i)]

            if pd.notna(avg_vol) and vol > avg_vol * 3:
                # Huge volume spike
                if candle['close'] < candle['open']:
                    # Down bar
                    body_size = abs(candle['close'] - candle['open'])
                    rng = candle['high'] - candle['low']

                    if rng > 0 and body_size / rng > 0.7:
                        # Large down body with huge volume = capitulation
                        signals.append("Potential capitulation (selling climax)")
                        features['capitulation'] = True
                        # This is actually good for reversal
                        score += 2
                        break

        if not signals:
            signals.append("No distribution signs detected")

        # Determine status
        status = score >= 10
        details = "Clean (no distribution)" if status else "Distribution warning"

        return self._create_score(max(0, score), status, details, signals, features)

    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume."""
        obv = [0]

        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])

        return pd.Series(obv, index=df.index)
