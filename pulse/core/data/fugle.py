"""Fugle Market Data provider for Taiwan stocks (third-tier fallback)."""

import base64
import threading
from typing import Any

import httpx

from pulse.core.models import StockData
from pulse.utils.logger import get_logger

log = get_logger(__name__)

# Fugle API configuration
FUGLE_BASE_URL = "https://api.fugle.tw"
FUGLE_API_VERSION = "marketdata/v1.0"


def decode_api_key(key: str) -> str:
    """Decode base64 API key if encoded."""
    try:
        if key and len(key) > 32:
            return base64.b64decode(key).decode("utf-8")
    except Exception:
        pass
    return key


class FugleFetcher:
    """Fetch stock data from Fugle Market Data API for Taiwan stocks."""

    # Taiwan market indices mapping
    INDEX_MAPPING = {
        "TAIEX": ("TAIEX", "Taiwan Weighted Index"),
        "TWII": ("TAIEX", "Taiwan Weighted Index"),
        "TPEX": ("TPEX", "Taiwan OTC Index"),
        "OTC": ("TPEX", "Taiwan OTC Index"),
    }

    def __init__(self, api_key: str = ""):
        """
        Initialize Fugle fetcher.

        Args:
            api_key: Fugle API key (optional, can also use FUGLE_API_KEY env var)
        """
        # New Fugle API keys are base64 encoded, use as-is
        self.api_key = api_key
        self._client: httpx.Client | None = None
        self._lock = threading.Lock()

    def _get_client(self) -> httpx.Client:
        """Get or create httpx client (singleton pattern)."""
        if self._client is None or self._client.is_closed:
            with self._lock:
                if self._client is None or self._client.is_closed:
                    self._client = httpx.Client(
                        headers=self._get_headers(),
                        timeout=30.0,
                    )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers

    def _format_ticker(self, ticker: str) -> str:
        """Format ticker for Fugle API."""
        ticker = ticker.upper().strip()
        if ticker.endswith(".TW"):
            ticker = ticker[:-3]
        elif ticker.endswith(".TWO"):
            ticker = ticker[:-4]
        return ticker

    def close(self) -> None:
        """Close the httpx client."""
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None

    def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Make HTTP request to Fugle API.

        Args:
            endpoint: API endpoint (e.g., "/stock/historical/stats/2330")
            params: Query parameters

        Returns:
            JSON response as dict or None if failed
        """
        url = f"{FUGLE_BASE_URL}/{FUGLE_API_VERSION}{endpoint}"

        if params is None:
            params = {}

        client = self._get_client()

        try:
            response = client.get(url, params=params)

            if response.status_code == 429:
                log.warning("Fugle API rate limit exceeded")
                raise RateLimitError("Fugle API rate limit exceeded")

            if response.status_code == 401:
                raise UnauthorizedError("Fugle API unauthorized - check API key")

            if response.status_code == 404:
                raise NotFoundError(f"Fugle API: resource not found at {endpoint}")

            if response.status_code >= 400:
                text = response.text
                raise APIError(f"Fugle API error {response.status_code}: {text}")

            return response.json()

        except httpx.RequestError as e:
            log.error(f"Fugle API connection error: {e}")
            raise NetworkError(f"Fugle API connection error: {e}")

    def fetch_stock(
        self,
        ticker: str,
        start_date: str = "",
        end_date: str = "",
    ) -> StockData | None:
        """
        Fetch stock data for a ticker from Fugle.

        Args:
            ticker: Stock ticker (e.g., "2330")
            start_date: Start date (YYYY-MM-DD) - optional for stats endpoint
            end_date: End date (YYYY-MM-DD) - optional for stats endpoint

        Returns:
            StockData object or None if failed
        """
        formatted_ticker = self._format_ticker(ticker)

        try:
            log.debug(f"Fetching stock data for {formatted_ticker} from Fugle...")

            # Use /historical/stats endpoint for basic stock info
            stats_data = self._make_request(
                f"/stock/historical/stats/{formatted_ticker}",
            )

            if not stats_data:
                log.warning(f"No data found for {ticker} from Fugle")
                return None

            # Parse stats response
            data = stats_data
            if isinstance(stats_data, dict) and "data" in stats_data:
                data = stats_data["data"]

            # Extract values
            name = data.get("name", "")
            current_price = data.get("closePrice", 0)
            previous_close = data.get("previousClose", 0)
            change = data.get("change", 0)
            change_percent = data.get("changePercent", 0)
            week_52_high = data.get("week52High", 0)
            week_52_low = data.get("week52Low", 0)
            volume = data.get("tradeVolume", 0)
            day_high = data.get("highPrice", 0)
            day_low = data.get("lowPrice", 0)

            # Calculate avg volume (use tradeVolume as proxy)
            avg_volume = volume

            return StockData(
                ticker=formatted_ticker,
                name=name,
                sector=None,
                industry=None,
                current_price=current_price,
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                volume=volume,
                avg_volume=avg_volume,
                day_low=day_low,
                day_high=day_high,
                week_52_low=week_52_low,
                week_52_high=week_52_high,
                market_cap=None,
                shares_outstanding=None,
                history=[],  # Stats endpoint doesn't provide history
            )

        except Exception as e:
            log.error(f"Error fetching {ticker} from Fugle: {e}")
            return None

    def fetch_index(
        self,
        index_name: str,
        start_date: str = "",
        end_date: str = "",
    ) -> StockData | None:
        """
        Fetch market index data from Fugle.

        Args:
            index_name: Index name (TAIEX, TPEX)
            start_date: Start date (YYYY-MM-DD) - optional
            end_date: End date (YYYY-MM-DD) - optional

        Returns:
            StockData object with index data, or None if failed
        """
        index_name = index_name.upper().strip()

        # Map index name to Fugle symbol (use ETF as proxy for index)
        # TAIEX = 0050 (台灣50) as proxy
        # TPEX = 0051 (台灣50微) or similar
        if index_name in ["TAIEX", "TWII"]:
            # Use 0050 as TAIEX proxy
            proxy_symbol = "0050"
            display_name = "Taiwan Weighted Index (TAIEX)"
        elif index_name in ["TPEX", "OTC"]:
            proxy_symbol = "0051"
            display_name = "Taiwan OTC Index (TPEX)"
        else:
            log.warning(f"Unknown index: {index_name}")
            return None

        try:
            log.debug(f"Fetching index {index_name} from Fugle (via {proxy_symbol})...")

            stats_data = self._make_request(
                f"/stock/historical/stats/{proxy_symbol}",
            )

            if not stats_data:
                log.warning(f"No data found for index {index_name} from Fugle")
                return None

            # Parse stats response
            data = stats_data
            if isinstance(stats_data, dict) and "data" in stats_data:
                data = stats_data["data"]

            current_price = data.get("closePrice", 0)
            previous_close = data.get("previousClose", 0)
            change = data.get("change", 0)
            change_percent = data.get("changePercent", 0)
            week_52_high = data.get("week52High", 0)
            week_52_low = data.get("week52Low", 0)
            volume = data.get("tradeVolume", 0)
            day_high = data.get("highPrice", 0)
            day_low = data.get("lowPrice", 0)

            return StockData(
                ticker=index_name,
                name=display_name,
                sector="Index",
                industry="Market Index",
                current_price=current_price,
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                volume=volume,
                avg_volume=0,
                day_low=day_low,
                day_high=day_high,
                week_52_low=week_52_low,
                week_52_high=week_52_high,
                market_cap=None,
                shares_outstanding=None,
                history=[],
            )

        except NotFoundError:
            log.warning(f"Index {index_name} not found in Fugle API")
            return None
        except Exception as e:
            log.error(f"Error fetching index {index_name} from Fugle: {e}")
            return None

    def search_symbols(self, query: str) -> list[dict[str, Any]] | None:
        """
        Search for stock symbols by name or ticker.

        Args:
            query: Search query

        Returns:
            List of matching symbols
        """
        try:
            log.debug(f"Searching for symbols matching '{query}' in Fugle...")

            data = self._make_request(
                "/stock/info",
                params={"keyword": query},
            )

            if data and "data" in data:
                return data["data"]

            return None

        except Exception as e:
            log.error(f"Error searching symbols in Fugle: {e}")
            return None


# Custom exception classes for Fugle API errors
class FugleAPIError(Exception):
    """Base exception for Fugle API errors."""

    pass


class RateLimitError(FugleAPIError):
    """Raised when Fugle API rate limit is exceeded."""

    pass


class UnauthorizedError(FugleAPIError):
    """Raised when Fugle API authentication fails."""

    pass


class NotFoundError(FugleAPIError):
    """Raised when Fugle API resource is not found."""

    pass


class NetworkError(FugleAPIError):
    """Raised when Fugle API network request fails."""

    pass


class APIError(FugleAPIError):
    """Raised when Fugle API returns an error."""

    pass
