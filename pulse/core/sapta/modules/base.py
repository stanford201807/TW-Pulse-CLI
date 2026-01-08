"""
Base Module for SAPTA Analysis.

All SAPTA modules inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd

from pulse.core.sapta.models import ModuleScore


class BaseModule(ABC):
    """
    Base class for all SAPTA analysis modules.
    
    Each module:
    1. Analyzes specific aspect of price/volume data
    2. Returns a score (0 to max_score)
    3. Returns raw features for ML training
    4. Provides explainability (signals list)
    """

    name: str = "base"
    max_score: float = 20.0

    @abstractmethod
    def analyze(self, df: pd.DataFrame, **kwargs) -> ModuleScore:
        """
        Analyze data and return score.
        
        Args:
            df: OHLCV DataFrame with columns: open, high, low, close, volume
                Index should be DatetimeIndex
            **kwargs: Additional parameters
            
        Returns:
            ModuleScore with score, status, details, and raw features
        """
        pass

    def _create_score(
        self,
        score: float,
        status: bool,
        details: str,
        signals: list[str] = None,
        raw_features: dict[str, Any] = None,
    ) -> ModuleScore:
        """Helper to create ModuleScore."""
        return ModuleScore(
            module_name=self.name,
            score=min(max(0, score), self.max_score),
            max_score=self.max_score,
            status=status,
            details=details,
            signals=signals or [],
            raw_features=raw_features or {},
        )

    def _calculate_atr(
        self,
        df: pd.DataFrame,
        period: int = 14,
    ) -> pd.Series:
        """Calculate Average True Range."""
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def _has_higher_lows(
        self,
        values: np.ndarray,
        min_count: int = 3,
    ) -> bool:
        """Check if there are consecutive higher lows."""
        if len(values) < min_count + 1:
            return False

        higher_low_count = 0
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                higher_low_count += 1
            else:
                higher_low_count = 0
            if higher_low_count >= min_count:
                return True
        return False

    def _has_lower_highs(
        self,
        values: np.ndarray,
        min_count: int = 3,
    ) -> bool:
        """Check if there are consecutive lower highs."""
        if len(values) < min_count + 1:
            return False

        lower_high_count = 0
        for i in range(1, len(values)):
            if values[i] < values[i-1]:
                lower_high_count += 1
            else:
                lower_high_count = 0
            if lower_high_count >= min_count:
                return True
        return False

    def _calculate_slope(
        self,
        series: pd.Series,
        window: int = 20,
    ) -> float:
        """Calculate linear regression slope of series."""
        if len(series) < window:
            return 0.0

        recent = series.tail(window).values
        x = np.arange(len(recent))

        # Simple linear regression slope
        if np.std(recent) == 0:
            return 0.0

        slope = np.polyfit(x, recent, 1)[0]
        # Normalize by mean
        mean_val = np.mean(recent)
        if mean_val != 0:
            slope = slope / mean_val

        return float(slope)

    def _find_swing_points(
        self,
        df: pd.DataFrame,
        lookback: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find swing highs and lows.
        
        A swing high is a high that is higher than 'lookback' bars before and after.
        A swing low is a low that is lower than 'lookback' bars before and after.
        """
        swings = []
        highs = df['high'].values
        lows = df['low'].values
        dates = df.index

        for i in range(lookback, len(df) - lookback):
            # Check swing high
            is_swing_high = all(
                highs[i] > highs[i-j] and highs[i] > highs[i+j]
                for j in range(1, lookback + 1)
            )

            # Check swing low
            is_swing_low = all(
                lows[i] < lows[i-j] and lows[i] < lows[i+j]
                for j in range(1, lookback + 1)
            )

            if is_swing_high:
                swings.append({
                    'type': 'high',
                    'date': dates[i],
                    'price': highs[i],
                    'index': i,
                })

            if is_swing_low:
                swings.append({
                    'type': 'low',
                    'date': dates[i],
                    'price': lows[i],
                    'index': i,
                })

        return sorted(swings, key=lambda x: x['index'])
