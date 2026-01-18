"""Analysis commands: analyze, technical, fundamental."""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pulse.cli.app import PulseApp


async def analyze_command(app: "PulseApp", args: str) -> str:
    """Analyze command handler."""
    if not args:
        return "請指定股票代碼。用法: /analyze 2330 (台積電)"

    ticker = args.strip().upper()

    from pulse.core.analysis.fundamental import FundamentalAnalyzer
    from pulse.core.analysis.institutional_flow import InstitutionalFlowAnalyzer
    from pulse.core.analysis.technical import TechnicalAnalyzer
    from pulse.core.data.yfinance import YFinanceFetcher

    fetcher = YFinanceFetcher()
    stock = await fetcher.fetch_stock(ticker)

    if not stock:
        return f"無法取得 {ticker} 的資料"

    # Fetch all data in parallel
    tech_analyzer = TechnicalAnalyzer()
    fundamental_analyzer = FundamentalAnalyzer()
    broker_analyzer = InstitutionalFlowAnalyzer()

    technical, fundamental, broker = await asyncio.gather(
        tech_analyzer.analyze(ticker),
        fundamental_analyzer.analyze(ticker),
        broker_analyzer.analyze(ticker),
    )

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
        "fundamental": fundamental.to_summary() if fundamental else None,
        "broker": broker if broker else None,
    }

    response = await app.ai_client.analyze_stock(ticker, data)

    return response


async def technical_command(app: "PulseApp", args: str) -> str:
    """Technical analysis command handler."""
    if not args:
        return "請指定股票代碼。用法: /technical 2330 (台積電)"

    ticker = args.strip().upper()

    from pulse.core.analysis.technical import TechnicalAnalyzer
    from pulse.utils.rich_output import create_technical_table

    analyzer = TechnicalAnalyzer()
    indicators = await analyzer.analyze(ticker)

    if not indicators:
        return f"無法分析 {ticker}，請確認股票代碼是否正確"

    summary = analyzer.get_indicator_summary(indicators)
    return create_technical_table(ticker, summary)


async def fundamental_command(app: "PulseApp", args: str) -> str:
    """Fundamental analysis command handler."""
    if not args:
        return "請指定股票代碼。用法: /fundamental 2330 (台積電)"

    ticker = args.strip().upper()

    from pulse.core.analysis.fundamental import FundamentalAnalyzer
    from pulse.utils.rich_output import create_fundamental_table

    analyzer = FundamentalAnalyzer()
    data = await analyzer.analyze(ticker)

    if not data:
        return f"無法取得 {ticker} 的基本面資料"

    summary = analyzer.get_summary(data)
    score_data = analyzer.score_valuation(data)

    return create_fundamental_table(ticker, summary, score_data["score"])
