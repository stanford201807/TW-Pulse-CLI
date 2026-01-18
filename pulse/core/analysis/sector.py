"""Sector analysis engine."""

from datetime import datetime
from typing import Any

from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.models import SectorAnalysis, StockData
from pulse.utils.constants import MIDCAP100_TICKERS, TW50_TICKERS, TW_SECTORS
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class SectorAnalyzer:
    """Analyze sector performance and rotation."""

    def __init__(self):
        """Initialize sector analyzer."""
        self.fetcher = YFinanceFetcher()

    async def analyze_sector(
        self,
        sector: str,
        limit: int = 10,
    ) -> SectorAnalysis | None:
        """
        Analyze a specific sector.

        Args:
            sector: Sector name (e.g., "BANKING", "MINING")
            limit: Max stocks to analyze per sector

        Returns:
            SectorAnalysis object
        """
        sector_upper = sector.upper()

        if sector_upper not in TW_SECTORS:
            log.warning(f"Unknown sector: {sector}")
            return None

        tickers = TW_SECTORS[sector_upper][:limit]

        # Fetch data for all tickers
        stocks: list[StockData] = []
        for ticker in tickers:
            data = await self.fetcher.fetch_stock(ticker, period="5d")
            if data:
                stocks.append(data)

        if not stocks:
            return None

        return self._build_sector_analysis(sector_upper, stocks)

    def _build_sector_analysis(
        self,
        sector: str,
        stocks: list[StockData],
    ) -> SectorAnalysis:
        """Build sector analysis from stock data."""
        # Calculate aggregates
        total_volume = sum(s.volume for s in stocks)
        total_value = sum(s.volume * s.current_price for s in stocks)
        avg_change = sum(s.change_percent for s in stocks) / len(stocks) if stocks else 0

        # Sort for gainers/losers
        sorted_by_change = sorted(stocks, key=lambda x: x.change_percent, reverse=True)
        sorted_by_volume = sorted(stocks, key=lambda x: x.volume, reverse=True)

        top_gainers = [
            {
                "ticker": s.ticker,
                "change_percent": s.change_percent,
                "price": s.current_price,
                "volume": s.volume,
            }
            for s in sorted_by_change[:5]
            if s.change_percent > 0
        ]

        top_losers = [
            {
                "ticker": s.ticker,
                "change_percent": s.change_percent,
                "price": s.current_price,
                "volume": s.volume,
            }
            for s in sorted_by_change[-5:]
            if s.change_percent < 0
        ]

        most_active = [
            {
                "ticker": s.ticker,
                "volume": s.volume,
                "value": s.volume * s.current_price,
                "change_percent": s.change_percent,
            }
            for s in sorted_by_volume[:5]
        ]

        return SectorAnalysis(
            sector=sector,
            total_stocks=len(stocks),
            avg_change_percent=avg_change,
            total_volume=total_volume,
            total_value=total_value,
            top_gainers=top_gainers,
            top_losers=top_losers,
            most_active=most_active,
        )

    async def get_sector_rotation(self) -> dict[str, Any]:
        """
        Analyze sector rotation and relative strength.

        Returns:
            Sector rotation analysis
        """
        sector_performance = {}

        for sector, tickers in TW_SECTORS.items():
            # Skip sub-sectors if needed
            if sector in ["BANKING", "INSURANCE"]:  # BANKING and INSURANCE are separate
                continue

            # Sample a few stocks from each sector
            sample_tickers = tickers[:5]
            changes = []

            for ticker in sample_tickers:
                data = await self.fetcher.fetch_stock(ticker, period="1mo")
                if data and data.history:
                    # Calculate 1-month return
                    first_close = data.history[0].close
                    last_close = data.history[-1].close
                    if first_close > 0:
                        monthly_return = ((last_close - first_close) / first_close) * 100
                        changes.append(monthly_return)

            if changes:
                avg_return = sum(changes) / len(changes)
                sector_performance[sector] = {
                    "avg_return": avg_return,
                    "sample_size": len(changes),
                }

        # Sort by performance
        sorted_sectors = sorted(
            sector_performance.items(), key=lambda x: x[1]["avg_return"], reverse=True
        )

        return {
            "leaders": [{"sector": s, "return": d["avg_return"]} for s, d in sorted_sectors[:3]],
            "laggards": [{"sector": s, "return": d["avg_return"]} for s, d in sorted_sectors[-3:]],
            "all_sectors": {s: d["avg_return"] for s, d in sorted_sectors},
            "analyzed_at": datetime.now().isoformat(),
        }

    async def get_index_summary(self, index: str = "TW50") -> dict[str, Any]:
        """
        Get summary for a major index.

        Args:
            index: Index name (TW50 or MIDCAP)

        Returns:
            Index summary
        """
        if index.upper() in ["TW50", "LQ45"]:  # LQ45 for backward compat
            tickers = TW50_TICKERS
        elif index.upper() in ["MIDCAP", "TW100", "IDX80"]:  # IDX80 for backward compat
            tickers = MIDCAP100_TICKERS
        else:
            log.warning(f"Unknown index: {index}")
            return {}

        stocks: list[StockData] = []
        for ticker in tickers[:20]:  # Limit for performance
            data = await self.fetcher.fetch_stock(ticker, period="5d")
            if data:
                stocks.append(data)

        if not stocks:
            return {}

        # Calculate aggregates
        total_market_cap = sum(s.market_cap or 0 for s in stocks)
        avg_change = sum(s.change_percent for s in stocks) / len(stocks)
        gainers = sum(1 for s in stocks if s.change_percent > 0)
        losers = sum(1 for s in stocks if s.change_percent < 0)

        # Top movers
        sorted_stocks = sorted(stocks, key=lambda x: x.change_percent, reverse=True)

        return {
            "index": index.upper(),
            "stocks_analyzed": len(stocks),
            "total_market_cap": total_market_cap,
            "avg_change_percent": avg_change,
            "gainers": gainers,
            "losers": losers,
            "unchanged": len(stocks) - gainers - losers,
            "top_gainers": [
                {"ticker": s.ticker, "change": s.change_percent} for s in sorted_stocks[:5]
            ],
            "top_losers": [
                {"ticker": s.ticker, "change": s.change_percent} for s in sorted_stocks[-5:]
            ],
            "analyzed_at": datetime.now().isoformat(),
        }

    def list_sectors(self) -> list[dict[str, Any]]:
        """List all available sectors."""
        return [
            {
                "name": sector,
                "stock_count": len(tickers),
                "sample_tickers": tickers[:5],
            }
            for sector, tickers in TW_SECTORS.items()
        ]

    def get_sector_for_ticker(self, ticker: str) -> list[str]:
        """
        Get sectors that a ticker belongs to.

        Args:
            ticker: Stock ticker

        Returns:
            List of sector names
        """
        ticker_upper = ticker.upper()
        sectors = []

        for sector, tickers in TW_SECTORS.items():
            if ticker_upper in tickers:
                sectors.append(sector)

        return sectors
