"""
SmartAgent - True Agentic Flow for Stock Analysis.

Flow:
1. User message -> Parse intent & extract tickers
2. Fetch REAL data from yfinance
3. Run analysis tools (technical, fundamental, etc)
4. Build context with real data
5. AI analyzes with full context
6. Return insight to user

This is NOT a proxy to AI - this is an agent that gathers data first,
then uses AI to analyze and explain the data.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from pulse.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class AgentContext:
    """Context built from real data for AI analysis."""

    ticker: str | None = None
    tickers: list[str] = field(default_factory=list)
    intent: str = "general"
    stock_data: dict[str, Any] | None = None
    technical_data: dict[str, Any] | None = None
    fundamental_data: dict[str, Any] | None = None
    historical_prices: list[float] | None = None
    comparison_data: list[dict[str, Any]] | None = None
    error: str | None = None


@dataclass
class AgentResponse:
    """Response from agent execution."""

    message: str
    context: AgentContext | None = None
    chart: str | None = None
    raw_data: dict[str, Any] | None = None


class SmartAgent:
    """
    Smart agent that fetches real data FIRST, then uses AI for analysis.

    This implements true agentic flow:
    User Question -> Data Gathering -> AI Analysis with Context -> Response
    """

    # Taiwan stock tickers (common ones)
    KNOWN_TICKERS = {
        # Semiconductor (半導體)
        "2330",  # 台積電
        "2454",  # 聯發科
        "2303",  # 聯電
        "3711",  # 日月光投控
        "2379",  # 瑞昱
        "3034",  # 聯詠
        "6415",  # 矽力KY
        "2449",  # 京元電子
        "3529",  # 力旺
        "2408",  # 南亞科
        # Electronics (電子)
        "2317",  # 鴻海
        "2382",  # 廣達
        "2357",  # 華碩
        "3231",  # 緯創
        "2324",  # 仁寶
        "2356",  # 英業達
        "2301",  # 光寶科
        "2308",  # 台達電
        # Finance (金融)
        "2881",  # 富邦金
        "2882",  # 國泰金
        "2891",  # 中信金
        "2886",  # 兆豐金
        "2884",  # 玉山金
        "2892",  # 第一金
        "2880",  # 華南金
        "2883",  # 開發金
        "2887",  # 台新金
        "5880",  # 合庫金
        # Steel (鋼鐵)
        "2002",  # 中鋼
        "2006",  # 東和鋼鐵
        "2014",  # 中鴻
        "2027",  # 大成鋼
        # Plastic (塑化)
        "1301",  # 台塑
        "1303",  # 南亞
        "1326",  # 台化
        "6505",  # 台塑化
        # Food (食品)
        "1216",  # 統一
        "1227",  # 佳格
        "1229",  # 聯華
        "1231",  # 聯華食
        # Biotech (生技)
        "4736",  # 泰博
        "4743",  # 合一
        "4746",  # 台耀
        "6446",  # 藥華藥
        # Telecom (電信)
        "2412",  # 中華電
        "3045",  # 台灣大
        "4904",  # 遠傳
        # Others (其他)
        "2912",  # 統一超
        "2801",  # 彰銀
        "2603",  # 長榮
        "2609",  # 陽明
    }

    # Words that look like tickers but aren't (Taiwan context)
    TICKER_BLACKLIST = {
        # Numbers that aren't tickers
        "1000",
        "2000",
        "3000",
        "5000",
        "10000",
        # Common Chinese/English words
        "STOP",
        "LOSS",
        "HOLD",
        "CHART",
        "DATA",
    }

    # Taiwan market indices
    KNOWN_INDICES = {
        "TAIEX": "^TWII",
        "TWII": "^TWII",
        "TPEX": "^TWOTCI",
        "OTC": "^TWOTCI",
        "TW50": "0050.TW",
    }

    # Intent patterns - Traditional Chinese & English
    INTENT_PATTERNS = {
        "analyze": [
            r"分析\s*(\d{4})",
            r"分析\s+(\w+)",
            r"看看\s*(\d{4})",
            r"查看\s*(\d{4})",
            r"檢查\s*(\d{4})",
            r"analyze\s+(\w+)",
            r"review\s+(\w+)",
        ],
        "price": [
            r"價格\s*(\d{4})",
            r"股價\s*(\d{4})",
            r"多少\s*(\d{4})",
            r"price\s+(\w+)",
        ],
        "chart": [
            r"圖表\s*(\d{4})",
            r"走勢\s*(\d{4})",
            r"chart\s+(\w+)",
            r"graph\s+(\w+)",
        ],
        "technical": [
            r"技術\s*(\d{4})",
            r"技術面\s*(\d{4})",
            r"technical\s+(\w+)",
            r"ta\s+(\w+)",
            r"rsi\s+(\w+)",
            r"macd\s+(\w+)",
        ],
        "fundamental": [
            r"基本面\s*(\d{4})",
            r"fundamental\s+(\w+)",
            r"valuation\s+(\w+)",
            r"pe\s+(\w+)",
            r"pbv\s+(\w+)",
        ],
        "forecast": [
            r"預測\s*(\d{4})",
            r"預估\s*(\d{4})",
            r"forecast\s+(\w+)",
            r"target\s+(\w+)",
        ],
        "compare": [
            r"比較\s*(\d{4})\s*(?:和|與|跟)\s*(\d{4})",
            r"(\d{4})\s+vs\.?\s+(\d{4})",
            r"(\w+)\s+vs\.?\s+(\w+)",
        ],
        "recommendation": [
            r"推薦\s*(\d{4})",
            r"建議\s*(\d{4})",
            r"可以買\s*(\d{4})",
            r"worth\s+(?:it)?\s+(\w+)",
        ],
        "screen": [
            r"找股票",
            r"篩選股票",
            r"尋找.*股票",
            r"哪些股票",
            r"什麼股票",
            r"screen\s+(.+)",
            r"filter\s+(.+)",
            r"rsi\s*[<>]\s*\d+",
            r"pe\s*[<>]\s*\d+",
            r"oversold",
            r"overbought",
            r"超賣",
            r"超買",
            r"bullish",
            r"bearish",
            r"多頭",
            r"空頭",
            r"breakout",
            r"突破",
            r"undervalued",
            r"低估",
            r"潛力股",
            r"推薦.*股票",
            r"small\s*cap",
            r"mid\s*cap",
        ],
        "trading_plan": [
            r"交易計畫\s*(\d{4})",
            r"trading\s*plan\s+(\w+)",
            r"plan\s+(\w+)",
            r"tp\s+sl\s+(\w+)",
            r"停利停損\s*(\d{4})",
            r"stop\s*loss\s+(\w+)",
            r"take\s*profit\s+(\w+)",
            r"停損\s*(\d{4})",
            r"停利\s*(\d{4})",
            r"rr\s+(\w+)",
            r"risk\s*reward\s+(\w+)",
            r"entry\s+(\w+)",
            r"進場\s*(\d{4})",
            r"出場\s*(\d{4})",
            r"目標價\s*(\d{4})",
        ],
        "sapta": [
            r"sapta\s+(\w+)",
            r"預漲\s*(\d{4})",
            r"準備突破\s*(\d{4})",
            r"pre[\s\-]?markup\s+(\w+)",
            r"(\d{4})\s*準備突破",
            r"(\d{4})\s*要突破",
            r"(\w+)\s+breakout",
        ],
    }

    def __init__(self):
        self.ai_client = None  # Lazy load
        self._last_ticker: str | None = None  # Remember last analyzed ticker
        self._last_context: AgentContext | None = None  # Remember last context

    def _get_ai_client(self):
        """Get AI client lazily."""
        if self.ai_client is None:
            from pulse.ai.client import AIClient

            self.ai_client = AIClient()
        return self.ai_client

    def _extract_tickers(self, message: str) -> list[str]:
        """Extract stock tickers from message (Taiwan 4-6 digit codes)."""
        tickers = []

        # Check for known tickers (4-digit codes)
        for ticker in self.KNOWN_TICKERS:
            if ticker in message:
                tickers.append(ticker)

        # Also check for 4-6 digit numbers that might be tickers
        words = re.findall(r"\b(\d{4,6})\b", message)
        for word in words:
            if word not in tickers and self._is_valid_ticker(word):
                tickers.append(word)

        return list(set(tickers))

    def _is_valid_ticker(self, ticker: str) -> bool:
        """Validate ticker format (Taiwan 4-6 digit codes)."""
        # Must be in known tickers OR not in blacklist
        if ticker in self.KNOWN_TICKERS:
            return True
        # Reject blacklisted words
        if ticker in self.TICKER_BLACKLIST:
            return False
        # For Taiwan, accept 4-6 digit numbers
        if re.match(r"^\d{4,6}$", ticker):
            return True
        return False

    def _detect_intent(self, message: str) -> tuple[str, list[str]]:
        """
        Detect user intent and extract tickers.

        Returns:
            Tuple of (intent, tickers)
        """
        message_lower = message.lower().strip()

        # Check for index intent first (TAIEX, TW50, etc)
        # BUT NOT if there are screening keywords
        screen_context_keywords = ["screen", "篩選", "尋找", "找股票", "filter"]
        has_screen_context = any(kw in message_lower for kw in screen_context_keywords)

        if not has_screen_context:
            for index_name in self.KNOWN_INDICES:
                if index_name.lower() in message_lower:
                    return "index", [index_name]

        # Check for market keywords
        if any(kw in message_lower for kw in ["大盤", "市場", "指數", "market", "taiex"]):
            return "index", ["TAIEX"]

        # Check for trading plan intent (check BEFORE screen)
        trading_plan_keywords = [
            "trading plan",
            "交易計畫",
            "tp sl",
            "停利停損",
            "stop loss",
            "停損",
            "take profit",
            "停利",
            "risk reward",
            "進場",
            "出場",
            "目標價",
            "rr ratio",
        ]
        # Only trigger if has ticker AND trading plan keyword
        if any(kw in message_lower for kw in trading_plan_keywords):
            tickers = self._extract_tickers(message)
            if tickers:
                return "trading_plan", tickers

        # Check for SAPTA/pre-markup intent (check BEFORE screen)
        sapta_keywords = [
            "sapta",
            "預漲",
            "pre-markup",
            "premarkup",
            "pre markup",
            "準備突破",
            "要突破",
            "breakout",
        ]
        # Extended SAPTA scan keywords (natural language)
        sapta_scan_keywords = [
            "找預漲股票",
            "尋找預漲",
            "預漲股票",
            "找準備突破",
            "準備突破的股票",
            "即將突破",
            "scan pre-markup",
            "scan premarkup",
            "pre-markup scan",
            "找突破股",
        ]
        # Check for SAPTA scan first (natural language screening)
        if any(kw in message_lower for kw in sapta_scan_keywords):
            return "sapta_scan", []
        # Then check for single ticker SAPTA
        if any(kw in message_lower for kw in sapta_keywords):
            tickers = self._extract_tickers(message)
            if tickers:
                return "sapta", tickers
            # Check if it's a scan command
            if "scan" in message_lower or "cari" in message_lower or "carikan" in message_lower:
                return "sapta_scan", []

        # Check for screen intent (doesn't require tickers)
        screen_keywords = [
            "找股票",
            "篩選股票",
            "什麼股票",
            "哪些股票",
            "尋找股票",
            "oversold",
            "overbought",
            "超賣",
            "超買",
            "bullish",
            "bearish",
            "多頭",
            "空頭",
            "breakout",
            "突破",
            "undervalued",
            "低估",
            "便宜",
            "screen",
            "filter",
            "潛力股",
            "推薦股票",
            "small cap",
            "mid cap",
            "大漲",
        ]
        if any(kw in message_lower for kw in screen_keywords):
            return "screen", []

        # Check for rsi/pe/etc with operators (screening criteria)
        if re.search(r"(rsi|pe|pb|roe|macd)\s*[<>]\s*\d+", message_lower):
            return "screen", []

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    # Extract tickers from match groups
                    tickers = []
                    for group in match.groups():
                        ticker = group.upper()
                        if self._is_valid_ticker(ticker):
                            tickers.append(ticker)

                    if tickers:
                        return intent, tickers

        # Fallback: extract any tickers mentioned
        tickers = self._extract_tickers(message)
        if tickers:
            return "analyze", tickers  # Default to analyze if tickers found

        return "general", []

    async def _fetch_stock_data(self, ticker: str) -> dict[str, Any] | None:
        """Fetch real stock data from yfinance."""
        try:
            from pulse.core.data.yfinance import YFinanceFetcher

            fetcher = YFinanceFetcher()
            stock = await fetcher.fetch_stock(ticker)

            if not stock:
                return None

            return {
                "ticker": stock.ticker,
                "name": stock.name,
                "sector": stock.sector,
                "current_price": stock.current_price,
                "previous_close": stock.previous_close,
                "change": stock.change,
                "change_percent": stock.change_percent,
                "volume": stock.volume,
                "avg_volume": stock.avg_volume,
                "day_high": stock.day_high,
                "day_low": stock.day_low,
                "week_52_high": stock.week_52_high,
                "week_52_low": stock.week_52_low,
                "market_cap": stock.market_cap,
            }
        except Exception as e:
            log.error(f"Error fetching stock data for {ticker}: {e}")
            return None

    async def _fetch_technical(self, ticker: str) -> dict[str, Any] | None:
        """Fetch technical analysis data."""
        try:
            from pulse.core.analysis.technical import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            indicators = await analyzer.analyze(ticker)

            if not indicators:
                return None

            return {
                "rsi_14": indicators.rsi_14,
                "macd": indicators.macd,
                "macd_signal": indicators.macd_signal,
                "macd_histogram": indicators.macd_histogram,
                "sma_20": indicators.sma_20,
                "sma_50": indicators.sma_50,
                "sma_200": indicators.sma_200,
                "ema_9": indicators.ema_9,
                "ema_21": indicators.ema_21,
                "bb_upper": indicators.bb_upper,
                "bb_middle": indicators.bb_middle,
                "bb_lower": indicators.bb_lower,
                "stoch_k": indicators.stoch_k,
                "stoch_d": indicators.stoch_d,
                "atr_14": indicators.atr_14,
                "support_1": indicators.support_1,
                "resistance_1": indicators.resistance_1,
                "trend": indicators.trend.value if indicators.trend else None,
                "signal": indicators.signal.value if indicators.signal else None,
            }
        except Exception as e:
            log.error(f"Error fetching technical data for {ticker}: {e}")
            return None

    async def _fetch_fundamental(self, ticker: str) -> dict[str, Any] | None:
        """Fetch fundamental data."""
        try:
            from pulse.core.data.yfinance import YFinanceFetcher

            fetcher = YFinanceFetcher()
            fund = await fetcher.fetch_fundamentals(ticker)

            if not fund:
                return None

            return {
                "pe_ratio": fund.pe_ratio,
                "pb_ratio": fund.pb_ratio,
                "ps_ratio": fund.ps_ratio,
                "roe": fund.roe,
                "roa": fund.roa,
                "npm": fund.npm,
                "debt_to_equity": fund.debt_to_equity,
                "current_ratio": fund.current_ratio,
                "dividend_yield": fund.dividend_yield,
                "eps": fund.eps,
                "bvps": fund.bvps,
                "revenue_growth": fund.revenue_growth,
                "earnings_growth": fund.earnings_growth,
                "market_cap": fund.market_cap,
            }
        except Exception as e:
            log.error(f"Error fetching fundamental data for {ticker}: {e}")
            return None

    async def _generate_chart(self, ticker: str, period: str = "3mo") -> str | None:
        """Generate price chart as PNG file."""
        try:
            from pulse.core.chart_generator import ChartGenerator
            from pulse.core.data.yfinance import YFinanceFetcher

            fetcher = YFinanceFetcher()
            df = fetcher.get_history_df(ticker, period)

            if df is None or df.empty:
                return None

            dates = df.index.strftime("%Y-%m-%d").tolist()
            prices = df["close"].tolist()
            volumes = df["volume"].tolist() if "volume" in df.columns else None

            generator = ChartGenerator()
            filepath = generator.price_chart(ticker, dates, prices, volumes, period)

            return filepath
        except Exception as e:
            log.error(f"Error generating chart for {ticker}: {e}")
            return None

    async def _generate_forecast(self, ticker: str, days: int = 7) -> dict[str, Any] | None:
        """Generate price forecast with PNG chart."""
        try:
            from pulse.core.chart_generator import ChartGenerator
            from pulse.core.data.yfinance import YFinanceFetcher
            from pulse.core.forecasting import PriceForecaster

            fetcher = YFinanceFetcher()
            df = fetcher.get_history_df(ticker, "6mo")

            if df is None or df.empty:
                return None

            prices = df["close"].tolist()
            dates = df.index.strftime("%Y-%m-%d").tolist()

            forecaster = PriceForecaster()
            result = await forecaster.forecast(ticker, prices, dates, days)

            if not result:
                return None

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

            return {
                "summary": forecaster.format_forecast(result),
                "filepath": filepath,
                "result": result,
            }
        except Exception as e:
            log.error(f"Error generating forecast for {ticker}: {e}")
            return None

    async def _gather_context(
        self,
        intent: str,
        tickers: list[str],
    ) -> AgentContext:
        """
        Gather all relevant data based on intent.
        This is where we fetch REAL data before AI analysis.
        """
        ctx = AgentContext(
            intent=intent,
            tickers=tickers,
            ticker=tickers[0] if tickers else None,
        )

        if not tickers:
            return ctx

        primary_ticker = tickers[0]

        # Always fetch basic stock data
        ctx.stock_data = await self._fetch_stock_data(primary_ticker)

        if not ctx.stock_data:
            ctx.error = f"無法取得 {primary_ticker} 的資料"
            return ctx

        # Fetch additional data based on intent
        if intent in ["analyze", "technical", "recommendation"]:
            ctx.technical_data = await self._fetch_technical(primary_ticker)

        if intent in ["analyze", "fundamental", "recommendation"]:
            ctx.fundamental_data = await self._fetch_fundamental(primary_ticker)

        if intent == "compare" and len(tickers) >= 2:
            comparison = []
            for t in tickers[:4]:  # Max 4 tickers
                stock = await self._fetch_stock_data(t)
                if stock:
                    comparison.append(stock)
            ctx.comparison_data = comparison

        return ctx

    def _build_analysis_prompt(
        self,
        user_message: str,
        context: AgentContext,
    ) -> str:
        """
        Build prompt for AI with real data context.
        AI will analyze based on this real data.
        """
        parts = []

        # System context
        parts.append("你是專業的台灣股市分析師。")
        parts.append("以下是從市場取得的真實數據：")
        parts.append("")

        # Stock data
        if context.stock_data:
            s = context.stock_data
            change_sign = "+" if s.get("change", 0) >= 0 else ""
            parts.append(f"=== 股票數據: {s.get('ticker')} ===")
            parts.append(f"名稱: {s.get('name', 'N/A')}")
            parts.append(f"產業: {s.get('sector', 'N/A')}")
            parts.append(f"股價: NT$ {s.get('current_price', 0):,.2f}")
            parts.append(
                f"漲跌: {change_sign}{s.get('change', 0):,.2f} ({change_sign}{s.get('change_percent', 0):.2f}%)"
            )
            parts.append(f"成交量: {s.get('volume', 0):,.0f} (均量: {s.get('avg_volume', 0):,.0f})")
            parts.append(f"當日區間: {s.get('day_low', 0):,.2f} - {s.get('day_high', 0):,.2f}")
            parts.append(
                f"52週區間: {s.get('week_52_low', 0):,.2f} - {s.get('week_52_high', 0):,.2f}"
            )
            if s.get("market_cap"):
                mc = s["market_cap"]
                if mc >= 1e12:
                    mc_str = f"{mc / 1e12:.1f}兆"
                else:
                    mc_str = f"{mc / 1e9:.1f}億"
                parts.append(f"市值: NT$ {mc_str}")
            parts.append("")

        # Technical data
        if context.technical_data:
            t = context.technical_data
            parts.append("=== 技術指標 ===")
            if t.get("rsi_14"):
                rsi_status = "超賣" if t["rsi_14"] < 30 else "超買" if t["rsi_14"] > 70 else "中性"
                parts.append(f"RSI(14): {t['rsi_14']:.1f} - {rsi_status}")
            if t.get("macd") is not None:
                macd_status = "多頭" if t["macd"] > t.get("macd_signal", 0) else "空頭"
                parts.append(
                    f"MACD: {t['macd']:.2f} (訊號: {t.get('macd_signal', 0):.2f}) - {macd_status}"
                )
            if t.get("sma_20"):
                parts.append(f"SMA20: {t['sma_20']:,.2f} | SMA50: {t.get('sma_50', 0):,.2f}")
            if t.get("bb_upper"):
                parts.append(
                    f"布林通道: {t['bb_lower']:,.2f} - {t['bb_middle']:,.2f} - {t['bb_upper']:,.2f}"
                )
            if t.get("stoch_k"):
                parts.append(f"隨機指標: K={t['stoch_k']:.1f}, D={t['stoch_d']:.1f}")
            if t.get("support_1"):
                parts.append(f"支撐: {t['support_1']:,.2f} | 壓力: {t.get('resistance_1', 0):,.2f}")
            if t.get("trend"):
                parts.append(f"趨勢: {t['trend']} | 訊號: {t.get('signal', 'N/A')}")
            parts.append("")

        # Fundamental data
        if context.fundamental_data:
            f = context.fundamental_data
            parts.append("=== 基本面數據 ===")
            if f.get("pe_ratio"):
                parts.append(f"本益比: {f['pe_ratio']:.2f}")
            if f.get("pb_ratio"):
                parts.append(f"股價淨值比: {f['pb_ratio']:.2f}")
            if f.get("roe"):
                parts.append(f"股東權益報酬率: {f['roe']:.1f}%")
            if f.get("roa"):
                parts.append(f"資產報酬率: {f['roa']:.1f}%")
            if f.get("npm"):
                parts.append(f"淨利率: {f['npm']:.1f}%")
            if f.get("debt_to_equity"):
                parts.append(f"負債權益比: {f['debt_to_equity']:.2f}")
            if f.get("dividend_yield"):
                parts.append(f"股利殖利率: {f['dividend_yield']:.2f}%")
            if f.get("revenue_growth"):
                parts.append(f"營收成長率: {f['revenue_growth']:.1f}%")
            if f.get("earnings_growth"):
                parts.append(f"獲利成長率: {f['earnings_growth']:.1f}%")
            parts.append("")

        # Comparison data
        if context.comparison_data:
            parts.append("=== 股票比較 ===")
            parts.append(f"{'代碼':<8} {'股價':>12} {'漲跌':>10}")
            parts.append("-" * 32)
            for stock in context.comparison_data:
                change_str = f"{stock.get('change_percent', 0):+.2f}%"
                parts.append(
                    f"{stock['ticker']:<8} {stock.get('current_price', 0):>12,.2f} {change_str:>10}"
                )
            parts.append("")

        # User's actual question
        parts.append("=== 使用者問題 ===")
        parts.append(user_message)
        parts.append("")

        # Instructions
        parts.append("=== 指示 ===")
        parts.append("根據上述真實數據，提供分析時請：")
        parts.append("1. 簡潔直接（最多3-4段）")
        parts.append("2. 使用數據中的實際數字")
        parts.append("3. 提供可執行的洞察")
        parts.append("4. 如被問及建議，請根據數據說明理由")
        parts.append("5. 提及相關的支撐/壓力位")
        parts.append("")
        parts.append("不要捏造數據。僅使用上述提供的數據。")

        return "\n".join(parts)

    async def _handle_index(self, index_name: str, user_message: str) -> AgentResponse:
        """
        Handle market index queries (IHSG, LQ45, etc).
        """
        try:
            from pulse.core.chart_generator import ChartGenerator
            from pulse.core.data.yfinance import YFinanceFetcher

            fetcher = YFinanceFetcher()
            index_data = await fetcher.fetch_index(index_name)

            if not index_data:
                return AgentResponse(message=f"無法取得 {index_name} 的資料")

            # Generate chart
            df = fetcher.get_history_df(
                f"^{self.KNOWN_INDICES.get(index_name, 'JKSE').replace('^', '')}", "3mo"
            )
            chart_path = None

            if df is not None and not df.empty:
                generator = ChartGenerator()
                dates = df.index.strftime("%Y-%m-%d").tolist()
                prices = df["close"].tolist()
                chart_path = generator.price_chart(index_name, dates, prices, period="3mo")

            # Format response
            change_sign = "+" if index_data.change >= 0 else ""

            msg = f"""{index_data.name} ({index_name})

