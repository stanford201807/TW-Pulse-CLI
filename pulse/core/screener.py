"""
Stock Screener - Filter stocks by technical and fundamental criteria.

Supports:
1. Preset screeners (oversold, bullish, breakout, etc)
2. Flexible criteria (rsi<30, pe<15, etc)
3. AI-driven smart screening
"""

import asyncio
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pulse.utils.constants import MIDCAP100_TICKERS, TPEX_POPULAR, TW50_TICKERS
from pulse.utils.logger import get_logger

log = get_logger(__name__)


def load_all_tickers() -> list[str]:
    """Load all tickers (TW50 + MIDCAP + POPULAR combined)."""
    # Combine all ticker lists and remove duplicates
    all_tickers = list(set(TW50_TICKERS + MIDCAP100_TICKERS + TPEX_POPULAR))
    return sorted(all_tickers)


class ScreenPreset(str, Enum):
    """Predefined screening presets."""

    OVERSOLD = "oversold"
    OVERBOUGHT = "overbought"
    BULLISH = "bullish"
    BEARISH = "bearish"
    BREAKOUT = "breakout"
    SQUEEZE = "squeeze"
    UNDERVALUED = "undervalued"
    DIVIDEND = "dividend"
    MOMENTUM = "momentum"


class StockUniverse(str, Enum):
    """Stock universe for screening."""

    TW50 = "tw50"  # Taiwan 50 Index components
    MIDCAP = "midcap"  # Mid-cap 100 stocks
    POPULAR = "popular"  # Popular stocks
    ALL = "all"  # All Taiwan stocks


@dataclass
class ScreenResult:
    """Result from stock screening."""

    ticker: str
    name: str | None = None
    sector: str | None = None

    # Price data
    price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    avg_volume: int = 0

    # Technical indicators
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    bb_upper: float | None = None
    bb_lower: float | None = None
    bb_middle: float | None = None
    stoch_k: float | None = None
    stoch_d: float | None = None

    # Fundamental data
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    dividend_yield: float | None = None
    market_cap: float | None = None  # in TWD
    earnings_growth: float | None = None  # YoY %
    revenue_growth: float | None = None  # YoY %

    # Support/Resistance
    support: float | None = None
    resistance: float | None = None

    # Scoring
    score: float = 0.0
    signals: list[str] = field(default_factory=list)

    @property
    def volume_ratio(self) -> float:
        """Volume vs average volume ratio."""
        if self.avg_volume > 0:
            return self.volume / self.avg_volume
        return 1.0

    @property
    def market_cap_category(self) -> str:
        """Categorize market cap: micro, small, mid, large, mega."""
        if self.market_cap is None:
            return "unknown"
        mc = self.market_cap
        if mc < 500e9:  # < 500B = micro cap
            return "micro"
        elif mc < 2e12:  # < 2T = small cap
            return "small"
        elif mc < 10e12:  # < 10T = mid cap
            return "mid"
        elif mc < 50e12:  # < 50T = large cap
            return "large"
        else:  # >= 50T = mega cap
            return "mega"

    @property
    def rsi_status(self) -> str:
        """RSI status description."""
        if self.rsi_14 is None:
            return "N/A"
        if self.rsi_14 < 30:
            return "Oversold"
        if self.rsi_14 > 70:
            return "Overbought"
        return "Neutral"

    @property
    def macd_status(self) -> str:
        """MACD status description."""
        if self.macd is None or self.macd_signal is None:
            return "N/A"
        if self.macd > self.macd_signal:
            return "Bullish"
        return "Bearish"


