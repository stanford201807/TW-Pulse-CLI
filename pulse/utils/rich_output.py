"""Rich output formatting utilities for Pulse CLI.

Provides consistent, beautiful terminal output.
"""

import sys


# Check if we can use emojis (not on Windows cp950/gbk)
def _can_use_emoji() -> bool:
    """Check if terminal supports emoji."""
    try:
        # Handle cases where sys.stdout might be replaced (e.g., Textual's _PrintCapture)
        encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        "📈".encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError, AttributeError):
        return False


USE_EMOJI = _can_use_emoji()

# Icon mappings with fallbacks
ICONS = {
    "up": "📈" if USE_EMOJI else "+",
    "down": "📉" if USE_EMOJI else "-",
    "neutral": "➡️" if USE_EMOJI else "=",
    "green": "🟢" if USE_EMOJI else "+",
    "red": "🔴" if USE_EMOJI else "-",
    "yellow": "🟡" if USE_EMOJI else "!",
    "white": "⚪" if USE_EMOJI else "o",
    "check": "✅" if USE_EMOJI else "v",
    "box": "⬜" if USE_EMOJI else " ",
    "warn": "⚠️" if USE_EMOJI else "!",
    "chart": "📊" if USE_EMOJI else "#",
    "rocket": "🚀" if USE_EMOJI else "*",
    "eye": "👀" if USE_EMOJI else "?",
    "skip": "⏭️" if USE_EMOJI else ">",
    "bullet": "•" if USE_EMOJI else "*",
}


def create_header(title: str, ticker: str = "") -> str:
    """Create a styled header."""
    if ticker:
        return f"=== {title}: {ticker} ==="
    return f"=== {title} ==="


def create_progress_bar(value: float, max_value: float = 100, width: int = 10) -> str:
    """Create a text-based progress bar."""
    if max_value == 0:
        return "-" * width

    ratio = min(value / max_value, 1.0)
    filled = int(width * ratio)
    empty = width - filled

    return "#" * filled + "-" * empty


def get_trend_icon(value: float) -> str:
    """Get trend icon based on value."""
    if value > 0:
        return ICONS["up"]
    elif value < 0:
        return ICONS["down"]
    return ICONS["neutral"]


def create_technical_table(ticker: str, indicators: list[dict]) -> str:
    """Create a formatted technical analysis output."""
    lines = [create_header("技術分析", ticker), ""]

    # Group indicators by category
    categories = {
        "趨勢指標": ["SMA", "EMA", "Trend"],
        "動能指標": ["RSI", "MACD", "Stochastic"],
        "波動指標": ["BB", "ATR"],
        "成交量": ["Volume", "OBV", "MFI"],
        "支撐壓力": ["Support", "Resistance"],
    }

    # Status translation
    status_map = {
        "Overbought": "超買",
        "Oversold": "超賣",
        "Bullish": "多頭",
        "Bearish": "空頭",
        "Neutral": "中性",
        "Strong": "強勢",
        "Weak": "弱勢",
    }

    current_category = ""

    for item in indicators:
        name = item.get("name", "")
        value = item.get("value", "")
        status = item.get("status", "")

        # Determine category
        for cat, keywords in categories.items():
            if any(kw.lower() in name.lower() for kw in keywords):
                if cat != current_category:
                    current_category = cat
                    lines.append(f"\n[{cat}]")
                break

        status_zh = status_map.get(status, status)
        if status_zh:
            lines.append(f"  {name}: {value} ({status_zh})")
        else:
            lines.append(f"  {name}: {value}")

    return "\n".join(lines)


def create_fundamental_table(ticker: str, summary: list[dict], score: int) -> str:
    """Create a formatted fundamental analysis output."""
    lines = [create_header("基本面分析", ticker), ""]

    # Score bar
    score_bar = create_progress_bar(score, 100, 10)
    lines.append(f"估值評分: [{score_bar}] {score}/100")
    lines.append("")

    # Category mapping
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

    current_category = ""

    for item in summary:
        cat = item.get("category", "")
        if cat != current_category:
            current_category = cat
            cat_zh = category_map.get(cat, cat)
            lines.append(f"\n[{cat_zh}]")

        name = item.get("name", "")
        value = item.get("value", "")
        status = item.get("status", "")

        status_zh = status_map.get(status, status)
        if status_zh:
            lines.append(f"  {name}: {value} ({status_zh})")
        else:
            lines.append(f"  {name}: {value}")

    return "\n".join(lines)