Value: {index_data.current_price:,.2f}
Change: {change_sign}{index_data.change:,.2f} ({change_sign}{index_data.change_percent:.2f}%)
Range: {index_data.day_low:,.2f} - {index_data.day_high:,.2f}
52W Range: {index_data.week_52_low:,.2f} - {index_data.week_52_high:,.2f}"""

            if chart_path:
                msg += f"\n\nChart saved: {chart_path}"

            # Add AI analysis if user asked a question
            if any(
                w in user_message.lower()
                for w in ["怎麼樣", "如何", "狀況", "分析", "什麼"]
            ):
                ai = self._get_ai_client()
                ai_prompt = f"""資料 {index_name}:
- 數值: {index_data.current_price:,.2f}
- 變化: {index_data.change_percent:+.2f}%
- 52週區間: {index_data.week_52_low:,.2f} - {index_data.week_52_high:,.2f}

使用者詢問: "{user_message}"

請提供簡短分析（2-3句話）關於 {index_name} 的現況。"""

                ai_response = await ai.chat(
                    ai_prompt,
                    system_prompt="你是專業的台灣市場分析師。簡潔且切中要點地回答。",
                    use_history=False,
                )
                msg = f"{ai_response}\n\n---\n\n{msg}"

            return AgentResponse(message=msg, chart=chart_path)

        except Exception as e:
            log.error(f"Error handling index {index_name}: {e}")
            return AgentResponse(message=f"Error: {e}")

    async def _handle_screen(self, user_message: str) -> AgentResponse:
        """
        Handle stock screening request.

        Uses SmartScreener to find stocks matching criteria,
        then returns formatted results with AI explanation.
        """
        try:
            from pulse.core.screener import StockScreener, StockUniverse

            msg_lower = user_message.lower()

            # Determine universe based on message
            if any(kw in msg_lower for kw in ["全部", "all", "955", "所有"]):
                screener = StockScreener(universe_type=StockUniverse.ALL)
                universe_note = f"(掃描 {len(screener.universe)} 檔股票)"
            elif any(kw in msg_lower for kw in ["idx80", "80"]):
                screener = StockScreener(universe_type=StockUniverse.IDX80)
                universe_note = "(IDX80)"
            elif any(kw in msg_lower for kw in ["lq45", "lq"]):
                screener = StockScreener(universe_type=StockUniverse.LQ45)
                universe_note = "(LQ45)"
            else:
                # Default to POPULAR (113 stocks)
                screener = StockScreener(universe_type=StockUniverse.POPULAR)
                universe_note = f"(scanning {len(screener.universe)} stocks)"

            # Use smart screening for natural language
            results, explanation = await screener.smart_screen(user_message, limit=15)

            if not results:
                return AgentResponse(
                    message=f"找不到符合條件的股票 {universe_note}。\n\n條件: {explanation}"
                )

            # Format results
            formatted = screener.format_results(
                results,
                title=f"Stock Screening Results {universe_note}",
                show_details=True,
            )

            # Add explanation
            msg = f"{explanation}\n\n{formatted}"

            # Generate AI summary
            ai = self._get_ai_client()

            # Build summary of top picks for AI
            top_picks = []
            for r in results[:5]:
                rsi_str = f"{r.rsi_14:.1f}" if r.rsi_14 else "N/A"
                # Include market cap info
                mc_str = ""
                if hasattr(r, "market_cap") and r.market_cap:
                    mc = r.market_cap
                    if mc >= 1e12:
                        mc_str = f", MCap: {mc / 1e12:.1f}T"
                    else:
                        mc_str = f", MCap: {mc / 1e9:.0f}B"

                top_picks.append(
                    f"- {r.ticker}: NT$ {r.price:,.0f} ({r.change_percent:+.2f}%), "
                    f"RSI: {rsi_str}, "
                    f"評分: {r.score:.0f}{mc_str}"
                )

            ai_prompt = f"""使用者詢問: "{user_message}"

