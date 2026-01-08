"""
SAPTA Data Labeling for ML Training.

Labels historical data based on whether price achieved
target gain within target days.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from pulse.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class LabeledSample:
    """A single labeled sample for training."""
    ticker: str
    date: date
    features: dict[str, float]
    label: int  # 1 = hit target, 0 = did not
    forward_return: float  # Actual return within target days
    max_return: float  # Maximum return within target days
    days_to_target: int | None  # Days to hit target (if hit)


class SaptaLabeler:
    """
    Label historical SAPTA signals for ML training.
    
    A positive label (1) means the stock achieved target_gain_pct
    within target_days trading days from the signal date.
    """

    def __init__(
        self,
        target_gain_pct: float = 10.0,
        target_days: int = 20,
    ):
        """
        Initialize labeler.
        
        Args:
            target_gain_pct: Target gain percentage (default: 10%)
            target_days: Trading days to achieve target (default: 20)
        """
        self.target_gain_pct = target_gain_pct
        self.target_days = target_days

    def label_price_series(
        self,
        df: pd.DataFrame,
        signal_dates: list[date] | None = None,
    ) -> pd.DataFrame:
        """
        Label a price series with forward returns.
        
        Args:
            df: DataFrame with 'close' column and DatetimeIndex
            signal_dates: Optional list of dates to label (if None, labels all)
            
        Returns:
            DataFrame with additional columns:
            - forward_return: Return over target_days
            - max_forward_return: Max return within target_days
            - hit_target: 1 if max_forward_return >= target_gain_pct
            - days_to_target: Days to first hit target (or NaN)
        """
        if df.empty or 'close' not in df.columns:
            return df

        df = df.copy()
        closes = df['close'].values
        n = len(closes)

        # Calculate forward returns
        forward_returns = np.zeros(n)
        max_forward_returns = np.zeros(n)
        days_to_target = np.full(n, np.nan)
        hit_target = np.zeros(n, dtype=int)

        target_ratio = 1.0 + (self.target_gain_pct / 100.0)

        for i in range(n):
            entry_price = closes[i]
            end_idx = min(i + self.target_days, n - 1)

            if i >= n - 1:
                continue

            # Get forward window
            window = closes[i + 1:end_idx + 1]

            if len(window) == 0:
                continue

            # Calculate returns
            exit_price = closes[end_idx] if end_idx < n else closes[-1]
            forward_returns[i] = (exit_price - entry_price) / entry_price * 100

            # Max return in window
            max_price = np.max(window) if len(window) > 0 else entry_price
            max_forward_returns[i] = (max_price - entry_price) / entry_price * 100

            # Check if hit target
            if max_forward_returns[i] >= self.target_gain_pct:
                hit_target[i] = 1

                # Find first day that hit target
                for j, price in enumerate(window):
                    if price >= entry_price * target_ratio:
                        days_to_target[i] = j + 1
                        break

        df['forward_return'] = forward_returns
        df['max_forward_return'] = max_forward_returns
        df['hit_target'] = hit_target
        df['days_to_target'] = days_to_target

        return df

    def label_samples(
        self,
        features_by_date: dict[date, dict[str, float]],
        price_df: pd.DataFrame,
        ticker: str,
    ) -> list[LabeledSample]:
        """
        Create labeled samples from features and prices.
        
        Args:
            features_by_date: Dict mapping date to feature dict
            price_df: DataFrame with close prices
            ticker: Stock ticker
            
        Returns:
            List of LabeledSample objects
        """
        # First label the price series
        labeled_df = self.label_price_series(price_df)

        samples = []

        for signal_date, features in features_by_date.items():
            # Find this date in the DataFrame
            try:
                if isinstance(signal_date, str):
                    signal_date = pd.to_datetime(signal_date).date()

                # Find closest date in index
                idx = labeled_df.index.get_indexer([pd.Timestamp(signal_date)], method='nearest')[0]

                if idx < 0 or idx >= len(labeled_df):
                    continue

                row = labeled_df.iloc[idx]

                sample = LabeledSample(
                    ticker=ticker,
                    date=signal_date,
                    features=features,
                    label=int(row.get('hit_target', 0)),
                    forward_return=float(row.get('forward_return', 0)),
                    max_return=float(row.get('max_forward_return', 0)),
                    days_to_target=int(row['days_to_target']) if pd.notna(row.get('days_to_target')) else None,
                )
                samples.append(sample)

            except Exception as e:
                log.debug(f"Could not label {ticker} on {signal_date}: {e}")
                continue

        return samples

    def calculate_statistics(
        self,
        samples: list[LabeledSample],
    ) -> dict[str, Any]:
        """
        Calculate statistics from labeled samples.
        
        Args:
            samples: List of labeled samples
            
        Returns:
            Dictionary with statistics
        """
        if not samples:
            return {}

        labels = [s.label for s in samples]
        returns = [s.forward_return for s in samples]
        max_returns = [s.max_return for s in samples]

        positive_samples = [s for s in samples if s.label == 1]
        days_to_target = [s.days_to_target for s in positive_samples if s.days_to_target is not None]

        return {
            "total_samples": len(samples),
            "positive_samples": sum(labels),
            "negative_samples": len(labels) - sum(labels),
            "hit_rate": sum(labels) / len(labels) * 100,
            "avg_forward_return": np.mean(returns),
            "avg_max_return": np.mean(max_returns),
            "avg_days_to_target": np.mean(days_to_target) if days_to_target else None,
            "median_days_to_target": np.median(days_to_target) if days_to_target else None,
        }
