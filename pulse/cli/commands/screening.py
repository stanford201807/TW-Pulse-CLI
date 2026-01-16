"""Screening commands: screen, compare, export."""

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pulse.cli.app import PulseApp
    from pulse.core.screener import ScreenResult


async def screen_command(app: "PulseApp", args: str) -> str:
    """Screen stocks based on technical/fundamental criteria."""
    if not args:
        return """Stock Screening (股票篩選)

Usage: /screen <criteria> [--universe=tw50|midcap|popular] [--export[=filename]]

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

Export (導出):
  --export            - 導出到 data/reports/screen_YYYYMMDD_HHMMSS.csv
  --export=filename   - 導出到指定檔名 (含副檔名)

Example (範例):
  /screen oversold --universe=tw50 --export
  /screen rsi<30 --export=my_screening.csv
  /screen bullish --universe=all --export
"""

    from pulse.core.screener import ScreenPreset, StockScreener, StockUniverse

    # Parse universe option
    universe_type = None
    export_filename = None
    criteria_str = args

    # Parse --export option
    if "--export" in args.lower():
        export_match = re.search(r"--export(?:=(.+))?", args.lower())
        if export_match:
            export_filename = export_match.group(1)  # None if just --export without =
        criteria_str = re.sub(r"\s*--export(?:=\S+)?", "", args).strip()

    # Parse universe option
    if "--universe=" in args.lower():
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
            criteria_str = re.sub(r"\s*--universe=\w+", "", criteria_str).strip()

    # Create screener with proper universe
    screener = StockScreener(universe_type=universe_type)
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

    # Convert ScreenResult to dict format for rich_output
    from pulse.utils.rich_output import create_screen_table

    result_dicts = []
    for r in results:
        signal = ""
        if r.rsi_status:
            signal = (
                "bullish"
                if "oversold" in r.rsi_status.lower()
                else "bearish"
                if "overbought" in r.rsi_status.lower()
                else ""
            )
        if not signal and r.macd_status:
            signal = (
                "bullish"
                if "bullish" in r.macd_status.lower()
                else "bearish"
                if "bearish" in r.macd_status.lower()
                else ""
            )

        result_dicts.append(
            {
                "ticker": r.ticker,
                "price": r.price,
                "change_percent": r.change_percent,
                "rsi": r.rsi_14,
                "signal": signal,
            }
        )

    # Create display output
    output = create_screen_table(result_dicts, title)

    # Export to CSV if requested
    if export_filename:
        try:
            csv_path = export_results_to_csv(results, export_filename)
            output += f"\n\n已導出 CSV: {csv_path}"
        except Exception as e:
            output += f"\n\n導出失敗: {e}"

    return output


async def compare_command(app: "PulseApp", args: str) -> str:
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

    from pulse.utils.rich_output import create_compare_table

    return create_compare_table(results)


def export_results_to_csv(results: list["ScreenResult"], filename: str | None = None) -> str:
    """Export screening results to CSV file.

    Args:
        results: List of ScreenResult objects
        filename: Optional filename. If not provided, generates one with timestamp.

    Returns:
        Path to the exported CSV file
    """
    if not results:
        raise ValueError("No results to export")

    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screen_results_{timestamp}.csv"

    # Ensure reports directory exists
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    filepath = reports_dir / filename

    # Define CSV columns
    fieldnames = [
        "ticker",
        "name",
        "sector",
        "price",
        "change_percent",
        "volume",
        "rsi_14",
        "macd",
        "macd_signal",
        "sma_20",
        "sma_50",
        "pe_ratio",
        "pb_ratio",
        "roe",
        "dividend_yield",
        "market_cap",
        "score",
        "signals",
    ]

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            row = {
                "ticker": r.ticker,
                "name": r.name or "",
                "sector": r.sector or "",
                "price": r.price,
                "change_percent": r.change_percent,
                "volume": r.volume,
                "rsi_14": r.rsi_14,
                "macd": r.macd,
                "macd_signal": r.macd_signal,
                "sma_20": r.sma_20,
                "sma_50": r.sma_50,
                "pe_ratio": r.pe_ratio,
                "pb_ratio": r.pb_ratio,
                "roe": r.roe,
                "dividend_yield": r.dividend_yield,
                "market_cap": r.market_cap,
                "score": r.score,
                "signals": "; ".join(r.signals) if r.signals else "",
            }
            writer.writerow(row)

    return str(filepath)