篩選結果 ({explanation}):
{chr(10).join(top_picks)}

請提供簡短摘要（2-3句話）關於這次篩選結果。
請指出哪支股票最具吸引力，並說明原因。"""

            ai_summary = await ai.chat(
                ai_prompt,
                system_prompt="你是股票分析師。請提供簡短的篩選結果摘要。",
                use_history=False,
            )

            msg = f"{ai_summary}\n\n---\n\n{formatted}"

            return AgentResponse(message=msg)

        except Exception as e:
            log.error(f"Screen error: {e}")
            return AgentResponse(message=f"篩選時發生錯誤: {e}")

    async def _handle_trading_plan(self, ticker: str, user_message: str) -> AgentResponse:
        """
        Generate trading plan with TP, SL, and Risk/Reward for a ticker.
        """
        try:
            from pulse.core.trading_plan import TradingPlanGenerator

            self._last_ticker = ticker  # Remember for follow-ups

            generator = TradingPlanGenerator()
            plan = await generator.generate(ticker)

            if not plan:
                return AgentResponse(
                    message=f"無法為 {ticker} 建立交易計畫。請確認代碼有效。"
                )

            # Format the trading plan
            formatted = generator.format_plan(plan)

            # Add AI commentary
            ai = self._get_ai_client()

            # Build context for AI
            ai_prompt = f"""交易計畫 {ticker}:
