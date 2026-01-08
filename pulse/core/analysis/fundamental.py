"""Fundamental analysis engine."""

from typing import Any

from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.models import FundamentalData, SignalType
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class FundamentalAnalyzer:
    """Fundamental analysis engine."""

    def __init__(self):
        """Initialize fundamental analyzer."""
        self.fetcher = YFinanceFetcher()

    async def analyze(self, ticker: str) -> FundamentalData | None:
        """
        Perform fundamental analysis on a stock.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            FundamentalData object or None
        """
        return await self.fetcher.fetch_fundamentals(ticker)

    def score_valuation(self, data: FundamentalData) -> dict[str, Any]:
        """
        Score stock valuation based on fundamental metrics.
        
        Args:
            data: FundamentalData object
            
        Returns:
            Valuation score and breakdown
        """
        scores = []
        max_score = 0

        # P/E Ratio scoring
        if data.pe_ratio is not None:
            max_score += 20
            if data.pe_ratio < 0:
                scores.append(0)  # Negative earnings
            elif data.pe_ratio < 10:
                scores.append(20)  # Very undervalued
            elif data.pe_ratio < 15:
                scores.append(15)  # Undervalued
            elif data.pe_ratio < 25:
                scores.append(10)  # Fair
            elif data.pe_ratio < 40:
                scores.append(5)   # Overvalued
            else:
                scores.append(0)   # Very overvalued

        # P/B Ratio scoring
        if data.pb_ratio is not None:
            max_score += 15
            if data.pb_ratio < 1:
                scores.append(15)  # Trading below book value
            elif data.pb_ratio < 2:
                scores.append(12)
            elif data.pb_ratio < 3:
                scores.append(8)
            elif data.pb_ratio < 5:
                scores.append(4)
            else:
                scores.append(0)

        # ROE scoring
        if data.roe is not None:
            max_score += 20
            if data.roe > 20:
                scores.append(20)  # Excellent
            elif data.roe > 15:
                scores.append(15)  # Good
            elif data.roe > 10:
                scores.append(10)  # Average
            elif data.roe > 5:
                scores.append(5)   # Below average
            else:
                scores.append(0)   # Poor

        # ROA scoring
        if data.roa is not None:
            max_score += 15
            if data.roa > 10:
                scores.append(15)
            elif data.roa > 5:
                scores.append(10)
            elif data.roa > 2:
                scores.append(5)
            else:
                scores.append(0)

        # Debt/Equity scoring
        if data.debt_to_equity is not None:
            max_score += 15
            if data.debt_to_equity < 0.5:
                scores.append(15)  # Very low debt
            elif data.debt_to_equity < 1:
                scores.append(12)
            elif data.debt_to_equity < 2:
                scores.append(8)
            elif data.debt_to_equity < 3:
                scores.append(4)
            else:
                scores.append(0)   # High debt

        # Dividend Yield scoring
        if data.dividend_yield is not None:
            max_score += 15
            if data.dividend_yield > 5:
                scores.append(15)  # High yield
            elif data.dividend_yield > 3:
                scores.append(12)
            elif data.dividend_yield > 1:
                scores.append(8)
            elif data.dividend_yield > 0:
                scores.append(4)
            else:
                scores.append(0)

        total_score = sum(scores)
        normalized_score = (total_score / max_score * 100) if max_score > 0 else 0

        return {
            "score": round(normalized_score, 1),
            "max_score": 100,
            "breakdown": {
                "pe_score": scores[0] if len(scores) > 0 else None,
                "pb_score": scores[1] if len(scores) > 1 else None,
                "roe_score": scores[2] if len(scores) > 2 else None,
                "roa_score": scores[3] if len(scores) > 3 else None,
                "debt_score": scores[4] if len(scores) > 4 else None,
                "dividend_score": scores[5] if len(scores) > 5 else None,
            }
        }

    def get_valuation_signal(self, score: float) -> SignalType:
        """
        Get trading signal based on valuation score.
        
        Args:
            score: Valuation score (0-100)
            
        Returns:
            SignalType
        """
        if score >= 80:
            return SignalType.STRONG_BUY
        elif score >= 65:
            return SignalType.BUY
        elif score >= 40:
            return SignalType.NEUTRAL
        elif score >= 25:
            return SignalType.SELL
        else:
            return SignalType.STRONG_SELL

    def compare_peers(
        self,
        fundamentals: list[FundamentalData],
    ) -> list[dict[str, Any]]:
        """
        Compare fundamental metrics across peer stocks.
        
        Args:
            fundamentals: List of FundamentalData for peer stocks
            
        Returns:
            Comparison data sorted by score
        """
        results = []

        for data in fundamentals:
            score_data = self.score_valuation(data)

            results.append({
                "ticker": data.ticker,
                "pe_ratio": data.pe_ratio,
                "pb_ratio": data.pb_ratio,
                "roe": data.roe,
                "debt_to_equity": data.debt_to_equity,
                "dividend_yield": data.dividend_yield,
                "market_cap": data.market_cap,
                "score": score_data["score"],
                "signal": self.get_valuation_signal(score_data["score"]).value,
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        return results

    def get_summary(self, data: FundamentalData) -> list[dict[str, Any]]:
        """
        Generate human-readable fundamental summary.
        
        Args:
            data: FundamentalData object
            
        Returns:
            List of metric summaries
        """
        summary = []

        # Valuation metrics
        if data.pe_ratio is not None:
            status = "Cheap" if data.pe_ratio < 15 else "Expensive" if data.pe_ratio > 30 else "Fair"
            summary.append({
                "category": "Valuation",
                "name": "P/E Ratio",
                "value": f"{data.pe_ratio:.2f}",
                "status": status,
            })

        if data.pb_ratio is not None:
            status = "Undervalued" if data.pb_ratio < 1 else "Overvalued" if data.pb_ratio > 3 else "Fair"
            summary.append({
                "category": "Valuation",
                "name": "P/B Ratio",
                "value": f"{data.pb_ratio:.2f}",
                "status": status,
            })

        # Profitability metrics
        if data.roe is not None:
            status = "Excellent" if data.roe > 20 else "Good" if data.roe > 15 else "Average" if data.roe > 10 else "Poor"
            summary.append({
                "category": "Profitability",
                "name": "ROE",
                "value": f"{data.roe:.2f}%",
                "status": status,
            })

        if data.roa is not None:
            status = "Good" if data.roa > 10 else "Average" if data.roa > 5 else "Poor"
            summary.append({
                "category": "Profitability",
                "name": "ROA",
                "value": f"{data.roa:.2f}%",
                "status": status,
            })

        if data.npm is not None:
            summary.append({
                "category": "Profitability",
                "name": "Net Profit Margin",
                "value": f"{data.npm:.2f}%",
                "status": "",
            })

        # Financial Health
        if data.debt_to_equity is not None:
            status = "Low Risk" if data.debt_to_equity < 1 else "Moderate" if data.debt_to_equity < 2 else "High Risk"
            summary.append({
                "category": "Financial Health",
                "name": "Debt/Equity",
                "value": f"{data.debt_to_equity:.2f}",
                "status": status,
            })

        if data.current_ratio is not None:
            status = "Healthy" if data.current_ratio > 1.5 else "Adequate" if data.current_ratio > 1 else "Concerning"
            summary.append({
                "category": "Financial Health",
                "name": "Current Ratio",
                "value": f"{data.current_ratio:.2f}",
                "status": status,
            })

        # Dividend
        if data.dividend_yield is not None and data.dividend_yield > 0:
            status = "High" if data.dividend_yield > 5 else "Moderate" if data.dividend_yield > 2 else "Low"
            summary.append({
                "category": "Dividend",
                "name": "Dividend Yield",
                "value": f"{data.dividend_yield:.2f}%",
                "status": status,
            })

        # Growth
        if data.earnings_growth is not None:
            status = "Strong" if data.earnings_growth > 20 else "Moderate" if data.earnings_growth > 10 else "Weak" if data.earnings_growth > 0 else "Declining"
            summary.append({
                "category": "Growth",
                "name": "Earnings Growth",
                "value": f"{data.earnings_growth:.2f}%",
                "status": status,
            })

        return summary
