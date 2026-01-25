"""yfinance data fetcher for Taiwan stocks (fallback)."""

import pandas as pd
import yfinance as yf

from pulse.core.models import OHLCV, FundamentalData, StockData
from pulse.utils.logger import get_logger
from pulse.utils.retry import RetryPolicy

log = get_logger(__name__)


# Default retry policy for yfinance calls
YFINANCE_RETRY_POLICY = RetryPolicy(
    max_retries=2,
    initial_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
)


class YFinanceFetcher:
    """Fetch stock data from yfinance for Taiwan stocks."""

    # Taiwan market indices mapping
    INDEX_MAPPING = {
        "TAIEX": ("^TWII", "Taiwan Weighted Index"),
        "TWII": ("^TWII", "Taiwan Weighted Index"),
        "TPEX": ("^TWOTCI", "Taiwan OTC Index"),
        "OTC": ("^TWOTCI", "Taiwan OTC Index"),
        "TW50": ("0050.TW", "Taiwan 50 ETF"),
    }

    def __init__(self, suffix: str = ".TW"):
        """
        Initialize yfinance fetcher.

        Args:
            suffix: Ticker suffix for Taiwan (default: .TW)
        """
        self.suffix = suffix

    def _format_ticker(self, ticker: str) -> str:
        """Format ticker with Taiwan suffix (.TW)."""
        ticker = ticker.upper().strip()

        # Check if it's an index
        if ticker in self.INDEX_MAPPING:
            return self.INDEX_MAPPING[ticker][0]

        # Don't add suffix to indices starting with ^
        if ticker.startswith("^"):
            return ticker

        if not ticker.endswith(self.suffix):
            return f"{ticker}{self.suffix}"
        return ticker

    def _clean_ticker(self, ticker: str) -> str:
        """Remove suffix from ticker."""
        if ticker.endswith(self.suffix):
            return ticker[: -len(self.suffix)]
        return ticker

    async def fetch_stock(
        self,
        ticker: str,
        period: str = "3mo",
    ) -> StockData | None:
        """
        Fetch stock data for a ticker.

        Args:
            ticker: Stock ticker (e.g., "2330", "2881")
            period: Historical data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

        Returns:
            StockData object or None if failed
        """
        formatted_ticker = self._format_ticker(ticker)
        clean_ticker = self._clean_ticker(ticker)

        try:
            log.debug(f"Fetching {formatted_ticker} from yfinance...")

            stock = yf.Ticker(formatted_ticker)

            # Get historical data
            hist = stock.history(period=period)

            if hist.empty:
                log.warning(f"No data found for {ticker}")
                return None

            # Get stock info
            info = stock.info or {}

            # Convert history to OHLCV list
            history: list[OHLCV] = []
            for date, row in hist.iterrows():
                history.append(
                    OHLCV(
                        date=date.to_pydatetime(),
                        open=float(row.get("Open", 0)),
                        high=float(row.get("High", 0)),
                        low=float(row.get("Low", 0)),
                        close=float(row.get("Close", 0)),
                        volume=int(row.get("Volume", 0)),
                    )
                )

            # Get latest data
            latest = history[-1] if history else None
            prev = history[-2] if len(history) > 1 else None

            current_price = latest.close if latest else 0.0
            previous_close = prev.close if prev else current_price
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0.0

            # Calculate 52-week high/low
            week_52_data = hist.tail(252) if len(hist) >= 252 else hist
            week_52_high = float(week_52_data["High"].max()) if not week_52_data.empty else 0.0
            week_52_low = float(week_52_data["Low"].min()) if not week_52_data.empty else 0.0

            return StockData(
                ticker=clean_ticker,
                name=info.get("longName") or info.get("shortName"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                current_price=current_price,
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                volume=latest.volume if latest else 0,
                avg_volume=int(info.get("averageVolume", 0)),
                day_low=latest.low if latest else 0.0,
                day_high=latest.high if latest else 0.0,
                week_52_low=week_52_low,
                week_52_high=week_52_high,
                market_cap=info.get("marketCap"),
                shares_outstanding=info.get("sharesOutstanding"),
                history=history,
            )

        except TimeoutError:
            log.error(f"Timeout fetching {ticker} from yfinance")
            return None
        except ConnectionError as e:
            log.error(f"Connection error fetching {ticker}: {e}")
            return None
        except Exception as e:
            log.error(f"Error fetching {ticker}: {e}")
            return None

    async def fetch_fundamentals(self, ticker: str) -> FundamentalData | None:
        """
        Fetch fundamental data for a ticker.

        Args:
            ticker: Stock ticker

        Returns:
            FundamentalData object or None if failed
        """
        formatted_ticker = self._format_ticker(ticker)
        clean_ticker = self._clean_ticker(ticker)

        try:
            stock = yf.Ticker(formatted_ticker)
            info = stock.info or {}

            if not info:
                return None

            return FundamentalData(
                ticker=clean_ticker,
                pe_ratio=info.get("trailingPE") or info.get("forwardPE"),
                pb_ratio=info.get("priceToBook"),
                ps_ratio=info.get("priceToSalesTrailing12Months"),
                peg_ratio=info.get("pegRatio"),
                ev_ebitda=info.get("enterpriseToEbitda"),
                roe=info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None,
                roa=info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None,
                npm=info.get("profitMargins", 0) * 100 if info.get("profitMargins") else None,
                opm=info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else None,
                gpm=info.get("grossMargins", 0) * 100 if info.get("grossMargins") else None,
                eps=info.get("trailingEps"),
                bvps=info.get("bookValue"),
                dps=info.get("dividendRate"),
                revenue_growth=info.get("revenueGrowth", 0) * 100
                if info.get("revenueGrowth")
                else None,
                earnings_growth=info.get("earningsGrowth", 0) * 100
                if info.get("earningsGrowth")
                else None,
                debt_to_equity=info.get("debtToEquity"),
                current_ratio=info.get("currentRatio"),
                quick_ratio=info.get("quickRatio"),
                dividend_yield=info.get("dividendYield", 0) * 100
                if info.get("dividendYield")
                else None,
                payout_ratio=info.get("payoutRatio", 0) * 100 if info.get("payoutRatio") else None,
                market_cap=info.get("marketCap"),
                enterprise_value=info.get("enterpriseValue"),
            )

        except Exception as e:
            log.error(f"Error fetching fundamentals for {ticker}: {e}")
            return None

    async def fetch_multiple(
        self,
        tickers: list[str],
        period: str = "3mo",
    ) -> list[StockData]:
        """
        Fetch data for multiple tickers.

        Args:
            tickers: List of stock tickers
            period: Historical data period

        Returns:
            List of StockData objects
        """
        results = []

        for ticker in tickers:
            data = await self.fetch_stock(ticker, period)
            if data:
                results.append(data)

        return results

    async def fetch_history(
        self,
        ticker: str,
        period: str | None = None,
        start = None,
        end = None,
    ) -> pd.DataFrame | None:
        """
        Fetch historical data as DataFrame (async wrapper).

        Args:
            ticker: Stock ticker
            period: Historical data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: Start date (datetime or str), used if period is None
            end: End date (datetime or str), used if period is None

        Returns:
            DataFrame with OHLCV data
        """
        return self.get_history_df(ticker, period=period, start=start, end=end)

    def get_history_df(
        self,
        ticker: str,
        period: str | None = None,
        start = None,
        end = None,
    ) -> pd.DataFrame | None:
        """
        Get historical data as pandas DataFrame (for technical analysis).

        Args:
            ticker: Stock ticker
            period: Historical data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: Start date (datetime or str), used if period is None
            end: End date (datetime or str), used if period is None

        Returns:
            DataFrame with OHLCV data
        """
        formatted_ticker = self._format_ticker(ticker)

        try:
            stock = yf.Ticker(formatted_ticker)
            
            # 優先使用 period，若為 None 則使用 start/end
            if period:
                hist = stock.history(period=period)
            elif start and end:
                hist = stock.history(start=start, end=end)
            elif start:
                hist = stock.history(start=start)
            else:
                # 預設使用 1 年
                hist = stock.history(period="1y")

            if hist.empty:
                return None

            # Ensure column names are lowercase for ta library
            hist.columns = hist.columns.str.lower()

            return hist

        except Exception as e:
            log.error(f"Error fetching history for {ticker}: {e}")
            return None

    async def fetch_index(
        self,
        index_name: str,
        period: str = "3mo",
    ) -> StockData | None:
        """
        Fetch market index data (TAIEX, TPEX, etc).

        Args:
            index_name: Index name (TAIEX, TPEX, TW50, OTC)
            period: Historical data period

        Returns:
            StockData object with index data, or None if failed
        """
        index_name = index_name.upper().strip()

        # Map index name to yfinance ticker
        if index_name in self.INDEX_MAPPING:
            yf_ticker, display_name = self.INDEX_MAPPING[index_name]
        elif index_name.startswith("^"):
            yf_ticker = index_name
            display_name = index_name
        else:
            log.warning(f"Unknown index: {index_name}")
            return None

        try:
            log.debug(f"Fetching index {yf_ticker} from yfinance...")

            stock = yf.Ticker(yf_ticker)

            # Get historical data
            hist = stock.history(period=period)

            if hist.empty:
                log.warning(f"No data found for index {index_name}")
                return None

            # Get index info
            info = stock.info or {}

            # Convert history to OHLCV list
            history: list[OHLCV] = []
            for date, row in hist.iterrows():
                history.append(
                    OHLCV(
                        date=date.to_pydatetime(),
                        open=float(row.get("Open", 0)),
                        high=float(row.get("High", 0)),
                        low=float(row.get("Low", 0)),
                        close=float(row.get("Close", 0)),
                        volume=int(row.get("Volume", 0)),
                    )
                )

            # Get latest data
            latest = history[-1] if history else None
            prev = history[-2] if len(history) > 1 else None

            current_price = latest.close if latest else 0.0
            previous_close = prev.close if prev else current_price
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0.0

            # Calculate 52-week high/low
            week_52_data = hist.tail(252) if len(hist) >= 252 else hist
            week_52_high = float(week_52_data["High"].max()) if not week_52_data.empty else 0.0
            week_52_low = float(week_52_data["Low"].min()) if not week_52_data.empty else 0.0

            return StockData(
                ticker=index_name,
                name=display_name,
                sector="Index",
                industry="Market Index",
                current_price=current_price,
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                volume=latest.volume if latest else 0,
                avg_volume=int(info.get("averageVolume", 0)),
                day_low=latest.low if latest else 0.0,
                day_high=latest.high if latest else 0.0,
                week_52_low=week_52_low,
                week_52_high=week_52_high,
                market_cap=None,
                shares_outstanding=None,
                history=history,
            )

        except Exception as e:
            log.error(f"Error fetching index {index_name}: {e}")
            return None