進場: NT$ {plan.entry_price:,.0f}
TP1: NT$ {plan.tp1:,.0f} ({plan.tp1_percent:+.2f}%)
停損: NT$ {plan.stop_loss:,.0f} ({plan.stop_loss_percent:.2f}%)
R:R 比率: 1:{plan.rr_ratio_tp1:.1f}
交易品質: {plan.trade_quality.value}
趋勢: {plan.trend.value}
訊號: {plan.signal.value}
RSI: {plan.rsi}
信心: {plan.confidence}%

使用者詢問: "{user_message}"

請提供簡短評論（2-3句話）關於這個交易計畫。
這個交易值得執行嗎？需要注意什麼？"""

            ai_comment = await ai.chat(
                ai_prompt,
                system_prompt=(
                    "你是專業的台灣股票交易員。"
                    "請提供簡短且可執行的交易計畫評論。"
                    "請專注於這筆交易是否值得執行以及風險所在。"
                ),
                use_history=False,
            )

            # Combine AI comment with formatted plan
            msg = f"{ai_comment}\n\n---\n\n{formatted}"

            return AgentResponse(
                message=msg,
                raw_data={"trading_plan": plan.model_dump()},
            )

        except Exception as e:
            log.error(f"Trading plan error for {ticker}: {e}")
            return AgentResponse(message=f"建立交易計畫時發生錯誤: {e}")

    async def _handle_sapta(self, ticker: str, user_message: str) -> AgentResponse:
        """
        Run SAPTA PRE-MARKUP analysis for a ticker.
        """
        try:
            from pulse.core.sapta import SaptaEngine

            self._last_ticker = ticker  # Remember for follow-ups

            engine = SaptaEngine()
            result = await engine.analyze(ticker)

            if not result:
                return AgentResponse(
                    message=f"無法執行 {ticker} 的 SAPTA 分析。請確認代碼有效。"
                )

            # Format the SAPTA result
            formatted = engine.format_result(result, detailed=True)

            # Add AI commentary for interpretation
            ai = self._get_ai_client()

            notes_str = (
                "\n".join(f"- {n}" for n in result.notes[:5])
                if result.notes
                else "沒有特別訊號"
            )

            ai_prompt = f"""SAPTA 分析 {ticker}:
狀態: {result.status.value}
評分: {result.final_score:.1f}/100
信心: {result.confidence.value}
波段: {result.wave_phase or "N/A"}

偵測到的訊號:
{notes_str}

使用者詢問: "{user_message}"

請提供簡短解釋（2-3句話）關於 SAPTA 分析結果。
{ticker} 值得購買嗎？什麼時機最適合？"""

            ai_comment = await ai.chat(
                ai_prompt,
                system_prompt=(
                    "你是專業的技術分析師，擅長偵測突破前期。"
                    "請提供簡短且可執行的解釋。"
                    "請專注於這支股票是否準備突破以及時機。"
                ),
                use_history=False,
            )

            # Combine AI comment with formatted result
            msg = f"{ai_comment}\n\n---\n\n{formatted}"

            return AgentResponse(
                message=msg,
                raw_data={"sapta_result": result.to_dict()},
            )

        except Exception as e:
            log.error(f"SAPTA analysis error for {ticker}: {e}")
            return AgentResponse(message=f"SAPTA 分析錯誤: {e}")

    async def _handle_sapta_scan(self, user_message: str) -> AgentResponse:
        """
        掃描股票尋找 SAPTA PRE-MARKUP 候選標的。

        支援：
        - 台灣50、中型100、熱門股等分類
        - "全部" 或 "all" 掃描資料庫中所有上市櫃股票
        """
        try:
            from pulse.core.sapta import SaptaEngine, SaptaStatus
            from pulse.core.screener import StockScreener, StockUniverse

            engine = SaptaEngine()

            # 依據訊息判斷掃描範圍
            msg_lower = user_message.lower()

            # 檢查是否要掃描全部股票
            if any(kw in msg_lower for kw in ["全部", "all", "所有", "全部股票", "上市櫃"]):
                try:
                    from pulse.core.sapta.ml.data_loader import SaptaDataLoader

                    loader = SaptaDataLoader()
                    tickers = loader.get_all_tickers()
                    universe_name = f"全部 ({len(tickers)} 支股票)"
                    # 大規模掃描時，使用 SIAP 作為最低標準以減少雜訊
                    min_status = SaptaStatus.SIAP
                except Exception:
                    # 若資料庫不可用，回退到熱門股
                    screener = StockScreener(universe_type=StockUniverse.POPULAR)
                    tickers = screener.universe
                    universe_name = "熱門股"
                    min_status = SaptaStatus.WATCHLIST
            elif any(kw in msg_lower for kw in ["中型100", "中型", "100"]):
                screener = StockScreener(universe_type=StockUniverse.IDX80)
                tickers = screener.universe
                universe_name = "中型100"
                min_status = SaptaStatus.WATCHLIST
            elif any(kw in msg_lower for kw in ["熱門", "popular", "活躍"]):
                screener = StockScreener(universe_type=StockUniverse.POPULAR)
                tickers = screener.universe
                universe_name = "熱門股"
                min_status = SaptaStatus.WATCHLIST
            else:
                # 預設使用台灣50進行快速掃描
                screener = StockScreener(universe_type=StockUniverse.LQ45)
                tickers = screener.universe
                universe_name = "台灣50"
                min_status = SaptaStatus.WATCHLIST

            # 執行掃描
            results = await engine.scan(tickers, min_status=min_status)

            if not results:
                return AgentResponse(
                    message=f"在 {universe_name} 找不到符合 SAPTA 標準（WATCHLIST 或更高）的股票。"
                )

            # 格式化結果
            formatted = engine.format_scan_results(
                results, title=f"SAPTA 篩選: {universe_name} (找到 {len(results)} 支)"
            )

            # Add AI summary
            ai = self._get_ai_client()

            top_picks = []
            for r in results[:5]:
                top_picks.append(
                    f"- {r.ticker}: {r.status.value}, Score: {r.final_score:.0f}, "
                    f"Wave: {r.wave_phase or 'N/A'}"
                )

            ai_prompt = f"""SAPTA 篩選結果 {universe_name}:
{chr(10).join(top_picks)}