def create_sapta_table(result) -> str:
    """Create a formatted SAPTA analysis output."""
    lines = [create_header("SAPTA 分析", result.ticker), ""]

    # Status
    status_str = result.status.value if hasattr(result.status, 'value') else str(result.status)

    # Score bar
    score = result.total_score
    score_bar = create_progress_bar(score, 100, 10)

    lines.append(f"狀態: {status_str}")
    lines.append(f"總分: [{score_bar}] {score:.0f}/100")
    lines.append("")

    # Module scores
    lines.append("[模組分數]")

    modules = [
        ("absorption", "供給吸收", result.absorption),
        ("compression", "價格壓縮", result.compression),
        ("bb_squeeze", "布林擠壓", result.bb_squeeze),
        ("elliott", "艾略特波浪", result.elliott),
        ("time_projection", "時間投影", result.time_projection),
        ("anti_distribution", "反派發", result.anti_distribution),
    ]

    for key, name, data in modules:
        if data:
            mod_score = data.get("score", 0)
            max_score = data.get("max_score", 15)
            bar = create_progress_bar(mod_score, max_score, 8)
            status_mark = "v" if data.get("status", False) else " "
            lines.append(f"  {name}: [{bar}] {mod_score:.0f}/{max_score:.0f} [{status_mark}]")

    # Signals
    lines.append("\n[訊號]")
    all_signals = []
    for _, _, data in modules:
        if data and data.get("signals"):
            all_signals.extend(data["signals"])

    for signal in all_signals[:8]:
        lines.append(f"  * {signal}")

    # Warnings
    if result.warnings:
        lines.append("\n[警告]")
        for warning in result.warnings:
            lines.append(f"  ! {warning}")

    return "\n".join(lines)


def create_screen_table(results: list[dict], title: str) -> str:
    """Create a formatted screening results output."""
    lines = [create_header("股票篩選", ""), ""]
    lines.append(f"{title}")
    lines.append("")

    if not results:
        lines.append("找不到符合條件的股票")
        return "\n".join(lines)

    for i, r in enumerate(results[:20], 1):
        ticker = r.get("ticker", "")
        price = r.get("price", 0)
        change = r.get("change_percent", 0)
        rsi = r.get("rsi", 0)
        signal = r.get("signal", "")

        change_str = f"{change:+.2f}%"
        rsi_str = f"RSI:{rsi:.1f}" if rsi else ""

        # Signal indicator
        if "bullish" in signal.lower():
            signal_str = "(多頭)"
        elif "bearish" in signal.lower():
            signal_str = "(空頭)"
        else:
            signal_str = ""

        lines.append(f"{i:2}. {ticker} - NT${price:,.0f} {change_str} {rsi_str} {signal_str}")

    if len(results) > 20:
        lines.append(f"\n... 還有 {len(results) - 20} 檔股票")

    return "\n".join(lines)


def create_compare_table(results: list[dict]) -> str:
    """Create a formatted stock comparison output."""
    lines = [create_header("股票比較", ""), ""]

    for r in results:
        ticker = r.get("ticker", "")
        name = r.get("name", "")
        price = r.get("price", 0)
        change = r.get("change_pct", 0)
        volume = r.get("volume", 0)

        change_str = f"{change:+.2f}%"
        trend = ICONS["up"] if change >= 0 else ICONS["down"]

        lines.append(f"{trend} {ticker} ({name})")
        lines.append(f"   股價: NT$ {price:,.0f}")
        lines.append(f"   漲跌: {change_str}")
        lines.append(f"   成交量: {volume:,.0f}")
        lines.append("")

    return "\n".join(lines)


def create_forecast_table(ticker: str, current: float, target: float,
                          support: float, resistance: float,
                          confidence: float, days: int, chart_path: str = None) -> str:
    """Create a formatted forecast output."""
    change_pct = (target - current) / current * 100
    trend = "上漲" if change_pct > 0 else "下跌" if change_pct < 0 else "盤整"
    trend_icon = get_trend_icon(change_pct)
    change_sign = "+" if change_pct > 0 else ""

    # Confidence bar
    conf_bar = create_progress_bar(confidence, 100, 10)

    lines = [
        create_header("價格預測", f"{ticker} ({days}天)"),
        "",
        f"現價: NT$ {current:,.2f}",
        f"目標價: NT$ {target:,.2f}",
        f"預期漲跌: {change_sign}{change_pct:.2f}%",
        "",
        f"趨勢: {trend_icon} {trend}",
        f"支撐位: NT$ {support:,.2f}",
        f"壓力位: NT$ {resistance:,.2f}",
        f"信心度: [{conf_bar}] {confidence:.0f}%",
    ]

    if chart_path:
        lines.append(f"\n圖表已儲存: {chart_path}")

    return "\n".join(lines)


def create_index_table(name: str, index_name: str, price: float, change: float,
                       change_pct: float, day_low: float, day_high: float,
                       week_52_low: float, week_52_high: float,
                       chart_path: str = None) -> str:
    """Create a formatted index output."""
    change_sign = "+" if change >= 0 else ""
    trend_icon = get_trend_icon(change)
    trend = "上漲" if change >= 0 else "下跌"

    lines = [
        create_header(name, index_name),
        "",
        f"指數: {price:,.2f}",
        f"漲跌: {change_sign}{change:,.2f}",
        f"漲跌幅: {change_sign}{change_pct:.2f}%",
        "",
        f"今日最高: {day_high:,.2f}",
        f"今日最低: {day_low:,.2f}",
        f"52週最高: {week_52_high:,.2f}",
        f"52週最低: {week_52_low:,.2f}",
        "",
        f"趨勢: {trend_icon} {trend}",
    ]

    if chart_path:
        lines.append(f"\n圖表已儲存: {chart_path}")

    return "\n".join(lines)
