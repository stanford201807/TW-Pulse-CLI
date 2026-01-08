"""
SAPTA Data Loader.

Ticker list from data/tickers.json.
Historical data from yfinance (live).
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from pulse.utils.logger import get_logger

log = get_logger(__name__)


class SaptaDataLoader:
    """
    Load data for SAPTA analysis.
    
    Data sources:
    - Ticker list: data/tickers.json (955 IDX stocks)
    - Historical OHLCV: yfinance (live data)
    """

    def __init__(self, tickers_path: str | None = None):
        """
        Initialize data loader.
        
        Args:
            tickers_path: Path to tickers.json (auto-detect if None)
        """
        # Find tickers.json
        if tickers_path is None:
            candidates = [
                Path(__file__).parent.parent.parent.parent / "data" / "tickers.json",
                Path(__file__).parent.parent.parent.parent.parent / "data" / "tickers.json",
                Path.cwd() / "data" / "tickers.json",
            ]
            for p in candidates:
                if p.exists():
                    tickers_path = str(p)
                    break

        self.tickers_path = tickers_path
        self._tickers_cache: list[str] | None = None
        self._yf_fetcher = None

    def _get_fetcher(self):
        """Get yfinance fetcher lazily."""
        if self._yf_fetcher is None:
            from pulse.core.data.yfinance import YFinanceFetcher
            self._yf_fetcher = YFinanceFetcher()
        return self._yf_fetcher

    def get_all_tickers(self) -> list[str]:
        """
        Get all available stock tickers from tickers.json.
        """
        # Return cached if available
        if self._tickers_cache is not None:
            return self._tickers_cache

        # Load from tickers.json
        if self.tickers_path and Path(self.tickers_path).exists():
            try:
                with open(self.tickers_path) as f:
                    self._tickers_cache = json.load(f)
                log.info(f"Loaded {len(self._tickers_cache)} tickers from tickers.json")
                return self._tickers_cache
            except Exception as e:
                log.warning(f"Could not load tickers.json: {e}")

        # Fallback to common tickers
        log.warning("tickers.json not found, using LQ45 fallback")
        from pulse.utils.constants import LQ45_TICKERS
        return LQ45_TICKERS

    def get_historical_df(
        self,
        ticker: str,
        period: str = "1y",
    ) -> pd.DataFrame | None:
        """
        Get historical OHLCV data from yfinance.
        
        Args:
            ticker: Stock ticker (e.g., "BBCA")
            period: Period string (1mo, 3mo, 6mo, 1y, 2y)
            
        Returns:
            DataFrame with columns: open, high, low, close, volume
            Index: DatetimeIndex
        """
        fetcher = self._get_fetcher()
        return fetcher.get_history_df(ticker, period=period)

    def get_multiple_stocks(
        self,
        tickers: list[str],
        period: str = "1y",
        min_rows: int = 120,
    ) -> dict[str, pd.DataFrame]:
        """
        Load historical data for multiple stocks from yfinance.
        
        Args:
            tickers: List of stock tickers
            period: Period string
            min_rows: Minimum rows required
            
        Returns:
            Dict of ticker -> DataFrame
        """
        result = {}
        fetcher = self._get_fetcher()

        for ticker in tickers:
            try:
                df = fetcher.get_history_df(ticker, period=period)
                if df is not None and len(df) >= min_rows:
                    result[ticker] = df
            except Exception as e:
                log.debug(f"Could not fetch {ticker}: {e}")
                continue

        log.info(f"Loaded {len(result)}/{len(tickers)} stocks with >= {min_rows} rows")
        return result

    def get_statistics(self) -> dict[str, Any]:
        """Get basic statistics."""
        return {
            "total_stocks": len(self.get_all_tickers()),
            "data_source": "yfinance (live)",
        }


def load_training_data(
    tickers: list[str] | None = None,
    period: str = "2y",
    min_rows: int = 120,
) -> dict[str, pd.DataFrame]:
    """
    Convenience function to load training data from yfinance.
    
    Args:
        tickers: List of tickers (None = all from tickers.json)
        period: Period string for yfinance
        min_rows: Minimum rows required
        
    Returns:
        Dict of ticker -> DataFrame
    """
    loader = SaptaDataLoader()

    if tickers is None:
        tickers = loader.get_all_tickers()

    return loader.get_multiple_stocks(
        tickers=tickers,
        period=period,
        min_rows=min_rows,
    )