總計: {len(results)} 支股票符合標準。

使用者詢問: "{user_message}"

請提供簡短摘要（2-3句話）關於這次篩選結果。
哪支股票最值得關注？"""

            ai_summary = await ai.chat(
                ai_prompt,
                system_prompt="你是技術分析師。請提供 SAPTA 篩選結果的簡短摘要。",
                use_history=False,
            )

            msg = f"{ai_summary}\n\n---\n\n{formatted}"

            return AgentResponse(message=msg)

        except Exception as e:
            log.error(f"SAPTA scan error: {e}")
            return AgentResponse(message=f"SAPTA 篩選錯誤: {e}")

    async def run(self, user_message: str) -> AgentResponse:
        """
        Main entry point - run the agentic flow.

        1. Parse intent & extract tickers
        2. Use last ticker if none found (for follow-up questions)
        3. Fetch real data
        4. Build context
        5. AI analyzes with context (with history for follow-ups)
        6. Return response
        """
        log.info(f"SmartAgent processing: {user_message}")

        # Step 1: Detect intent and extract tickers
        intent, tickers = self._detect_intent(user_message)
        log.info(f"Detected intent: {intent}, tickers: {tickers}")

        # Step 2: If no tickers found but we have last context, this might be a follow-up
        is_followup = False
        if not tickers and self._last_ticker and intent == "general":
            # Check if this looks like a follow-up question
            followup_patterns = [
                r"為什麼",
                r"為何",
                r"怎麼",
                r"如何",
                r"然後",
                r"接著",
                r"那麼",
                r"所以",
                r"是否",
                r"什麼是",
                r"意思",
                r"比較",
                r"差異",
                r"上漲",
                r"下跌",
                r"support",
                r"resistance",
                r"目標",
            ]
            msg_lower = user_message.lower()
            for pattern in followup_patterns:
                if pattern in msg_lower:
                    is_followup = True
                    tickers = [self._last_ticker]
                    log.info(f"Follow-up detected, using last ticker: {self._last_ticker}")
                    break

        # If no stock-related intent and not a follow-up, let AI handle with history
        if intent == "general" and not tickers and not is_followup:
            ai = self._get_ai_client()
            response = await ai.chat(
                user_message,
                system_prompt=(
                    "你是 Pulse，台灣股市分析助理。"
                    "如果使用者詢問與台灣股市無關的事項，"
                    "請禮貌地拒絕並引導回 TWSE/TPEx 股票主題。"
                    "簡短回答，1-2句話內。"
                ),
                use_history=True,  # Enable history for context
            )
            return AgentResponse(message=response)

        # Handle index intent (IHSG, LQ45, etc)
        if intent == "index" and tickers:
            return await self._handle_index(tickers[0], user_message)

        # Handle chart intent directly
        if intent == "chart" and tickers:
            ticker = tickers[0]
            self._last_ticker = ticker  # Remember this ticker
            filepath = await self._generate_chart(ticker)
            stock = await self._fetch_stock_data(ticker)

            if filepath and stock:
                msg = f"""{ticker}: NT$ {stock["current_price"]:,.0f} ({stock["change"]:+,.0f}, {stock["change_percent"]:+.2f}%)

