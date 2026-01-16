"""Rich output formatting utilities for Pulse CLI.

Provides consistent, beautiful terminal output.
"""

import sys
from typing import Any

# Type definitions for better type checking
ScreenResultDict = dict[str, Any]
CompareResultDict = dict[str, Any]
TechnicalIndicatorDict = dict[str, Any]


# Check if we can use emojis (not on Windows cp950/gbk)
def _can_use_emoji() -> bool:
    """Check if terminal supports emoji."""
    try:
        # Handle cases where sys.stdout might be replaced (e.g., Textual's _PrintCapture)
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
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


def create_technical_table(ticker: str, indicators: list[TechnicalIndicatorDict]) -> str:
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


def create_sapta_table(
    result,
    detailed: bool = False,
    current_price: float | None = None,
    recent_high: float | None = None,
    support_level: float | None = None,
) -> str:
    """Create a formatted SAPTA analysis output with Chinese interpretation.

    Args:
        result: SaptaResult object with analysis data
        detailed: If True, show additional details like price targets, support levels, ML probability
        current_price: Current stock price (for detailed mode)
        recent_high: Recent high price (for price target calculation)
        support_level: Support level (for detailed mode)
    """
    lines = []

    # === 1. 開頭摘要 ===
    status_str = result.status.value if hasattr(result.status, "value") else str(result.status)
    score = result.total_score

    # 狀態翻譯
    status_translation = {
        "PRE-MARKUP": ("PRE-MARKUP", "●", "準備突破"),
        "SIAP": ("SIAP", "●", "接近突破"),
        "WATCHLIST": ("WATCHLIST", "●", "觀察中"),
        "SKIP": ("SKIP", "○", "跳過"),
    }
    status_en, status_icon, status_zh = status_translation.get(
        status_str, (status_str, "○", status_str)
    )

    # 信心度
    if score >= 70:
        confidence = "★★★★★"
        confidence_zh = "極高"
    elif score >= 55:
        confidence = "★★★★☆"
        confidence_zh = "高"
    elif score >= 40:
        confidence = "★★★☆☆"
        confidence_zh = "中等"
    else:
        confidence = "★★☆☆☆"
        confidence_zh = "偏低"

    lines.append(f"SAPTA 分析: {result.ticker}")
    lines.append(f"狀態: {status_icon} {status_en} ({status_zh}) - {score:.0f}/100")
    lines.append(f"信心度: {confidence} ({confidence_zh})")

    # === 詳細模式：價格與目標 ===
    if detailed:
        if current_price is not None:
            lines.append(f"現價: {current_price:,.0f}")

            # 計算價格目標
            if status_en == "PRE-MARKUP":
                # 突破在即，目標為近期高點 + 預期漲幅
                if recent_high and recent_high > current_price:
                    target1 = recent_high
                    target2 = recent_high * 1.08
                else:
                    target1 = current_price * 1.08
                    target2 = current_price * 1.15
                stop_loss = current_price * 0.97
            elif status_en == "SIAP":
                target1 = current_price * 1.10
                target2 = current_price * 1.20
                stop_loss = current_price * 0.97
            elif status_en == "WATCHLIST":
                target1 = current_price * 1.15
                target2 = current_price * 1.25
                stop_loss = current_price * 0.95
            else:  # SKIP
                target1 = current_price * 1.05
                target2 = current_price * 1.10
                stop_loss = current_price * 0.95

            lines.append(f"目標1: {target1:,.0f} (+{(target1 / current_price - 1) * 100:.1f}%)")
            lines.append(f"目標2: {target2:,.0f} (+{(target2 / current_price - 1) * 100:.1f}%)")
            lines.append(f"停損: {stop_loss:,.0f} ({(stop_loss / current_price - 1) * 100:.1f}%)")

    # === 詳細模式：ML 機率 ===
    if detailed and result.ml_probability is not None:
        ml_pct = result.ml_probability * 100
        lines.append(f"ML 機率: {ml_pct:.1f}%")

    # 模組解讀 (max_scores from SaptaConfig)
    modules_info = [
        (
            "absorption",
            "供給吸收",
            result.absorption,
            20,
            "主力持續吸籌，成交量放大後價格撐住",
        ),
        (
            "compression",
            "價格壓縮",
            result.compression,
            15,
            "波動收斂，準備突破",
        ),
        (
            "bb_squeeze",
            "布林擠壓",
            result.bb_squeeze,
            15,
            "布林通道收縮，突破在即",
        ),
        (
            "elliott",
            "艾略特波浪",
            result.elliott,
            20,
            "處於修正浪末端，準備啟動主升浪",
        ),
        (
            "time_projection",
            "時間投影",
            result.time_projection,
            15,
            "接近費波那契時間窗口",
        ),
        (
            "anti_distribution",
            "逆分佈",
            result.anti_distribution,
            15,
            "無出貨跡象，籌碼穩定",
        ),
    ]

    # 分類模組
    strong_mods = []  # 強勢
    weak_mods = []  # 弱勢
    neutral_mods = []  # 中性

    for key, name, data, max_score, interp in modules_info:
        if data:
            mod_score = data.get("score", 0)
            ratio = mod_score / max_score if max_score > 0 else 0

            if ratio >= 0.7:
                strong_mods.append((name, mod_score, max_score, interp))
            elif ratio >= 0.4:
                neutral_mods.append((name, mod_score, max_score, interp))
            else:
                weak_mods.append((name, mod_score, max_score, interp))

    # === 2. 核心信號 ===
    lines.append("")
    lines.append("【核心信號】")

    if strong_mods:
        lines.append("  強: " + " | ".join([f"{n} {m}/{Mx}" for n, m, Mx, _ in strong_mods]))
        for _, _, _, interp in strong_mods:
            lines.append(f"      {interp}")

    if neutral_mods:
        lines.append("  中: " + " | ".join([f"{n} {m}/{Mx}" for n, m, Mx, _ in neutral_mods]))
        for _, _, _, interp in neutral_mods:
            lines.append(f"      {interp}")

    if weak_mods:
        lines.append("  弱: " + " | ".join([f"{n} {m}/{Mx}" for n, m, Mx, _ in weak_mods]))
        for _, _, _, interp in weak_mods:
            lines.append(f"      {interp}")

    # === 3. 技術解讀 ===
    lines.append("")
    lines.append("【技術解讀】")

    # 收集所有訊號
    all_signals = []
    for _, _, data, _, _ in modules_info:
        if data and data.get("signals"):
            all_signals.extend(data["signals"])

    # 價格型態判斷
    price_trend = "盤整"
    if len(all_signals) >= 3:
        price_trend = "偏多整理"
    if any("triangle" in s.lower() for s in all_signals):
        price_trend = "三角形整理"
    if any("higher low" in s.lower() for s in all_signals):
        price_trend = "多頭整理 (支撐墊高)"
    if any("volume spike" in s.lower() and "absorbed" in s.lower() for s in all_signals):
        price_trend = "吸籌完成即將突破"

    lines.append(f"  型態: {price_trend}")

    vol_signals = [s for s in all_signals if "volume" in s.lower()]
    if vol_signals:
        lines.append(f"  成交量: {vol_signals[0][:40]}")
    else:
        lines.append("  成交量: 無明顯放量")

    # === 詳細模式：價格目標與支撐 ===
    if detailed:
        lines.append("")
        lines.append("【價格預測】")

        # 從模組數據中提取關鍵價位
        # 嘗試從 absorption 模組獲取支撐位
        if result.absorption:
            # 嘗試找到近期高點和支撐
            lines.append("  近期高點: (需從股價數據計算)")
            lines.append("  支撐位: (需從技術分析取得)")

        # 從 time_projection 模組獲取時間窗口
        if result.time_projection:
            window = result.projected_breakout_window
            if window:
                lines.append(f"  突破窗口: {window}")
            days = result.days_to_window
            if days is not None:
                lines.append(f"  距窗口: {days} 天")

        # 顯示波浪位置
        if result.wave_phase:
            wave_zh = {
                "wave1": "第1浪",
                "wave2": "第2浪",
                "wave3": "第3浪 (主升浪)",
                "wave4": "第4浪",
                "wave5": "第5浪",
                "wave_a": "A浪",
                "wave_b": "B浪",
                "wave_c": "C浪",
            }.get(result.wave_phase, result.wave_phase)
            lines.append(f"  波浪位置: {wave_zh}")

        # 費波那契回撤
        if result.fib_retracement:
            lines.append(f"  費波回撤: {result.fib_retracement:.1f}%")

    # === 4. 操作建議 ===
    lines.append("")
    lines.append("【操作建議】")

    # 根據狀態給出不同建議
    if status_en == "PRE-MARKUP":
        lines.append("  入場: 突破高點 + 成交量放大 1.5x")
        lines.append("  停損: 跌破近 5 日低點")
        lines.append("  目標: +8% / +15%")
        lines.append("  RR=1:3 可考慮分批進場")

    elif status_en == "SIAP":
        lines.append("  入場: 等布林擠壓 + 放量突破")
        lines.append("  停損: 跌破近 5 日低點")
        lines.append("  目標: +10% / +20%")
        lines.append("  RR=1:2 接近突破，待確認")

    elif status_en == "WATCHLIST":
        lines.append("  入場: 暫不進場")
        lines.append("  觀察: 等待整理完成 + 布林擠壓")
        lines.append("  加入自選觀察")

    else:  # SKIP
        lines.append("  入場: 不建議")
        lines.append("  建議: 尋找其他標的")
        lines.append("  跳過")

    # === 5. 模組分數 ===
    lines.append("")
    lines.append("【模組分數】")
    for _, name, data, max_score, _ in modules_info:
        if data:
            mod_score = data.get("score", 0)
            bar = create_progress_bar(mod_score, max_score, 10)
            status_mark = "✓" if data.get("status", False) else " "
            lines.append(f"  {name:<8} [{bar}] {mod_score:>4.0f}/{max_score:.0f} {status_mark}")

    return "\n".join(lines)


def create_screen_table(results: list[ScreenResultDict], title: str) -> str:
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


def create_compare_table(results: list[CompareResultDict]) -> str:
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


def create_forecast_table(
    ticker: str,
    current: float,
    target: float,
    support: float,
    resistance: float,
    confidence: float,
    days: int,
    chart_path: str | None = None,
) -> str:
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


def create_index_table(
    name: str,
    index_name: str,
    price: float,
    change: float,
    change_pct: float,
    day_low: float,
    day_high: float,
    week_52_low: float,
    week_52_high: float,
    chart_path: str | None = None,
) -> str:
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
