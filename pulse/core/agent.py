"""Smart agent for autonomous stock analysis."""

import re
from dataclasses import dataclass
from typing import Any

from pulse.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class AgentAction:
    """Represents an action the agent should take."""

    tool: str
    params: dict[str, Any]
    reason: str


@dataclass
class AgentResult:
    """Result from agent execution."""

    success: bool
    message: str
    data: dict[str, Any] | None = None
    chart: str | None = None


class StockAgent:
    """
    Smart agent that can autonomously analyze stocks.

    Capabilities:
    - Parse user intent
    - Fetch stock data
    - Run technical/fundamental analysis
    - Generate charts
    - Create forecasts
    - Provide actionable insights
    """

    # Intent patterns
    INTENT_PATTERNS = {
        "analyze": [
            r"分析\s*(\d{4})",
            r"analis[ai]s?\s+(\w+)",
            r"查看\s*(\d{4})",
            r"看看\s*(\d{4})",
        ],
        "chart": [
            r"圖表\s*(\d{4})",
            r"chart\s+(\w+)",
            r"graph\s+(\w+)",
        ],
        "forecast": [
            r"預測\s*(\d{4})",
            r"forecast\s+(\w+)",
            r"target\s+(\w+)",
        ],
        "technical": [
            r"技術\s*(\d{4})",
            r"ta\s+(\w+)",
            r"rsi\s+(\w+)",
            r"macd\s+(\w+)",
        ],
        "broker": [
            r"broker\s+(\w+)",
            r"法人\s+(\w+)",
            r"flow\s+(\w+)",
            r"外資\s+(\w+)",
        ],
        "compare": [
            r"比較\s*(\d{4})\s*(?:和|與|跟)\s*(\d{4})",
            r"(\w+)\s+vs\s+(\w+)",
        ],
    }

    # Known tickers for validation (Taiwan stocks)
    KNOWN_TICKERS = [
        "2330",
        "2454",
        "2317",
        "2881",
        "2882",  # Top stocks
        "2303",
        "3711",
        "2379",
        "3034",
        "2408",  # Semiconductor
        "2382",
        "2357",
        "3231",
        "2324",
        "2356",  # Electronics
        "2891",
        "2886",
        "2884",
        "2892",
        "2880",  # Finance
        "2002",
        "2006",
        "2014",
        "2027",  # Steel
        "1301",
        "1303",
        "1326",
        "6505",  # Plastic
        "4736",
        "4743",
        "4746",
        "6446",  # Biotech
        "2412",
        "3045",
        "4904",  # Telecom
        "1216",
        "1227",
        "1229",  # Food
        "2603",
        "2609",
        "2615",  # Shipping
    ]

    def __init__(self):
        self._tools = self._register_tools()

    def _register_tools(self) -> dict[str, callable]:
        """Register available tools."""
        return {
            "fetch_stock": self._tool_fetch_stock,
            "technical_analysis": self._tool_technical,
            "fundamental_analysis": self._tool_fundamental,
            "broker_flow": self._tool_broker_flow,
            "chart": self._tool_chart,
            "forecast": self._tool_forecast,
            "compare": self._tool_compare,
        }

    def parse_intent(self, message: str) -> AgentAction | None:
        """
        Parse user message to determine intent.

        Args:
            message: User input message

        Returns:
            AgentAction or None
        """
        message_lower = message.lower().strip()

        # Check each intent pattern
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    ticker = match.group(1).upper()

                    # Validate ticker
                    if not self._is_valid_ticker(ticker):
                        continue

                    # Handle compare (needs 2 tickers)
                    if intent == "compare" and len(match.groups()) >= 2:
                        ticker2 = match.group(2).upper()
                        return AgentAction(
                            tool="compare",
                            params={"tickers": [ticker, ticker2]},
                            reason=f"比較 {ticker} vs {ticker2}",
                        )

                    return AgentAction(
                        tool=self._intent_to_tool(intent),
                        params={"ticker": ticker},
                        reason=f"{intent.capitalize()} {ticker}",
                    )

        # Check for standalone ticker mention
        for ticker in self.KNOWN_TICKERS:
            if ticker.lower() in message_lower:
                return AgentAction(
                    tool="fetch_stock", params={"ticker": ticker}, reason=f"股票資訊 {ticker}"
                )

        return None

    def _intent_to_tool(self, intent: str) -> str:
        """Map intent to tool name."""
        mapping = {
            "analyze": "technical_analysis",
            "chart": "chart",
            "forecast": "forecast",
            "technical": "technical_analysis",
            "broker": "broker_flow",
            "compare": "compare",
        }
        return mapping.get(intent, "fetch_stock")

    def _is_valid_ticker(self, ticker: str) -> bool:
        """Check if ticker is valid (Taiwan 4-6 digit codes)."""
        # Known tickers
        if ticker in self.KNOWN_TICKERS:
            return True
        # Pattern: 4-6 digits
        if re.match(r"^\d{4,6}$", ticker):
            return True
        return False

    async def execute(self, action: AgentAction) -> AgentResult:
        """
        Execute an agent action.

        Args:
            action: The action to execute

        Returns:
            AgentResult
        """
        tool_fn = self._tools.get(action.tool)
        if not tool_fn:
            return AgentResult(success=False, message=f"找不到工具: {action.tool}")

        try:
            return await tool_fn(**action.params)
        except Exception as e:
            log.error(f"Agent execution failed: {e}")
            return AgentResult(success=False, message=f"Error: {str(e)}")

    async def run(self, message: str) -> AgentResult | None:
        """
        Run agent on user message.

        Args:
            message: User input

        Returns:
            AgentResult or None if no action detected
        """
        action = self.parse_intent(message)
        if action:
            log.info(f"Agent action: {action.tool} - {action.reason}")
            return await self.execute(action)
        return None

    # Tool implementations
    async def _tool_fetch_stock(self, ticker: str) -> AgentResult:
        """Fetch basic stock info."""
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        stock = await fetcher.fetch_stock(ticker)

        if not stock:
            return AgentResult(success=False, message=f"無法取得 {ticker} 的資料")

        change_symbol = "+" if stock.change >= 0 else ""
        message = f"""{stock.ticker} - {stock.name}
股價: {stock.current_price:,.2f}
漲跌: {change_symbol}{stock.change:,.2f} ({change_symbol}{stock.change_percent:.2f}%)
成交量: {stock.volume:,.0f}"""

        return AgentResult(success=True, message=message, data={"stock": stock.__dict__})

    async def _tool_technical(self, ticker: str) -> AgentResult:
        """Run technical analysis."""
        from pulse.core.analysis.technical import TechnicalAnalyzer
        from pulse.core.charts import generate_sparkline
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        stock = await fetcher.fetch_stock(ticker)

        if not stock:
            return AgentResult(success=False, message=f"{ticker} 的資料不可用")

        analyzer = TechnicalAnalyzer()
        indicators = await analyzer.analyze(ticker)

        if not indicators:
            return AgentResult(success=False, message=f"{ticker} 的分析失敗")

        summary = analyzer.get_indicator_summary(indicators)

        # Build message
        lines = [f"技術分析: {ticker}", ""]
        for item in summary:
            status = f" ({item.get('status', '')})" if item.get("status") else ""
            lines.append(f"{item['name']}: {item['value']}{status}")

        # Add sparkline if we have price data
        if hasattr(stock, "history") and stock.history:
            prices = [h.close for h in stock.history[-20:]]
            sparkline = generate_sparkline(prices)
            lines.append(f"\nTrend: {sparkline}")

        return AgentResult(
            success=True,
            message="\n".join(lines),
            data={"indicators": indicators.__dict__ if indicators else None},
        )

    async def _tool_fundamental(self, ticker: str) -> AgentResult:
        """Run fundamental analysis."""
        from pulse.core.analysis.fundamental import FundamentalAnalyzer

        analyzer = FundamentalAnalyzer()
        data = await analyzer.analyze(ticker)

        if not data:
            return AgentResult(
                success=False, message=f"{ticker} 的基本面資料不可用"
            )

        summary = analyzer.get_summary(data)
        score_data = analyzer.score_valuation(data)

        lines = [f"基本面分析: {ticker}", f"評分: {score_data['score']}/100", ""]

        current_cat = ""
        for item in summary:
            if item["category"] != current_cat:
                current_cat = item["category"]
                lines.append(f"\n{current_cat}")
            status = f" ({item.get('status', '')})" if item.get("status") else ""
            lines.append(f"  {item['name']}: {item['value']}{status}")

        return AgentResult(success=True, message="\n".join(lines), data={"fundamental": data})

    async def _tool_broker_flow(self, ticker: str) -> AgentResult:
        """Get broker flow analysis."""
        from pulse.core.analysis.institutional_flow import InstitutionalFlowAnalyzer

        analyzer = InstitutionalFlowAnalyzer()

        result = await analyzer.analyze(ticker)

        if not result:
            return AgentResult(success=False, message=f"無法取得 {ticker} 的法人資料")

        return AgentResult(
            success=True,
            message=analyzer.format_summary_table(result),
            data={"broker_flow": result},
        )

    async def _tool_chart(self, ticker: str) -> AgentResult:
        """Generate price chart."""
        from pulse.core.charts import TerminalChart
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        df = await fetcher.fetch_history(ticker, period="3mo")

        if df is None or df.empty:
            return AgentResult(
                success=False, message=f"{ticker} 的歷史資料不可用"
            )

        chart = TerminalChart(width=60, height=15)

        dates = df.index.strftime("%Y-%m-%d").tolist()
        prices = df["Close"].tolist()

        chart_str = chart.price_chart(dates, prices, title=f"{ticker} - 3 個月")

        return AgentResult(success=True, message=f"{ticker} 圖表:", chart=chart_str)

    async def _tool_forecast(self, ticker: str) -> AgentResult:
        """Generate price forecast."""
        from pulse.core.charts import TerminalChart
        from pulse.core.data.yfinance import YFinanceFetcher
        from pulse.core.forecasting import PriceForecaster

        fetcher = YFinanceFetcher()
        df = await fetcher.fetch_history(ticker, period="6mo")

        if df is None or df.empty:
            return AgentResult(success=False, message=f"{ticker} 的預測資料不足")

        prices = df["Close"].tolist()
        dates = df.index.strftime("%Y-%m-%d").tolist()

        forecaster = PriceForecaster()
        result = await forecaster.forecast(ticker, prices, dates, days=7)

        if not result:
            return AgentResult(success=False, message=f"{ticker} 的預測失敗")

        # Generate forecast chart
        chart = TerminalChart(width=60, height=15)
        chart_str = chart.forecast_chart(
            historical=prices[-30:],
            forecast=result.predictions,
            lower_bound=result.lower_bound,
            upper_bound=result.upper_bound,
            title=f"{ticker} - 7 日預測",
        )

        message = forecaster.format_forecast(result)

        return AgentResult(
            success=True, message=message, chart=chart_str, data={"forecast": result.__dict__}
        )

    async def _tool_compare(self, tickers: list[str]) -> AgentResult:
        """Compare multiple stocks."""
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()

        results = []
        for ticker in tickers:
            stock = await fetcher.fetch_stock(ticker)
            if stock:
                results.append(
                    {
                        "ticker": stock.ticker,
                        "name": stock.name,
                        "price": stock.current_price,
                        "change": stock.change_percent,
                    }
                )

        if len(results) < 2:
            return AgentResult(success=False, message="資料不足無法比較")

        # Build comparison table
        lines = ["股票比較:", ""]
        lines.append(f"{'代碼':<8} {'股價':>12} {'漲跌':>10}")
        lines.append("-" * 32)

        for r in results:
            change_str = f"{r['change']:+.2f}%"
            lines.append(f"{r['ticker']:<8} {r['price']:>12,.0f} {change_str:>10}")

        return AgentResult(success=True, message="\n".join(lines), data={"comparison": results})
