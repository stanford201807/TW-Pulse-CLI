"""Command registry and handler."""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pulse.cli.app import PulseApp

from pulse.utils.logger import get_logger

log = get_logger(__name__)


class Command:
    """Represents a slash command."""

    def __init__(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        usage: str = "",
        aliases: list[str] | None = None,
    ):
        self.name = name
        self.handler = handler
        self.description = description
        self.usage = usage or f"/{name}"
        self.aliases = aliases or []


class CommandRegistry:
    """Registry for slash commands."""

    def __init__(self, app: "PulseApp"):
        self.app = app
        self._commands: dict[str, Command] = {}
        self._register_builtin_commands()

    def register(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        usage: str = "",
        aliases: list[str] | None = None,
    ) -> None:
        """Register a command."""
        cmd = Command(name, handler, description, usage, aliases)
        self._commands[name.lower()] = cmd

        for alias in aliases or []:
            self._commands[alias.lower()] = cmd

    def get(self, name: str) -> Command | None:
        """Get a command by name."""
        return self._commands.get(name.lower())

    def list_commands(self) -> list[Command]:
        """List all unique commands (excluding aliases)."""
        seen = set()
        commands = []

        for cmd in self._commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                commands.append(cmd)

        return sorted(commands, key=lambda c: c.name)

    async def execute(self, command_str: str) -> str | None:
        """Execute a command string."""
        parts = command_str.strip().split(maxsplit=1)
        cmd_name = parts[0].lstrip("/").lower()
        args = parts[1] if len(parts) > 1 else ""

        cmd = self.get(cmd_name)

        if not cmd:
            return f"Unknown command: /{cmd_name}. Type /help for available commands."

        try:
            result = await cmd.handler(args)
            return result
        except Exception as e:
            log.error(f"Command {cmd_name} failed: {e}")
            raise

    def _register_builtin_commands(self) -> None:
        """Register built-in commands."""

        self.register(
            "help",
            self._cmd_help,
            "Show available commands",
            "/help [command]",
            aliases=["h", "?"],
        )

        self.register(
            "models",
            self._cmd_models,
            "List or switch AI models",
            "/models [model_id]",
            aliases=["model", "m"],
        )

        self.register(
            "analyze",
            self._cmd_analyze,
            "Analyze a stock (分析股票)",
            "/analyze <TICKER>",
            aliases=["a", "stock"],
        )

        self.register(
            "sapta",
            self._cmd_sapta,
            "SAPTA PRE-MARKUP detection engine",
            "/sapta <TICKER> | /sapta scan [universe]",
            aliases=["premarkup", "markup"],
        )

        self.register(
            "technical",
            self._cmd_technical,
            "Technical analysis (技術分析)",
            "/technical <TICKER>",
            aliases=["tech", "ta"],
        )

        self.register(
            "fundamental",
            self._cmd_fundamental,
            "Fundamental analysis (基本面分析)",
            "/fundamental <TICKER>",
            aliases=["fund", "fa"],
        )

        self.register(
            "institutional",
            self._cmd_broker,
            "Institutional investor flow (法人動向)",
            "/institutional <TICKER>",
            aliases=["inst", "flow", "broker"],
        )

        self.register(
            "screen",
            self._cmd_screen,
            "Stock screener (股票篩選)",
            "/screen <strategy> [universe]",
            aliases=["scan", "filter"],
        )

        self.register(
            "sector",
            self._cmd_sector,
            "Sector analysis (產業分析)",
            "/sector [sector_name]",
            aliases=["industry"],
        )

        self.register(
            "compare",
            self._cmd_compare,
            "Compare stocks (股票比較)",
            "/compare <TICKER1> <TICKER2> [...]",
            aliases=["cmp", "vs"],
        )

        self.register(
            "chart",
            self._cmd_chart,
            "Generate stock chart (K線圖)",
            "/chart <TICKER> [period]",
            aliases=["k", "kline"],
        )

        self.register(
            "forecast",
            self._cmd_forecast,
            "Price forecast (價格預測)",
            "/forecast <TICKER> [days]",
            aliases=["pred", "predict"],
        )

        self.register(
            "taiex",
            self._cmd_taiex,
            "Taiwan index overview (大盤指數)",
            "/taiex [TPEX]",
            aliases=["twii", "index"],
        )

        self.register(
            "plan",
            self._cmd_plan,
            "Generate trading plan (交易計劃)",
            "/plan <TICKER>",
            aliases=["trade"],
        )

        self.register(
            "clear",
            self._cmd_clear,
            "Clear chat history",
            "/clear",
            aliases=["cls"],
        )

    async def _cmd_help(self, args: str) -> str:
        """Help command handler."""
        if args:
            cmd = self.get(args.strip())
            if cmd:
                aliases_str = ", ".join(f"/{a}" for a in cmd.aliases) if cmd.aliases else "無"
                return f"""/{cmd.name}

說明: {cmd.description}
用法: {cmd.usage}
別名: {aliases_str}
"""
            else:
                return f"未知的命令: /{args}"

        lines = ["可用命令\n"]

        for cmd in self.list_commands():
            aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"  /{cmd.name}{aliases} - {cmd.description}")

        lines.append("\n輸入 /help <命令> 查看詳細說明")

        return "\n".join(lines)

    async def _cmd_models(self, args: str) -> str | None:
        """Models command handler."""
        if args:
            model_id = args.strip()
            self.app.ai_client.set_model(model_id)

            model_info = self.app.ai_client.get_current_model()
            return f"已切換至模型: {model_info['name']}"

        # No args - show modal
        self.app.show_models_modal()
        return None  # Don't output anything to chat

    async def _cmd_analyze(self, args: str) -> str:
        """Analyze command handler."""
        if not args:
            return "請指定股票代碼。用法: /analyze 2330 (台積電)"

        ticker = args.strip().upper()

        from pulse.core.analysis.institutional_flow import InstitutionalFlowAnalyzer
        from pulse.core.analysis.technical import TechnicalAnalyzer
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        stock = await fetcher.fetch_stock(ticker)

        if not stock:
            return f"無法取得 {ticker} 的資料"

        tech_analyzer = TechnicalAnalyzer()
        technical = await tech_analyzer.analyze(ticker)

        broker_analyzer = InstitutionalFlowAnalyzer()
        broker = await broker_analyzer.analyze(ticker)

        data = {
            "stock": {
                "ticker": stock.ticker,
                "name": stock.name,
                "price": stock.current_price,
                "change": stock.change,
                "change_percent": stock.change_percent,
                "volume": stock.volume,
                "market_cap": stock.market_cap,
            },
            "technical": technical.to_summary() if technical else None,
            "broker": broker if broker else None,
        }

        response = await self.app.ai_client.analyze_stock(ticker, data)

        return response

    async def _cmd_broker(self, args: str) -> str:
        """Broker flow command handler."""
        if not args:
            return "請指定股票代碼。用法: /institutional 2330 (台積電)"

        ticker = args.strip().upper()

        from pulse.core.analysis.institutional_flow import InstitutionalFlowAnalyzer

        analyzer = InstitutionalFlowAnalyzer()

        result = await analyzer.analyze(ticker)

        if not result:
            return f"無法取得 {ticker} 的法人動向資料"

        return analyzer.format_summary_table(result)

    async def _cmd_technical(self, args: str) -> str:
        """Technical analysis command handler."""
        if not args:
            return "請指定股票代碼。用法: /technical 2330 (台積電)"

        ticker = args.strip().upper()

        from pulse.core.analysis.technical import TechnicalAnalyzer

        analyzer = TechnicalAnalyzer()
        indicators = await analyzer.analyze(ticker)

        if not indicators:
            return f"無法分析 {ticker}，請確認股票代碼是否正確"

        summary = analyzer.get_indicator_summary(indicators)

        # Translate status labels
        status_map = {
            "Overbought": "超買",
            "Oversold": "超賣",
            "Neutral": "中性",
            "Bullish": "多頭",
            "Bearish": "空頭",
            "Strong": "強勢",
            "Weak": "弱勢",
        }

        lines = [f"技術分析: {ticker}\n"]

        for item in summary:
            status_text = item.get("status", "")
            status_zh = status_map.get(status_text, status_text)
            status = f" ({status_zh})" if status_zh else ""
            lines.append(f"  {item['name']}: {item['value']}{status}")

        return "\n".join(lines)

    async def _cmd_fundamental(self, args: str) -> str:
        """Fundamental analysis command handler."""
        if not args:
            return "請指定股票代碼。用法: /fundamental 2330 (台積電)"

        ticker = args.strip().upper()

        from pulse.core.analysis.fundamental import FundamentalAnalyzer

        analyzer = FundamentalAnalyzer()
        data = await analyzer.analyze(ticker)

        if not data:
            return f"無法取得 {ticker} 的基本面資料"

        summary = analyzer.get_summary(data)
        score_data = analyzer.score_valuation(data)

        # Translate category and status labels
        category_map = {
            "Valuation": "估值指標",
            "Profitability": "獲利能力",
            "Growth": "成長指標",
            "Dividend": "股利資訊",
            "Financial Health": "財務健康",
        }
        status_map = {
            "Undervalued": "低估",
            "Overvalued": "高估",
            "Fair": "合理",
            "Good": "良好",
            "Excellent": "優秀",
            "Poor": "較差",
            "High": "高",
            "Low": "低",
        }

        lines = [f"基本面分析: {ticker}\n"]
        lines.append(f"估值評分: {score_data['score']}/100\n")

        current_category = ""
        for item in summary:
            if item["category"] != current_category:
                current_category = item["category"]
                category_zh = category_map.get(current_category, current_category)
                lines.append(f"\n{category_zh}")

            status_text = item.get("status", "")
            status_zh = status_map.get(status_text, status_text)
            status = f" ({status_zh})" if status_zh else ""
            lines.append(f"  {item['name']}: {item['value']}{status}")

        return "\n".join(lines)

    async def _cmd_screen(self, args: str) -> str:
        """Screen stocks based on technical/fundamental criteria."""
        if not args:
            return """Stock Screening (股票篩選)

Usage: /screen <criteria> [--universe=tw50|midcap|popular]

Presets (預設篩選條件):
  /screen oversold    - RSI < 30 (超賣,準備反彈)
  /screen overbought  - RSI > 70 (超買,準備回落)
  /screen bullish     - MACD bullish + price > SMA20 (多頭)
  /screen bearish     - MACD bearish + price < SMA20 (空頭)
  /screen breakout    - Near resistance + volume spike (突破)
  /screen momentum    - RSI 50-70 + MACD bullish (動能)
  /screen undervalued - PE < 15 + ROE > 10% (低估)

Flexible (自訂條件):
  /screen rsi<30
  /screen rsi>70
  /screen pe<15

Universe (股票池):
  --universe=tw50    - 台灣50成分股 (快速)
  --universe=midcap  - 中型股100檔 (中速)
  --universe=popular - 熱門股150檔 (較慢)

Example (範例):
  /screen oversold --universe=tw50
"""

        from pulse.core.screener import ScreenPreset, StockScreener, StockUniverse

        # Parse universe option
        universe_type = None
        criteria_str = args

        if "--universe=" in args.lower():
            import re

            match = re.search(r"--universe=(\w+)", args.lower())
            if match:
                universe_map = {
                    "tw50": StockUniverse.TW50,
                    "lq45": StockUniverse.TW50,  # backward compat
                    "midcap": StockUniverse.MIDCAP,
                    "tw100": StockUniverse.MIDCAP,
                    "popular": StockUniverse.POPULAR,
                    "all": StockUniverse.ALL,
                }
                universe_type = universe_map.get(match.group(1))
                criteria_str = re.sub(r"\s*--universe=\w+", "", args).strip()

        # Create screener with proper universe
        screener = StockScreener()
        args_lower = criteria_str.strip().lower()

        # Check if it's a preset
        preset_names = [p.value for p in ScreenPreset]
        if args_lower in preset_names:
            results = await screener.screen_preset(ScreenPreset(args_lower))
            title = f"Screening: {args_lower.upper()} ({len(screener.universe)} stocks)"
        else:
            # Use flexible criteria
            results = await screener.screen_criteria(criteria_str)
            title = f"Screening: {criteria_str} ({len(screener.universe)} stocks)"

        if not results:
            return f"找不到符合條件的股票: {criteria_str}"

        return screener.format_results(results, title=title, show_details=True)

    async def _cmd_sector(self, args: str) -> str:
        """Sector analysis command handler."""
        from pulse.core.analysis.sector import SectorAnalyzer
        from pulse.utils.constants import TW_SECTORS

        analyzer = SectorAnalyzer()

        if not args:
            sectors = analyzer.list_sectors()

            lines = ["可用產業類別\n"]
            for s in sectors:
                lines.append(f"  {s['name']} ({s['stock_count']} 檔)")

            lines.append("\n用法: /sector <產業代碼> 進行產業分析")

            return "\n".join(lines)

        sector = args.strip().upper()

        if sector not in TW_SECTORS:
            return f"未知的產業類別: {sector}"

        analysis = await analyzer.analyze_sector(sector)

        if not analysis:
            return f"無法分析產業 {sector}"

        lines = [f"產業分析: {sector}\n"]
        lines.append(f"分析股票數: {analysis.total_stocks} 檔")
        lines.append(f"平均漲跌: {analysis.avg_change_percent:.2f}%\n")

        if analysis.top_gainers:
            lines.append("漲幅前三")
            for g in analysis.top_gainers[:3]:
                lines.append(f"  {g['ticker']}: +{g['change_percent']:.2f}%")

        if analysis.top_losers:
            lines.append("\n跌幅前三")
            for l in analysis.top_losers[:3]:
                lines.append(f"  {l['ticker']}: {l['change_percent']:.2f}%")

        return "\n".join(lines)

    async def _cmd_compare(self, args: str) -> str:
        """Compare stocks command handler."""
        if not args:
            return "請指定股票代碼。用法: /compare 2330 2454 (台積電 vs 聯發科)"

        tickers = args.strip().upper().split()

        if len(tickers) < 2:
            return "請至少指定 2 檔股票進行比較"

        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        results = []

        for ticker in tickers[:4]:  # Max 4 tickers
            stock = await fetcher.fetch_stock(ticker)
            if stock:
                results.append(
                    {
                        "ticker": stock.ticker,
                        "name": stock.name or ticker,
                        "price": stock.current_price,
                        "change": stock.change,
                        "change_pct": stock.change_percent,
                        "volume": stock.volume,
                    }
                )

        if len(results) < 2:
            return "無法取得足夠的資料進行比較"

        lines = ["═══ 股票比較 ═══\n"]
        lines.append("┌────────┬──────────────┬────────────┬────────────────┐")
        lines.append("│  代碼  │     股價     │   漲跌幅   │      成交量    │")
        lines.append("├────────┼──────────────┼────────────┼────────────────┤")

        for r in results:
            change_str = f"{r['change_pct']:+.2f}%"
            icon = "📈" if r['change_pct'] >= 0 else "📉"
            vol_str = f"{r['volume']:,.0f}"
            lines.append(f"│ {r['ticker']:<6} │ {r['price']:>12,.0f} │ {change_str:>10} │ {vol_str:>14} │")

        lines.append("└────────┴──────────────┴────────────┴────────────────┘")

        return "\n".join(lines)

    async def _cmd_chart(self, args: str) -> str:
        """Chart command handler - generate and save price chart as PNG."""
        if not args:
            return "請指定股票代碼。用法: /chart 2330 [1mo|3mo|6mo|1y] (台積電圖表)"

        parts = args.strip().upper().split()
        ticker = parts[0]
        period = parts[1].lower() if len(parts) > 1 else "3mo"

        # Validate period
        valid_periods = ["1mo", "3mo", "6mo", "1y", "2y"]
        if period not in valid_periods:
            period = "3mo"

        from pulse.core.chart_generator import ChartGenerator
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        df = fetcher.get_history_df(ticker, period)

        if df is None or df.empty:
            return f"無法取得 {ticker} 的歷史資料"

        dates = df.index.strftime("%Y-%m-%d").tolist()
        prices = df["close"].tolist()
        volumes = df["volume"].tolist() if "volume" in df.columns else None

        # Generate PNG chart
        generator = ChartGenerator()
        filepath = generator.price_chart(ticker, dates, prices, volumes, period)

        if not filepath:
            return f"無法產生 {ticker} 的圖表"

        # Get current price info
        current = prices[-1]
        prev = prices[-2] if len(prices) > 1 else current
        change = current - prev
        change_pct = (change / prev * 100) if prev else 0

        return f"""{ticker}: NT$ {current:,.2f} ({change:+,.2f}, {change_pct:+.2f}%)

圖表已儲存: {filepath}"""

    async def _cmd_forecast(self, args: str) -> str:
        """Forecast command handler - predict future prices and save chart as PNG."""
        if not args:
            return "請指定股票代碼。用法: /forecast 2330 [7|14|30] (台積電預測)"

        parts = args.strip().upper().split()
        ticker = parts[0]

        # Parse days
        days = 7
        if len(parts) > 1:
            try:
                days = int(parts[1])
                days = min(max(days, 1), 30)  # Clamp between 1-30
            except ValueError:
                days = 7

        from pulse.core.chart_generator import ChartGenerator
        from pulse.core.data.yfinance import YFinanceFetcher
        from pulse.core.forecasting import PriceForecaster

        fetcher = YFinanceFetcher()
        df = fetcher.get_history_df(ticker, "6mo")

        if df is None or df.empty:
            return f"{ticker} 的歷史資料不足，無法預測"

        prices = df["close"].tolist()
        dates = df.index.strftime("%Y-%m-%d").tolist()

        forecaster = PriceForecaster()
        result = await forecaster.forecast(ticker, prices, dates, days)

        if not result:
            return f"{ticker} 預測失敗"

        # Generate PNG chart
        generator = ChartGenerator()
        filepath = generator.forecast_chart(
            ticker=ticker,
            dates=dates,
            historical=prices,
            forecast=result.predictions,
            lower_bound=result.lower_bound,
            upper_bound=result.upper_bound,
            forecast_days=days,
        )

        # Format summary
        current = prices[-1]
        target = result.target_price
        change_pct = (target - current) / current * 100
        trend_map = {"UP": "📈 上漲", "DOWN": "📉 下跌", "SIDEWAYS": "➡️ 盤整"}
        trend_key = "UP" if change_pct > 0 else "DOWN" if change_pct < 0 else "SIDEWAYS"
        trend_zh = trend_map[trend_key]
        change_color = "+" if change_pct > 0 else ""

        summary = f"""═══ 價格預測: {ticker} ({days} 天) ═══

┌─────────────────────────────────┐
│  現價      │ NT$ {current:>12,.2f}  │
│  目標價    │ NT$ {target:>12,.2f}  │
│  預期漲跌  │ {change_color}{change_pct:>12.2f}%  │
├─────────────────────────────────┤
│  趨勢      │ {trend_zh:<14}  │
│  支撐位    │ NT$ {result.support:>12,.2f}  │
│  壓力位    │ NT$ {result.resistance:>12,.2f}  │
│  信心度    │ {result.confidence:>12.0f}%  │
└─────────────────────────────────┘"""

        if filepath:
            summary += f"\n\n📊 圖表已儲存: {filepath}"

        return summary

    async def _cmd_clear(self, args: str) -> str | None:
        """Clear chat history."""
        self.app.action_clear()
        return None

    async def _cmd_taiex(self, args: str) -> str:
        """Show TAIEX or other Taiwan index status."""
        # Determine which index to show
        index_name = args.strip().upper() if args else "TAIEX"

        valid_indices = ["TAIEX", "TWII", "TPEX", "OTC", "TW50"]
        if index_name not in valid_indices:
            return f"""未知的指數: {index_name}

可用指數:
  TAIEX - 加權指數
  TPEX  - 櫃買指數
  TW50  - 台灣50 ETF

用法: /taiex [指數代碼]
範例: /taiex TPEX
"""

        from pulse.core.chart_generator import ChartGenerator
        from pulse.core.data.yfinance import YFinanceFetcher

        fetcher = YFinanceFetcher()
        index_data = await fetcher.fetch_index(index_name)

        if not index_data:
            return f"無法取得 {index_name} 的資料"

        # Generate chart
        yf_ticker = fetcher.INDEX_MAPPING.get(index_name, ("^TWII", "TAIEX"))[0]
        df = fetcher.get_history_df(yf_ticker, "3mo")
        chart_path = None

        if df is not None and not df.empty:
            generator = ChartGenerator()
            dates = df.index.strftime("%Y-%m-%d").tolist()
            prices = df["close"].tolist()
            chart_path = generator.price_chart(index_name, dates, prices, period="3mo")

        # Format response
        change_sign = "+" if index_data.change >= 0 else ""
        trend_icon = "📈" if index_data.change >= 0 else "📉"

        result = f"""═══ {index_data.name} ({index_name}) ═══

┌─────────────────────────────────┐
│  指數      │ {index_data.current_price:>15,.2f}  │
│  漲跌      │ {change_sign}{index_data.change:>14,.2f}  │
│  漲跌幅    │ {change_sign}{index_data.change_percent:>14.2f}%  │
├─────────────────────────────────┤
│  今日最高  │ {index_data.day_high:>15,.2f}  │
│  今日最低  │ {index_data.day_low:>15,.2f}  │
│  52週最高  │ {index_data.week_52_high:>15,.2f}  │
│  52週最低  │ {index_data.week_52_low:>15,.2f}  │
└─────────────────────────────────┘

{trend_icon} 趨勢: {"上漲" if index_data.change >= 0 else "下跌"}"""

        if chart_path:
            result += f"\n\n📊 圖表已儲存: {chart_path}"

        return result

    async def _cmd_plan(self, args: str) -> str:
        """Trading plan command handler."""
        if not args:
            return """Trading Plan - Generate TP/SL/RR analysis (交易計畫生成器)

Usage: /plan <TICKER> [account_size]

Examples (範例):
  /plan 2330              - Trading plan with default account size (預設帳戶大小)
  /plan 2881 1000000      - Trading plan with NT$ 1M account (百萬帳戶)

Output includes (輸出內容):
  - Entry price (current market) (進場價格)
  - Take Profit levels (TP1, TP2, TP3) (停利點位)
  - Stop Loss with method used (停損點位)
  - Risk/Reward ratio analysis (風險報酬比分析)
  - Position sizing suggestion (部位建議)
  - Execution strategy (執行策略)"""

        parts = args.strip().split()
        ticker = parts[0].upper()

        # Parse optional account size
        account_size = None
        if len(parts) > 1:
            try:
                account_size = float(parts[1].replace(",", "").replace(".", ""))
            except ValueError:
                return f"Invalid account size: {parts[1]}"

        from pulse.core.trading_plan import TradingPlanGenerator

        generator = TradingPlanGenerator()
        plan = await generator.generate(ticker)

        if not plan:
            return f"Could not generate trading plan for {ticker}. Make sure the ticker is valid."

        # Format with optional account size
        return generator.format_plan(plan, account_size=account_size)

    async def _cmd_sapta(self, args: str) -> str:
        """SAPTA PRE-MARKUP detection command handler."""
        if not args:
            return """SAPTA - PRE-MARKUP Detection Engine (預漲偵測引擎 - ML機器學習)

Usage (用法):
  /sapta <TICKER>              - Analyze single stock (分析單一股票)
  /sapta scan [universe]       - Scan for PRE-MARKUP candidates (掃描預漲股)

Universe Options (股票池選項):
  /sapta scan tw50             - Scan TW50 (台灣50, 50檔股票, 快速)
  /sapta scan midcap           - Scan Mid-Cap 100 stocks (中型股100檔)
  /sapta scan popular          - Scan popular stocks (熱門股)
  /sapta scan all              - Scan ALL stocks (全部股票, 較慢)

Options (選項):
  --detailed                   - Show module breakdown (顯示模組詳情)

Examples (範例):
  /sapta 2330                  - Analyze TSMC (分析台積電)
  /sapta 2881 --detailed       - Detailed analysis (詳細分析國泰金)
  /sapta scan all              - Scan all stocks for pre-markup (掃描全市場)

Status Levels (狀態等級 - ML學習門檻):
  PRE-MARKUP  (score >= 47)    - Ready to breakout (準備突破)
  SIAP        (score >= 35)    - Almost ready (接近突破)
  WATCHLIST   (score >= 24)    - Monitor (觀察中)
  SKIP        (score < 24)     - Skip (跳過)

Modules (分析模組):
  1. Supply Absorption - Smart money accumulation (供給吸收 - 主力吸籌)
  2. Compression - Volatility contraction (壓縮 - 波動收斂)
  3. BB Squeeze - Bollinger Band squeeze (布林通道擠壓)
  4. Elliott Wave - Wave position & Fibonacci (艾略特波浪 & 費波那契)
  5. Time Projection - Fib time + planetary aspects (時間投影 - 費氏時間)
  6. Anti-Distribution - Filter distribution patterns (反派發 - 過濾出貨)
  7. Institutional Flow - Foreign/Trust flow analysis (法人動向分析)
"""

        from pulse.core.sapta import SaptaEngine, SaptaStatus
        from pulse.core.screener import StockScreener, StockUniverse

        engine = SaptaEngine()
        args_lower = args.lower().strip()
        detailed = "--detailed" in args_lower
        args_clean = args_lower.replace("--detailed", "").strip()

        # Check if it's a scan command
        if args_clean.startswith("scan"):
            parts = args_clean.split()
            universe = parts[1] if len(parts) > 1 else "lq45"

            # Check for "all" universe - scan all stocks from tickers.json
            if universe in ["all", "semua", "955"]:
                try:
                    from pulse.core.sapta.ml.data_loader import SaptaDataLoader

                    loader = SaptaDataLoader()
                    tickers = loader.get_all_tickers()
                    universe_name = f"ALL ({len(tickers)} stocks)"
                    min_status = SaptaStatus.SIAP  # Higher threshold for large scan
                except Exception as e:
                    return f"Could not load tickers: {e}"
            else:
                # Select universe using screener's universe logic
                universe_map = {
                    "tw50": StockUniverse.TW50,
                    "lq45": StockUniverse.TW50,  # backward compat
                    "midcap": StockUniverse.MIDCAP,
                    "tw100": StockUniverse.MIDCAP,
                    "popular": StockUniverse.POPULAR,
                }
                universe_type = universe_map.get(universe, StockUniverse.TW50)
                screener = StockScreener(universe_type=universe_type)
                tickers = screener.universe
                universe_name = universe.upper()
                min_status = SaptaStatus.WATCHLIST

            # Scan
            results = await engine.scan(tickers, min_status=min_status)

            if not results:
                return f"No stocks found in {universe_name} matching SAPTA criteria."

            return engine.format_scan_results(
                results, title=f"SAPTA Scan: {universe_name} ({len(results)} found)"
            )

        # Single stock analysis
        ticker = args_clean.split()[0].upper()

        result = await engine.analyze(ticker)

        if not result:
            return f"Could not analyze {ticker}. Make sure the ticker is valid."

        return engine.format_result(result, detailed=detailed)
