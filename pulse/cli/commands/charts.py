"""Chart commands: chart, forecast, taiex."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pulse.cli.app import PulseApp


async def chart_command(app: "PulseApp", args: str) -> str:
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

    from pulse.utils.rich_output import ICONS, get_trend_icon

    trend_icon = get_trend_icon(change_pct)
    return f"""{trend_icon} {ticker}: NT$ {current:,.2f} ({change:+,.2f}, {change_pct:+.2f}%)

{ICONS["chart"]} 圖表已儲存: {filepath}"""


async def forecast_command(app: "PulseApp", args: str) -> str:
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

    # Format summary using rich_output
    from pulse.utils.rich_output import create_forecast_table

    current = prices[-1]
    target = result.target_price

    return create_forecast_table(
        ticker=ticker,
        current=current,
        target=target,
        support=result.support,
        resistance=result.resistance,
        confidence=result.confidence,
        days=days,
        chart_path=filepath,
    )


async def taiex_command(app: "PulseApp", args: str) -> str:
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

    # Format response using rich_output
    from pulse.utils.rich_output import create_index_table

    return create_index_table(
        name=index_data.name,
        index_name=index_name,
        price=index_data.current_price,
        change=index_data.change,
        change_pct=index_data.change_percent,
        day_low=index_data.day_low,
        day_high=index_data.day_high,
        week_52_low=index_data.week_52_low,
        week_52_high=index_data.week_52_high,
        chart_path=chart_path,
    )
