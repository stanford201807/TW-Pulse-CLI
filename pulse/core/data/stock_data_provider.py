"""Centralized data provider to fetch stock data from FinMind (primary), yfinance (fallback), or Fugle (tertiary)."""

import pandas as pd

from pulse.core.data.finmind_data import FinMindFetcher
from pulse.core.data.fugle import FugleFetcher
from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.models import FundamentalData, StockData
from pulse.utils.error_handler import RateLimitError
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class StockDataProvider:
    """
    Provides stock data by attempting to fetch from FinMind first, then yfinance, then Fugle.
    Handles graceful degradation when primary sources are unavailable.
    """

    def __init__(self, finmind_token: str = "", fugle_api_key: str = ""):
        """
        Initialize stock data provider.

        Args:
            finmind_token: FinMind API token (optional, for higher rate limits)
            fugle_api_key: Fugle API key (optional, for real-time data)
        """
        self.finmind_fetcher = FinMindFetcher(token=finmind_token)
        self.yfinance_fetcher = YFinanceFetcher()
        self.fugle_fetcher = FugleFetcher(api_key=fugle_api_key)
        self._quota_warning_shown: bool = False
        self._fugle_warning_shown: bool = False

    async def fetch_stock(
        self,
        ticker: str,
        period: str = "3mo",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> StockData | None:
        """
        Fetches stock data for a ticker.

        Attempts FinMind first, then yfinance, then Fugle.
        FinMind uses start_date/end_date, yfinance uses period.
        """
        # Check if FinMind quota was exceeded
        if FinMindFetcher.is_quota_exceeded():
            if not self._quota_warning_shown:
                log.warning("FinMind quota exceeded, using yfinance for all requests")
                self._quota_warning_shown = True
            # Skip FinMind, use yfinance directly
            data = await self.yfinance_fetcher.fetch_stock(ticker, period)
            if data:
                log.debug(f"Fetched {ticker} from yfinance (FinMind quota exceeded)")
                return data
            else:
                log.debug(f"yfinance failed for {ticker}, trying Fugle...")
                # Try Fugle as tertiary fallback
                if start_date and end_date:
                    data = await self.fugle_fetcher.fetch_stock(ticker, start_date, end_date)
                    if data:
                        log.debug(f"Fetched {ticker} from Fugle (tertiary fallback)")
                        return data
                else:
                    # Calculate date range for Fugle
                    from datetime import datetime, timedelta

                    if not end_date:
                        end_date = datetime.now().strftime("%Y-%m-%d")
                    if not start_date:
                        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
                    data = await self.fugle_fetcher.fetch_stock(ticker, start_date, end_date)
                    if data:
                        log.debug(f"Fetched {ticker} from Fugle (tertiary fallback)")
                        return data
                log.error(f"Failed to fetch {ticker} from both yfinance and Fugle.")
            return None

        # Try FinMind first
        if start_date and end_date:
            try:
                data = await self.finmind_fetcher.fetch_stock(ticker, start_date, end_date)
                if data:
                    log.debug(f"Fetched {ticker} from FinMind.")
                    return data
                else:
                    log.warning(f"FinMind failed for {ticker}, trying yfinance...")
            except RateLimitError:
                # Already handled by FinMindFetcher, will fallback to yfinance
                pass

        # Try yfinance as secondary fallback
        data = await self.yfinance_fetcher.fetch_stock(ticker, period)
        if data:
            log.debug(f"Fetched {ticker} from yfinance (fallback).")
            return data

        # Try Fugle as tertiary fallback
        log.debug(f"yfinance failed for {ticker}, trying Fugle...")
        if start_date and end_date:
            data = await self.fugle_fetcher.fetch_stock(ticker, start_date, end_date)
            if data:
                log.debug(f"Fetched {ticker} from Fugle (tertiary fallback).")
                return data
        else:
            # Calculate date range for Fugle
            from datetime import datetime, timedelta

            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            data = await self.fugle_fetcher.fetch_stock(ticker, start_date, end_date)
            if data:
                log.debug(f"Fetched {ticker} from Fugle (tertiary fallback).")
                return data

        log.error(f"Failed to fetch {ticker} from FinMind, yfinance, and Fugle.")
        return None

    async def fetch_fundamentals(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FundamentalData | None:
        """
        Fetches fundamental data for a ticker.

        Attempts FinMind first, then yfinance.
        """
        # Try FinMind first
        if start_date and end_date:
            data = await self.finmind_fetcher.fetch_fundamentals(ticker, start_date, end_date)
            if data:
                log.debug(f"Fetched fundamentals for {ticker} from FinMind.")
                return data
            else:
                log.warning(f"FinMind failed for fundamentals of {ticker}, trying yfinance...")

        # Fallback to yfinance
        data = await self.yfinance_fetcher.fetch_fundamentals(ticker)
        if data:
            log.debug(f"Fetched fundamentals for {ticker} from yfinance (fallback).")
            return data

        log.error(f"Failed to fetch fundamentals for {ticker} from both FinMind and yfinance.")
        return None

    async def fetch_multiple(
        self,
        tickers: list[str],
        period: str = "3mo",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[StockData]:
        """
        Fetches data for multiple tickers.

        Attempts FinMind first, then yfinance for each ticker, then Fugle.
        """
        # Try FinMind first for multiple stocks
        if start_date and end_date:
            finmind_results = await self.finmind_fetcher.fetch_multiple(
                tickers, start_date, end_date
            )
            if len(finmind_results) == len(tickers):  # All fetched successfully
                log.debug(f"Fetched {len(tickers)} stocks from FinMind.")
                return finmind_results
            elif finmind_results:  # Some fetched, try fallback for others
                log.warning(
                    f"FinMind only fetched {len(finmind_results)}/{len(tickers)} stocks. Trying yfinance for missing ones."
                )
                fetched_tickers = {s.ticker for s in finmind_results}
                remaining_tickers = [t for t in tickers if t not in fetched_tickers]
                yfinance_results = await self.yfinance_fetcher.fetch_multiple(
                    remaining_tickers, period
                )
                # Try Fugle for any still missing
                if yfinance_results:
                    missing_from_yfinance = [
                        t
                        for t in remaining_tickers
                        if t not in {s.ticker for s in yfinance_results}
                    ]
                    if missing_from_yfinance:
                        from datetime import datetime, timedelta

                        fugle_end = end_date or datetime.now().strftime("%Y-%m-%d")
                        fugle_start = start_date or (datetime.now() - timedelta(days=90)).strftime(
                            "%Y-%m-%d"
                        )
                        fugle_results = (
                            await self.fugle_fetcher.fetch_stock(
                                missing_from_yfinance[0], fugle_start, fugle_end
                            )
                            if missing_from_yfinance
                            else None
                        )
                        if fugle_results:
                            finmind_results.append(fugle_results)
                return finmind_results + yfinance_results
            else:
                log.warning(
                    f"FinMind failed for all {len(tickers)} stocks, trying yfinance for all."
                )

        # Fallback to yfinance for all if FinMind completely failed or dates not provided
        yfinance_results = await self.yfinance_fetcher.fetch_multiple(tickers, period)
        if yfinance_results:
            log.debug(f"Fetched {len(yfinance_results)} stocks from yfinance (fallback).")
            return yfinance_results

        # Try Fugle as tertiary fallback
        log.debug("yfinance failed for all stocks, trying Fugle...")
        if start_date and end_date:
            fugle_results = []
            for ticker in tickers:
                data = await self.fugle_fetcher.fetch_stock(ticker, start_date, end_date)
                if data:
                    fugle_results.append(data)
            if fugle_results:
                log.debug(f"Fetched {len(fugle_results)} stocks from Fugle (tertiary fallback).")
                return fugle_results
        else:
            from datetime import datetime, timedelta

            fugle_end = datetime.now().strftime("%Y-%m-%d")
            fugle_start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            fugle_results = []
            for ticker in tickers:
                data = await self.fugle_fetcher.fetch_stock(ticker, fugle_start, fugle_end)
                if data:
                    fugle_results.append(data)
            if fugle_results:
                log.debug(f"Fetched {len(fugle_results)} stocks from Fugle (tertiary fallback).")
                return fugle_results

        log.error("Failed to fetch multiple tickers from FinMind, yfinance, and Fugle.")
        return []

    async def fetch_history(
        self,
        ticker: str,
        period: str = "3mo",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame | None:
        """
        Fetches historical data as DataFrame.

        Attempts FinMind first, then yfinance, then Fugle.
        """
        # Try FinMind first
        if start_date and end_date:
            df = await self.finmind_fetcher.fetch_history(ticker, start_date, end_date)
            if df is not None and not df.empty:
                log.debug(f"Fetched history for {ticker} from FinMind.")
                return df
            else:
                log.warning(f"FinMind failed for history of {ticker}, trying yfinance...")

        # Fallback to yfinance
        df = self.yfinance_fetcher.get_history_df(
            ticker, period
        )  # yfinance fetch_history is async wrapper
        if df is not None and not df.empty:
            log.debug(f"Fetched history for {ticker} from yfinance (fallback).")
            return df

        # Try Fugle as tertiary fallback
        log.debug(f"yfinance failed for {ticker}, trying Fugle...")
        if start_date and end_date:
            df = await self.fugle_fetcher.fetch_history(ticker, start_date, end_date)
            if df is not None and not df.empty:
                log.debug(f"Fetched history for {ticker} from Fugle (tertiary fallback).")
                return df
        else:
            from datetime import datetime, timedelta

            fugle_end = end_date or datetime.now().strftime("%Y-%m-%d")
            fugle_start = start_date or (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            df = await self.fugle_fetcher.fetch_history(ticker, fugle_start, fugle_end)
            if df is not None and not df.empty:
                log.debug(f"Fetched history for {ticker} from Fugle (tertiary fallback).")
                return df

        log.error(f"Failed to fetch history for {ticker} from all sources.")
        return None

    async def fetch_index(
        self,
        index_name: str,
        period: str = "3mo",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> StockData | None:
        """
        Fetches market index data.

        Attempts FinMind first, then yfinance, then Fugle.
        """
        # Try FinMind first
        if start_date and end_date:
            data = await self.finmind_fetcher.fetch_index(index_name, start_date, end_date)
            if data:
                log.debug(f"Fetched index {index_name} from FinMind.")
                return data
            else:
                log.warning(f"FinMind failed for index {index_name}, trying yfinance...")

        # Fallback to yfinance
        data = await self.yfinance_fetcher.fetch_index(index_name, period)
        if data:
            log.debug(f"Fetched index {index_name} from yfinance (fallback).")
            return data

        # Try Fugle as tertiary fallback
        log.debug(f"yfinance failed for index {index_name}, trying Fugle...")
        if start_date and end_date:
            data = await self.fugle_fetcher.fetch_index(index_name, start_date, end_date)
            if data:
                log.debug(f"Fetched index {index_name} from Fugle (tertiary fallback).")
                return data
        else:
            from datetime import datetime, timedelta

            fugle_end = end_date or datetime.now().strftime("%Y-%m-%d")
            fugle_start = start_date or (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            data = await self.fugle_fetcher.fetch_index(index_name, fugle_start, fugle_end)
            if data:
                log.debug(f"Fetched index {index_name} from Fugle (tertiary fallback).")
                return data

        log.error(f"Failed to fetch index {index_name} from all sources.")
        return None

    async def fetch_institutional_investors(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame | None:
        """
        Fetches institutional investor data.

        Attempts FinMind first. No fallback to yfinance or Fugle as they don't provide this data.
        """
        if start_date and end_date:
            df = await self.finmind_fetcher.fetch_institutional_investors(
                ticker, start_date, end_date
            )
            if df is not None and not df.empty:
                log.debug(f"Fetched institutional investor data for {ticker} from FinMind.")
                return df
            else:
                log.warning(f"FinMind failed for institutional investor data of {ticker}.")

        log.warning(
            f"Institutional investor data for {ticker} not available from FinMind (yfinance and Fugle not supported)."
        )
        return None

    async def close(self) -> None:
        """
        Close all data fetcher sessions and clean up resources.
        """
        await self.fugle_fetcher.close()