class StockScreener:
    """
    Screen stocks based on technical and fundamental criteria.

    Usage:
        screener = StockScreener()

        # Using preset
        results = await screener.screen_preset(ScreenPreset.OVERSOLD)

        # Using flexible criteria
        results = await screener.screen_criteria("rsi<30 and volume>1000000")

        # AI smart screening
        results = await screener.smart_screen("saham yang akan naik")
    """

    # Preset criteria definitions
    PRESETS = {
        ScreenPreset.OVERSOLD: {
            "description": "Oversold stocks (RSI < 30)",
            "criteria": {"rsi_14": ("<", 30)},
            "sort_by": "rsi_14",
            "sort_asc": True,
        },
        ScreenPreset.OVERBOUGHT: {
            "description": "Overbought stocks (RSI > 70)",
            "criteria": {"rsi_14": (">", 70)},
            "sort_by": "rsi_14",
            "sort_asc": False,
        },
        ScreenPreset.BULLISH: {
            "description": "Bullish momentum (MACD bullish + price > SMA20)",
            "criteria": {"macd_above_signal": True, "price_above_sma20": True},
            "sort_by": "score",
            "sort_asc": False,
        },
        ScreenPreset.BEARISH: {
            "description": "Bearish momentum (MACD bearish + price < SMA20)",
            "criteria": {"macd_below_signal": True, "price_below_sma20": True},
            "sort_by": "score",
            "sort_asc": False,
        },
        ScreenPreset.BREAKOUT: {
            "description": "Potential breakout (price near resistance + volume spike)",
            "criteria": {"near_resistance": True, "volume_spike": True},
            "sort_by": "volume_ratio",
            "sort_asc": False,
        },
        ScreenPreset.SQUEEZE: {
            "description": "Bollinger Band squeeze (low volatility, ready to move)",
            "criteria": {"bb_squeeze": True},
            "sort_by": "bb_width",
            "sort_asc": True,
        },
        ScreenPreset.UNDERVALUED: {
            "description": "Fundamentally undervalued (low PE, high ROE)",
            "criteria": {"pe_ratio": ("<", 15), "roe": (">", 10)},
            "sort_by": "pe_ratio",
            "sort_asc": True,
        },
        ScreenPreset.MOMENTUM: {
            "description": "Strong momentum (RSI 50-70, MACD bullish, volume up)",
            "criteria": {
                "rsi_14": ("between", (50, 70)),
                "macd_above_signal": True,
                "volume_above_avg": True,
            },
            "sort_by": "score",
            "sort_asc": False,
        },
    }

    def __init__(
        self,
        universe: list[str] | None = None,
        universe_type: StockUniverse | None = None,
    ):
        """
        Initialize screener with stock universe.

        Args:
            universe: Custom list of tickers. If provided, overrides universe_type.
            universe_type: Predefined universe type (TW50, MIDCAP, POPULAR, ALL).
        """
        if universe:
            self.universe = universe
        elif universe_type:
            self.universe = self._get_universe(universe_type)
        else:
            self.universe = TW50_TICKERS  # Default to TW50

    def _get_universe(self, universe_type: StockUniverse) -> list[str]:
        """Get stock universe based on type."""
        if universe_type == StockUniverse.TW50:
            return TW50_TICKERS
        elif universe_type == StockUniverse.MIDCAP:
            return MIDCAP100_TICKERS
        elif universe_type == StockUniverse.POPULAR:
            return TW50_TICKERS + TPEX_POPULAR  # Combined popular stocks
        elif universe_type == StockUniverse.ALL:
            return load_all_tickers()
        return TW50_TICKERS  # Default

    async def _fetch_stock_data(self, ticker: str) -> ScreenResult | None:
        """Fetch all data needed for screening."""
        try:
            from datetime import datetime, timedelta

            from pulse.core.analysis.technical import TechnicalAnalyzer
            from pulse.core.data.stock_data_provider import StockDataProvider

            # Initialize StockDataProvider (token will be managed by config)
            fetcher = StockDataProvider()

            # Define date range for fetching data (e.g., 1 year history for screening)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Fetch stock data
            # Assuming fetch_stock can handle both period and start/end dates
            stock = await fetcher.fetch_stock(
                ticker, period="1y", start_date=start_date_str, end_date=end_date_str
            )
            if not stock:
                return None

            # Fetch technical indicators
            analyzer = TechnicalAnalyzer()
            technical = await analyzer.analyze(ticker)

            result = ScreenResult(
                ticker=ticker,
                name=stock.name,
                sector=stock.sector,
                price=stock.current_price,
                change=stock.change,
                change_percent=stock.change_percent,
                volume=stock.volume,
                avg_volume=stock.avg_volume,
            )

            if technical:
                result.rsi_14 = technical.rsi_14
                result.macd = technical.macd
                result.macd_signal = technical.macd_signal
                result.macd_histogram = technical.macd_histogram
                result.sma_20 = technical.sma_20
                result.sma_50 = technical.sma_50
                result.bb_upper = technical.bb_upper
                result.bb_lower = technical.bb_lower
                result.bb_middle = technical.bb_middle
                result.stoch_k = technical.stoch_k
                result.stoch_d = technical.stoch_d
                result.support = technical.support_1
                result.resistance = technical.resistance_1

            # Fetch fundamental data (optional, may be slow)
            try:
                # Assuming fetch_fundamentals also uses start_date/end_date for FinMind
                fundamental = await fetcher.fetch_fundamentals(
                    ticker, start_date=start_date_str, end_date=end_date_str
                )
                if fundamental:
                    result.pe_ratio = fundamental.pe_ratio
                    result.pb_ratio = fundamental.pb_ratio
                    result.roe = fundamental.roe
                    result.dividend_yield = fundamental.dividend_yield
                    result.market_cap = fundamental.market_cap
                    result.earnings_growth = fundamental.earnings_growth
                    result.revenue_growth = fundamental.revenue_growth
            except Exception:
                pass

            return result

        except Exception as e:
            log.error(f"Error fetching data for {ticker}: {e}")
            return None

    def _matches_criteria(
        self,
        result: ScreenResult,
        criteria: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        Check if stock matches all criteria.

        Returns:
            Tuple of (matches, list of matched signals)
        """
        signals = []

        for key, condition in criteria.items():
            # Handle special conditions
            if key == "macd_above_signal":
                if condition and result.macd is not None and result.macd_signal is not None:
                    if result.macd > result.macd_signal:
                        signals.append("MACD Bullish")
                    else:
                        return False, []
                continue

            if key == "macd_below_signal":
                if condition and result.macd is not None and result.macd_signal is not None:
                    if result.macd < result.macd_signal:
                        signals.append("MACD Bearish")
                    else:
                        return False, []
                continue

            if key == "price_above_sma20":
                if condition and result.sma_20 is not None:
                    if result.price > result.sma_20:
                        signals.append("Price > SMA20")
                    else:
                        return False, []
                continue

            if key == "price_below_sma20":
                if condition and result.sma_20 is not None:
                    if result.price < result.sma_20:
                        signals.append("Price < SMA20")
                    else:
                        return False, []
                continue

            if key == "volume_spike":
                if condition and result.volume_ratio > 1.5:
                    signals.append(f"Volume Spike ({result.volume_ratio:.1f}x)")
                elif condition:
                    return False, []
                continue

            if key == "volume_above_avg":
                if condition and result.volume_ratio > 1.0:
                    signals.append("Volume > Avg")
                elif condition:
                    return False, []
                continue

            if key == "near_resistance":
                if condition and result.resistance and result.price:
                    pct_to_resistance = (result.resistance - result.price) / result.price * 100
                    if 0 < pct_to_resistance < 3:  # Within 3% of resistance
                        signals.append(f"Near Resistance ({pct_to_resistance:.1f}%)")
                    else:
                        return False, []
                continue

            if key == "bb_squeeze":
                if condition and result.bb_upper and result.bb_lower and result.bb_middle:
                    bb_width = (result.bb_upper - result.bb_lower) / result.bb_middle * 100
                    if bb_width < 10:  # Narrow bands = squeeze
                        signals.append(f"BB Squeeze ({bb_width:.1f}%)")
                    else:
                        return False, []
                continue

            # Market cap categories
            if key == "market_cap_small":
                if condition:
                    if result.market_cap_category in ["micro", "small"]:
                        signals.append(f"Small Cap ({result.market_cap_category})")
                    else:
                        return False, []
                continue

            if key == "market_cap_mid":
                if condition:
                    if result.market_cap_category == "mid":
                        signals.append("Mid Cap")
                    else:
                        return False, []
                continue

            if key == "market_cap_small_mid":
                if condition:
                    if result.market_cap_category in ["micro", "small", "mid"]:
                        signals.append(f"Cap: {result.market_cap_category}")
                    else:
                        return False, []
                continue

            # High growth
            if key == "high_growth":
                if condition:
                    has_growth = False
                    if result.earnings_growth and result.earnings_growth > 20:
                        signals.append(f"Earnings Growth: {result.earnings_growth:.0f}%")
                        has_growth = True
                    if result.revenue_growth and result.revenue_growth > 15:
                        signals.append(f"Revenue Growth: {result.revenue_growth:.0f}%")
                        has_growth = True
                    if not has_growth:
                        return False, []
                continue

            # Handle numeric comparisons
            value = getattr(result, key, None)
            if value is None:
                continue  # Skip if no data

            if isinstance(condition, tuple):
                operator, threshold = condition

                if operator == "<" and value >= threshold:
                    return False, []
                elif operator == ">" and value <= threshold:
                    return False, []
                elif operator == "<=" and value > threshold:
                    return False, []
                elif operator == ">=" and value < threshold:
                    return False, []
                elif operator == "between":
                    low, high = threshold
                    if not (low <= value <= high):
                        return False, []
                    signals.append(f"{key}: {value:.1f}")
                else:
                    signals.append(f"{key}: {value:.1f}")

        return True, signals

    def _calculate_score(self, result: ScreenResult) -> float:
        """Calculate overall score for ranking."""
        score = 50.0  # Base score

        # RSI scoring
        if result.rsi_14 is not None:
            if result.rsi_14 < 30:
                score += 20  # Oversold bonus
            elif result.rsi_14 > 70:
                score -= 10  # Overbought penalty
            elif 40 <= result.rsi_14 <= 60:
                score += 5  # Neutral is okay

        # MACD scoring
        if result.macd is not None and result.macd_signal is not None:
            if result.macd > result.macd_signal:
                score += 15  # Bullish
                if result.macd_histogram and result.macd_histogram > 0:
                    score += 5  # Increasing momentum
            else:
                score -= 10  # Bearish

        # Volume scoring
        if result.volume_ratio > 1.5:
            score += 10  # High volume interest
        elif result.volume_ratio < 0.5:
            score -= 5  # Low interest

        # Trend scoring
        if result.sma_20 and result.sma_50:
            if result.price > result.sma_20 > result.sma_50:
                score += 15  # Strong uptrend
            elif result.price < result.sma_20 < result.sma_50:
                score -= 10  # Strong downtrend

        # Fundamental scoring
        if result.pe_ratio:
            if 0 < result.pe_ratio < 15:
                score += 10  # Undervalued
            elif result.pe_ratio > 30:
                score -= 5  # Expensive

        if result.roe:
            if result.roe > 15:
                score += 10  # Good ROE

        return max(0, min(100, score))

    def parse_criteria(self, criteria_str: str) -> dict[str, Any]:
        """
        Parse criteria string into dict.

        Examples:
            "rsi<30" -> {"rsi_14": ("<", 30)}
            "rsi>70 and pe<15" -> {"rsi_14": (">", 70), "pe_ratio": ("<", 15)}
            "macd_bullish" -> {"macd_above_signal": True}
        """
        criteria = {}

        # Normalize input
        criteria_str = criteria_str.lower().strip()

        # Handle preset names
        if criteria_str in [p.value for p in ScreenPreset]:
            return self.PRESETS[ScreenPreset(criteria_str)]["criteria"]

        # Handle special keywords
        if "bullish" in criteria_str or "naik" in criteria_str:
            criteria["macd_above_signal"] = True
            criteria["price_above_sma20"] = True

        if "bearish" in criteria_str or "turun" in criteria_str:
            criteria["macd_below_signal"] = True
            criteria["price_below_sma20"] = True

        if "oversold" in criteria_str:
            criteria["rsi_14"] = ("<", 30)

        if "overbought" in criteria_str:
            criteria["rsi_14"] = (">", 70)

        if "squeeze" in criteria_str:
            criteria["bb_squeeze"] = True

        if "breakout" in criteria_str:
            criteria["near_resistance"] = True
            criteria["volume_spike"] = True

        if "volume" in criteria_str and "spike" in criteria_str:
            criteria["volume_spike"] = True

        # Parse numeric criteria: rsi<30, pe>15, etc
        # Map common names to field names
        field_map = {
            "rsi": "rsi_14",
            "pe": "pe_ratio",
            "pb": "pb_ratio",
            "pbv": "pb_ratio",
            "roe": "roe",
            "macd": "macd",
            "volume": "volume",
            "price": "price",
            "change": "change_percent",
        }

        pattern = r"(\w+)\s*([<>]=?)\s*(\d+\.?\d*)"
        matches = re.findall(pattern, criteria_str)

        for indicator, operator, value in matches:
            field_name = field_map.get(indicator, indicator)
            criteria[field_name] = (operator, float(value))

        return criteria

    async def screen_preset(
        self,
        preset: ScreenPreset,
        limit: int = 20,
    ) -> list[ScreenResult]:
        """Screen stocks using a preset."""
        preset_config = self.PRESETS.get(preset)
        if not preset_config:
            return []

        log.info(f"Screening with preset: {preset.value}")
        return await self._run_screen(
            criteria=preset_config["criteria"],
            sort_by=preset_config.get("sort_by", "score"),
            sort_asc=preset_config.get("sort_asc", False),
            limit=limit,
        )

    async def screen_criteria(
        self,
        criteria_str: str,
        limit: int = 20,
    ) -> list[ScreenResult]:
        """Screen stocks using flexible criteria string."""
        criteria = self.parse_criteria(criteria_str)
        if not criteria:
            return []

        log.info(f"Screening with criteria: {criteria}")
        return await self._run_screen(
            criteria=criteria,
            sort_by="score",
            sort_asc=False,
            limit=limit,
        )

    async def smart_screen(
        self,
        query: str,
        limit: int = 10,
    ) -> tuple[list[ScreenResult], str]:
        """
        AI-driven smart screening based on natural language query.

        Returns:
            Tuple of (results, explanation of criteria used)
        """
        query_lower = query.lower()

        # Check specific patterns FIRST (before generic ones like "bagus")

        # Multibagger: small/mid cap, momentum, growth
        if any(
            w in query_lower
            for w in ["multibagger", "multi bagger", "10x", "100x", "cuan besar", "untung besar"]
        ):
            criteria = {
                "market_cap_small_mid": True,
                "macd_above_signal": True,
                "volume_above_avg": True,
            }
            explanation = "Mencari saham potensi multibagger (small/mid cap, momentum bullish, volume aktif). Kriteria: bukan big cap, MACD bullish, volume di atas rata-rata."

        # Small cap
        elif any(w in query_lower for w in ["small cap", "saham kecil", "kapitalisasi kecil"]):
            criteria = {
                "market_cap_small": True,
                "macd_above_signal": True,
            }
            explanation = "Mencari saham small cap dengan momentum bullish"

        # Growth stocks
        elif any(w in query_lower for w in ["growth", "pertumbuhan", "tumbuh"]):
            criteria = {
                "high_growth": True,
                "macd_above_signal": True,
            }
            explanation = (
                "Mencari saham dengan pertumbuhan tinggi (earnings/revenue growth > 15-20%)"
            )

        # Breakout
        elif any(w in query_lower for w in ["breakout", "tembus"]):
            criteria = {
                "near_resistance": True,
                "volume_spike": True,
            }
            explanation = "Mencari saham potensi breakout (dekat resistance, volume spike)"

        # Oversold
        elif any(w in query_lower for w in ["oversold", "jenuh jual"]):
            criteria = {"rsi_14": ("<", 30)}
            explanation = "Mencari saham oversold (RSI < 30)"

        # Undervalued
        elif any(w in query_lower for w in ["murah", "undervalued", "diskon"]):
            criteria = {
                "pe_ratio": ("<", 15),
                "roe": (">", 10),
            }
            explanation = "Mencari saham undervalued (PE < 15, ROE > 10%)"

        # Bearish
        elif any(w in query_lower for w in ["turun", "bearish", "jual", "hindari"]):
            criteria = {
                "rsi_14": (">", 70),
                "macd_below_signal": True,
            }
            explanation = "Mencari saham dengan sinyal bearish (RSI > 70, MACD bearish)"

        # Bullish momentum (generic - check last)
        elif any(w in query_lower for w in ["naik", "bullish", "bagus", "potensial", "beli"]):
            criteria = {
                "rsi_14": ("between", (30, 65)),
                "macd_above_signal": True,
                "volume_above_avg": True,
            }
            explanation = "Mencari saham dengan momentum bullish (RSI 30-65, MACD bullish, volume di atas rata-rata)"

        else:
            # Default: momentum screening
            criteria = {
                "macd_above_signal": True,
                "volume_above_avg": True,
            }
            explanation = "Screening momentum (MACD bullish, volume di atas rata-rata)"

        results = await self._run_screen(
            criteria=criteria,
            sort_by="score",
            sort_asc=False,
            limit=limit,
        )

        return results, explanation

    async def _run_screen(
        self,
        criteria: dict[str, Any],
        sort_by: str = "score",
        sort_asc: bool = False,
        limit: int = 20,
    ) -> list[ScreenResult]:
        """Run screening with given criteria."""
        results = []

        # Fetch data for all stocks in parallel (with semaphore to limit concurrency)
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

        async def fetch_with_limit(ticker: str) -> ScreenResult | None:
            async with semaphore:
                return await self._fetch_stock_data(ticker)

        log.info(f"Screening {len(self.universe)} stocks...")

        tasks = [fetch_with_limit(ticker) for ticker in self.universe]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter and score results
        for result in all_results:
            if isinstance(result, Exception) or result is None:
                continue

            matches, signals = self._matches_criteria(result, criteria)
            if matches:
                result.score = self._calculate_score(result)
                result.signals = signals
                results.append(result)

        # Sort results
        if sort_by == "score":
            results.sort(key=lambda x: x.score, reverse=not sort_asc)
        elif hasattr(results[0] if results else ScreenResult, sort_by):
            results.sort(key=lambda x: getattr(x, sort_by) or 0, reverse=not sort_asc)

        log.info(f"Found {len(results)} stocks matching criteria")

        return results[:limit]

    def format_results(
        self,
        results: list[ScreenResult],
        title: str = "Screening Results",
        show_details: bool = True,
    ) -> str:
        """Format screening results as text."""
        if not results:
            return "No stocks found matching criteria."

        lines = [
            title,
            f"Found {len(results)} stocks",
            "",
        ]

        if show_details:
            for i, r in enumerate(results, 1):
                rsi_str = f"{r.rsi_14:.1f}" if r.rsi_14 else "N/A"
                macd_str = r.macd_status

                lines.append(f"{i}. {r.ticker} - {r.name or 'N/A'}")
                lines.append(f"   Price: NT$ {r.price:,.0f} ({r.change_percent:+.2f}%)")
                lines.append(f"   RSI: {rsi_str} ({r.rsi_status}) | MACD: {macd_str}")

                if r.support and r.resistance:
                    lines.append(f"   Support: {r.support:,.0f} | Resistance: {r.resistance:,.0f}")

                if r.signals:
                    lines.append(f"   Signals: {', '.join(r.signals)}")

                lines.append(f"   Score: {r.score:.0f}/100")
                lines.append("")
        else:
            # Simple table format
            lines.append(
                f"{'No':<3} {'Ticker':<8} {'Price':>10} {'Change':>8} {'RSI':>6} {'Score':>6}"
            )
            lines.append("-" * 45)

            for i, r in enumerate(results, 1):
                rsi_str = f"{r.rsi_14:.1f}" if r.rsi_14 else "N/A"
                lines.append(
                    f"{i:<3} {r.ticker:<8} {r.price:>10,.0f} {r.change_percent:>+7.2f}% {rsi_str:>6} {r.score:>6.0f}"
                )

        return "\n".join(lines)