Chart saved: {filepath}"""
                return AgentResponse(message=msg, chart=filepath)
            return AgentResponse(message=f"無法為 {ticker} 建立圖表")

        # Handle forecast intent directly
        if intent == "forecast" and tickers:
            ticker = tickers[0]
            self._last_ticker = ticker  # Remember this ticker
            forecast = await self._generate_forecast(ticker)

            if forecast:
                msg = forecast["summary"]
                if forecast.get("filepath"):
                    msg += f"\n\nChart saved: {forecast['filepath']}"
                return AgentResponse(message=msg, chart=forecast.get("filepath"))
            return AgentResponse(message=f"無法為 {ticker} 建立預測")

        # Handle screen intent - smart stock screening
        if intent == "screen":
            return await self._handle_screen(user_message)

        # Handle trading plan intent
        if intent == "trading_plan" and tickers:
            return await self._handle_trading_plan(tickers[0], user_message)

        # Handle SAPTA intent
        if intent == "sapta" and tickers:
            return await self._handle_sapta(tickers[0], user_message)

        # Handle SAPTA scan intent
        if intent == "sapta_scan":
            return await self._handle_sapta_scan(user_message)

        # Step 3 & 4: Gather real data
        context = await self._gather_context(intent, tickers)

        if context.error:
            return AgentResponse(
                message=context.error,
                context=context,
            )

        # Remember context for follow-ups
        if tickers:
            self._last_ticker = tickers[0]
            self._last_context = context

        # Step 5: Build prompt with real data and get AI analysis
        analysis_prompt = self._build_analysis_prompt(user_message, context)

        ai = self._get_ai_client()

        # For follow-up questions, include previous context
        if is_followup and self._last_context:
            analysis_prompt = (
                f"[之前的背景: 分析 {self._last_ticker}]\n\n" + analysis_prompt
            )

        ai_response = await ai.chat(
            analysis_prompt,
            system_prompt=(
                "你是資深的台灣股市分析師。"
                "根據提供的真實數據進行分析。"
                "使用繁體中文回答，簡潔且切中要點。"
                "不要編造數據 - 只使用提供的數據。"
            ),
            use_history=True,  # Enable history for follow-up context
        )

        # Generate chart for analysis intent too
        chart_filepath = None
        if intent in ["analyze", "technical"] and tickers:
            chart_filepath = await self._generate_chart(tickers[0])

        # Append chart info to response if generated
        final_message = ai_response
        if chart_filepath:
            final_message += f"\n\nChart saved: {chart_filepath}"

        # Step 6: Return response
        return AgentResponse(
            message=final_message,
            context=context,
            chart=chart_filepath,
            raw_data={
                "intent": intent,
                "tickers": tickers,
                "stock_data": context.stock_data,
                "technical_data": context.technical_data,
                "fundamental_data": context.fundamental_data,
            },
        )
