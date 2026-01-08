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
            r"analis[ai]s?\s+(\w+)",
            r"cek\s+(\w+)",
            r"gimana\s+(\w+)",
            r"bagaimana\s+(\w+)",
            r"lihat\s+(\w+)",
        ],
        "chart": [
            r"chart\s+(\w+)",
            r"grafik\s+(\w+)",
            r"graph\s+(\w+)",
        ],
        "forecast": [
            r"prediksi\s+(\w+)",
            r"forecast\s+(\w+)",
            r"ramal\w*\s+(\w+)",
            r"target\s+(\w+)",
        ],
        "technical": [
            r"teknikal\s+(\w+)",
            r"ta\s+(\w+)",
            r"rsi\s+(\w+)",
            r"macd\s+(\w+)",
        ],
        "broker": [
            r"broker\s+(\w+)",
            r"bandar\s+(\w+)",
            r"flow\s+(\w+)",
            r"asing\s+(\w+)",
        ],
        "compare": [
            r"bandingi?n?g?\s+(\w+)\s+(?:dan|vs|dengan)\s+(\w+)",
            r"(\w+)\s+vs\s+(\w+)",
        ],
    }

    # Known tickers for validation
    KNOWN_TICKERS = [
        "BBCA", "BBRI", "BMRI", "BBNI", "BRIS",  # Banks
        "TLKM", "EXCL", "ISAT", "FREN",  # Telco
        "ASII", "UNTR", "ASTRA",  # Automotive
        "UNVR", "ICBP", "INDF", "MYOR",  # Consumer
        "ANTM", "INCO", "PTBA", "ADRO", "ITMG",  # Mining
        "PGAS", "AKRA", "MEDC",  # Energy
        "GOTO", "BUKA", "EMTK",  # Tech
        "ACES", "MAPI", "ERAA",  # Retail
        "SMGR", "INTP", "WIKA", "WSKT",  # Infrastructure
        "KLBF", "SIDO", "KAEF",  # Pharma
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
                            reason=f"Membandingkan {ticker} vs {ticker2}"
                        )

                    return AgentAction(
                        tool=self._intent_to_tool(intent),
                        params={"ticker": ticker},
                        reason=f"{intent.capitalize()} {ticker}"
                    )

        # Check for standalone ticker mention
        for ticker in self.KNOWN_TICKERS:
            if ticker.lower() in message_lower:
                return AgentAction(
                    tool="fetch_stock",
                    params={"ticker": ticker},
                    reason=f"Info saham {ticker}"
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
        """Check if ticker is valid."""
        # Known tickers
        if ticker in self.KNOWN_TICKERS:
            return True
        # Pattern: 4 uppercase letters
        if re.match(r'^[A-Z]{4}$', ticker):
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
            return AgentResult(
                success=False,
                message=f"Tool tidak ditemukan: {action.tool}"
            )

        try:
            return await tool_fn(**action.params)
        except Exception as e:
            log.error(f"Agent execution failed: {e}")
            return AgentResult(
                success=False,
                message=f"Error: {str(e)}"
            )

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
            return AgentResult(
                success=False,
                message=f"Tidak dapat mengambil data {ticker}"
            )

        change_symbol = "+" if stock.change >= 0 else ""
        message = f"""{stock.ticker} - {stock.name}
Harga: {stock.current_price:,.0f}
Change: {change_symbol}{stock.change:,.0f} ({change_symbol}{stock.change_percent:.2f}%)
Volume: {stock.volume:,.0f}"""

        return AgentResult(
            success=True,
            message=message,
            data={"stock": stock.__dict__}
        )

    async def _tool_technical(self, ticker: str) -> AgentResult:
        """Run technical analysis."""
        from pulse.core.analysis.technical import TechnicalAnalyzer
        from pulse.core.charts import generate_sparkline
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        stock = await fetcher.fetch_stock(ticker)

        if not stock:
            return AgentResult(success=False, message=f"Data tidak tersedia untuk {ticker}")

        analyzer = TechnicalAnalyzer()
        indicators = await analyzer.analyze(ticker)

        if not indicators:
            return AgentResult(success=False, message=f"Analisis gagal untuk {ticker}")

        summary = analyzer.get_indicator_summary(indicators)

        # Build message
        lines = [f"Teknikal: {ticker}", ""]
        for item in summary:
            status = f" ({item.get('status', '')})" if item.get('status') else ""
            lines.append(f"{item['name']}: {item['value']}{status}")

        # Add sparkline if we have price data
        if hasattr(stock, 'history') and stock.history:
            prices = [h.close for h in stock.history[-20:]]
            sparkline = generate_sparkline(prices)
            lines.append(f"\nTrend: {sparkline}")

        return AgentResult(
            success=True,
            message="\n".join(lines),
            data={"indicators": indicators.__dict__ if indicators else None}
        )

    async def _tool_fundamental(self, ticker: str) -> AgentResult:
        """Run fundamental analysis."""
        from pulse.core.analysis.fundamental import FundamentalAnalyzer

        analyzer = FundamentalAnalyzer()
        data = await analyzer.analyze(ticker)

        if not data:
            return AgentResult(success=False, message=f"Data fundamental tidak tersedia untuk {ticker}")

        summary = analyzer.get_summary(data)
        score_data = analyzer.score_valuation(data)

        lines = [f"Fundamental: {ticker}", f"Score: {score_data['score']}/100", ""]

        current_cat = ""
        for item in summary:
            if item['category'] != current_cat:
                current_cat = item['category']
                lines.append(f"\n{current_cat}")
            status = f" ({item.get('status', '')})" if item.get('status') else ""
            lines.append(f"  {item['name']}: {item['value']}{status}")

        return AgentResult(
            success=True,
            message="\n".join(lines),
            data={"fundamental": data}
        )

    async def _tool_broker_flow(self, ticker: str) -> AgentResult:
        """Get broker flow analysis."""
        from pulse.core.analysis.broker_flow import BrokerFlowAnalyzer

        analyzer = BrokerFlowAnalyzer()

        if not analyzer.client.is_authenticated:
            return AgentResult(
                success=False,
                message="Stockbit belum terautentikasi. Jalankan /auth dulu."
            )

        result = await analyzer.analyze(ticker)

        if not result:
            return AgentResult(success=False, message=f"Data broker tidak tersedia untuk {ticker}")

        return AgentResult(
            success=True,
            message=analyzer.format_summary_table(result),
            data={"broker_flow": result}
        )

    async def _tool_chart(self, ticker: str) -> AgentResult:
        """Generate price chart."""
        from pulse.core.charts import TerminalChart
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        df = await fetcher.fetch_history(ticker, period="3mo")

        if df is None or df.empty:
            return AgentResult(success=False, message=f"Data historis tidak tersedia untuk {ticker}")

        chart = TerminalChart(width=60, height=15)

        dates = df.index.strftime('%Y-%m-%d').tolist()
        prices = df['Close'].tolist()

        chart_str = chart.price_chart(dates, prices, title=f"{ticker} - 3 Bulan")

        return AgentResult(
            success=True,
            message=f"Chart {ticker}:",
            chart=chart_str
        )

    async def _tool_forecast(self, ticker: str) -> AgentResult:
        """Generate price forecast."""
        from pulse.core.charts import TerminalChart
        from pulse.core.data.yfinance import YFinanceFetcher
        from pulse.core.forecasting import PriceForecaster

        fetcher = YFinanceFetcher()
        df = await fetcher.fetch_history(ticker, period="6mo")

        if df is None or df.empty:
            return AgentResult(success=False, message=f"Data tidak cukup untuk forecast {ticker}")

        prices = df['Close'].tolist()
        dates = df.index.strftime('%Y-%m-%d').tolist()

        forecaster = PriceForecaster()
        result = await forecaster.forecast(ticker, prices, dates, days=7)

        if not result:
            return AgentResult(success=False, message=f"Forecast gagal untuk {ticker}")

        # Generate forecast chart
        chart = TerminalChart(width=60, height=15)
        chart_str = chart.forecast_chart(
            historical=prices[-30:],
            forecast=result.predictions,
            lower_bound=result.lower_bound,
            upper_bound=result.upper_bound,
            title=f"{ticker} - Forecast 7 Hari"
        )

        message = forecaster.format_forecast(result)

        return AgentResult(
            success=True,
            message=message,
            chart=chart_str,
            data={"forecast": result.__dict__}
        )

    async def _tool_compare(self, tickers: list[str]) -> AgentResult:
        """Compare multiple stocks."""
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()

        results = []
        for ticker in tickers:
            stock = await fetcher.fetch_stock(ticker)
            if stock:
                results.append({
                    "ticker": stock.ticker,
                    "name": stock.name,
                    "price": stock.current_price,
                    "change": stock.change_percent,
                })

        if len(results) < 2:
            return AgentResult(success=False, message="Tidak cukup data untuk perbandingan")

        # Build comparison table
        lines = ["Perbandingan:", ""]
        lines.append(f"{'Ticker':<8} {'Harga':>12} {'Change':>10}")
        lines.append("-" * 32)

        for r in results:
            change_str = f"{r['change']:+.2f}%"
            lines.append(f"{r['ticker']:<8} {r['price']:>12,.0f} {change_str:>10}")

        return AgentResult(
            success=True,
            message="\n".join(lines),
            data={"comparison": results}
        )
