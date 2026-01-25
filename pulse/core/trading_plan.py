"""
Trading Plan Generator - Calculate TP, SL, and Risk/Reward for trades.

Provides complete trading plans with:
- Entry price (current or suggested)
- Take Profit levels (TP1, TP2, TP3)
- Stop Loss with multiple calculation methods
- Risk/Reward ratio analysis
- Position sizing suggestions
- Execution strategy
"""

from datetime import datetime
from typing import Any

from pulse.core.analysis.technical import TechnicalAnalyzer
from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.models import (
    SignalType,
    TradeQuality,
    TradeValidity,
    TradingPlan,
    TrendType,
)
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class TradingPlanGenerator:
    """
    Generate complete trading plans with TP, SL, and RR calculations.

    Usage:
        generator = TradingPlanGenerator()
        plan = await generator.generate("BBCA")
        print(generator.format_plan(plan))
    """

    # Default settings
    DEFAULT_RISK_PERCENT = 2.0  # 2% risk per trade
    DEFAULT_ATR_SL_MULTIPLIER = 1.5  # SL = Entry - (ATR * 1.5)
    DEFAULT_ATR_TP_MULTIPLIER = 2.0  # TP1 = Entry + (ATR * 2.0)
    DEFAULT_ACCOUNT_SIZE = 100_000_000  # NT$ 100 萬預設值

    def __init__(self):
        self.fetcher = YFinanceFetcher()
        self.analyzer = TechnicalAnalyzer()

    async def generate(
        self,
        ticker: str,
        entry_price: float | None = None,
        risk_percent: float = DEFAULT_RISK_PERCENT,
        sl_method: str = "hybrid",
    ) -> TradingPlan | None:
        """
        Generate complete trading plan for a ticker.

        Args:
            ticker: Stock ticker (e.g., "BBCA")
            entry_price: Custom entry price (None = use current price)
            risk_percent: Risk percentage per trade (default 2%)
            sl_method: Stop loss method ("atr", "support", "percentage", "hybrid")

        Returns:
            TradingPlan object or None if data unavailable
        """
        log.info(f"Generating trading plan for {ticker}")

        try:
            # Fetch stock data
            stock = await self.fetcher.fetch_stock(ticker)
            if not stock:
                log.warning(f"No stock data for {ticker}")
                return None

            # Fetch technical indicators
            technical = await self.analyzer.analyze(ticker)
            if not technical:
                log.warning(f"No technical data for {ticker}")
                return None

            # Use current price if no entry specified
            entry = entry_price or stock.current_price
            if not entry or entry <= 0:
                log.warning(f"Invalid entry price for {ticker}")
                return None

            # Get key technical values
            atr = technical.atr_14 or (entry * 0.02)  # Fallback: 2% of price
            support_1 = technical.support_1 or (entry * 0.97)
            support_2 = technical.support_2 or (entry * 0.94)
            resistance_1 = technical.resistance_1 or (entry * 1.03)
            resistance_2 = technical.resistance_2 or (entry * 1.06)

            # Calculate Stop Loss
            stop_loss, sl_method_used = self._calculate_stop_loss(
                entry=entry,
                support_1=support_1,
                support_2=support_2,
                atr=atr,
                method=sl_method,
            )

            # Calculate Take Profit levels
            tp1, tp2, tp3 = self._calculate_take_profits(
                entry=entry,
                resistance_1=resistance_1,
                resistance_2=resistance_2,
                atr=atr,
            )

            # Calculate percentages
            sl_percent = ((stop_loss - entry) / entry) * 100
            tp1_percent = ((tp1 - entry) / entry) * 100
            tp2_percent = ((tp2 - entry) / entry) * 100 if tp2 else None
            tp3_percent = ((tp3 - entry) / entry) * 100 if tp3 else None

            # Calculate risk and reward
            risk_amount = entry - stop_loss
            reward_tp1 = tp1 - entry
            reward_tp2 = (tp2 - entry) if tp2 else None

            # Calculate R:R ratios
            rr_tp1 = reward_tp1 / risk_amount if risk_amount > 0 else 0
            rr_tp2 = reward_tp2 / risk_amount if reward_tp2 and risk_amount > 0 else None

            # Assess trade quality
            trade_quality = self._assess_trade_quality(rr_tp1)

            # Determine confidence based on multiple factors
            confidence = self._calculate_confidence(
                technical=technical,
                rr_ratio=rr_tp1,
                trade_quality=trade_quality,
            )

            # Determine validity/timeframe
            validity = self._determine_validity(atr, entry)

            # Generate notes
            notes = self._generate_notes(
                technical=technical,
                entry=entry,
                atr=atr,
            )

            # Generate execution strategy
            execution_strategy = self._generate_execution_strategy(
                entry=entry,
                tp1=tp1,
                tp2=tp2,
                stop_loss=stop_loss,
            )

            return TradingPlan(
                ticker=ticker,
                generated_at=datetime.now(),
                entry_price=round(entry, 0),
                entry_type="market",
                tp1=round(tp1, 0),
                tp1_percent=round(tp1_percent, 2),
                tp2=round(tp2, 0) if tp2 else None,
                tp2_percent=round(tp2_percent, 2) if tp2_percent else None,
                tp3=round(tp3, 0) if tp3 else None,
                tp3_percent=round(tp3_percent, 2) if tp3_percent else None,
                stop_loss=round(stop_loss, 0),
                stop_loss_percent=round(sl_percent, 2),
                stop_loss_method=sl_method_used,
                risk_amount=round(risk_amount, 0),
                reward_tp1=round(reward_tp1, 0),
                reward_tp2=round(reward_tp2, 0) if reward_tp2 else None,
                rr_ratio_tp1=round(rr_tp1, 2),
                rr_ratio_tp2=round(rr_tp2, 2) if rr_tp2 else None,
                trade_quality=trade_quality,
                confidence=confidence,
                validity=validity,
                suggested_risk_percent=risk_percent,
                trend=technical.trend,
                signal=technical.signal,
                rsi=round(technical.rsi_14, 1) if technical.rsi_14 else None,
                atr=round(atr, 0),
                support_1=round(support_1, 0),
                support_2=round(support_2, 0),
                resistance_1=round(resistance_1, 0),
                resistance_2=round(resistance_2, 0),
                notes=notes,
                execution_strategy=execution_strategy,
            )

        except Exception as e:
            log.error(f"Error generating trading plan for {ticker}: {e}")
            return None

    def _calculate_stop_loss(
        self,
        entry: float,
        support_1: float,
        support_2: float,
        atr: float,
        method: str = "hybrid",
    ) -> tuple[float, str]:
        """
        Calculate stop loss using multiple methods.

        Methods:
        - atr: Entry - (ATR * 1.5) - adapts to volatility
        - support: Below support_1 with buffer - respects key levels
        - percentage: Fixed 3% stop - simple and consistent
        - hybrid: Pick the tightest valid stop loss

        Returns:
            Tuple of (stop_loss_price, method_used)
        """
        # ATR-based SL
        atr_sl = entry - (atr * self.DEFAULT_ATR_SL_MULTIPLIER)

        # Support-based SL (1% below support for buffer)
        support_sl = support_1 * 0.99

        # Percentage-based SL (3% stop)
        pct_sl = entry * 0.97

        if method == "atr":
            return atr_sl, "atr"
        elif method == "support":
            return support_sl, "support"
        elif method == "percentage":
            return pct_sl, "percentage"
        else:  # hybrid
            # Pick the highest (tightest) SL that's still valid
            candidates = [
                (atr_sl, "atr"),
                (support_sl, "support"),
                (pct_sl, "percentage"),
            ]

            # Filter out invalid SLs (above entry or negative)
            valid = [(sl, m) for sl, m in candidates if 0 < sl < entry]

            if not valid:
                return pct_sl, "percentage"

            # Pick the tightest (highest value = smallest loss)
            best = max(valid, key=lambda x: x[0])
            return best

    def _calculate_take_profits(
        self,
        entry: float,
        resistance_1: float,
        resistance_2: float,
        atr: float,
    ) -> tuple[float, float | None, float | None]:
        """
        Calculate 3 levels of take profit.

        TP1: Conservative - nearest resistance or 1.5x ATR
        TP2: Moderate - resistance 2 or 2.5x ATR
        TP3: Aggressive - 3.5x ATR (extended target)
        """
        # TP1: Use resistance_1 if reasonable, else ATR-based
        tp1_atr = entry + (atr * 1.5)
        tp1 = resistance_1 if resistance_1 > entry * 1.01 else tp1_atr

        # TP2: Use resistance_2 or ATR-based
        tp2_atr = entry + (atr * 2.5)
        tp2 = resistance_2 if resistance_2 > tp1 * 1.01 else tp2_atr

        # TP3: Extended target
        tp3 = entry + (atr * 3.5)

        return tp1, tp2, tp3

    def _assess_trade_quality(self, rr_ratio: float) -> TradeQuality:
        """
        Assess trade quality based on R:R ratio.

        - Excellent: RR >= 3.0 (risk 1 to gain 3+)
        - Good: RR >= 2.0
        - Fair: RR >= 1.5
        - Poor: RR < 1.5 (not recommended)
        """
        if rr_ratio >= 3.0:
            return TradeQuality.EXCELLENT
        elif rr_ratio >= 2.0:
            return TradeQuality.GOOD
        elif rr_ratio >= 1.5:
            return TradeQuality.FAIR
        else:
            return TradeQuality.POOR

    def _calculate_confidence(
        self,
        technical: Any,
        rr_ratio: float,
        trade_quality: TradeQuality,
    ) -> int:
        """Calculate confidence score (0-100) based on multiple factors."""
        score = 50  # Base score

        # R:R ratio contribution
        if rr_ratio >= 3.0:
            score += 15
        elif rr_ratio >= 2.0:
            score += 10
        elif rr_ratio >= 1.5:
            score += 5
        else:
            score -= 10

        # Trend alignment
        if technical.trend == TrendType.BULLISH:
            score += 10
        elif technical.trend == TrendType.BEARISH:
            score -= 10

        # Signal strength
        if technical.signal == SignalType.STRONG_BUY:
            score += 15
        elif technical.signal == SignalType.BUY:
            score += 10
        elif technical.signal == SignalType.STRONG_SELL:
            score -= 15
        elif technical.signal == SignalType.SELL:
            score -= 10

        # RSI contribution
        if technical.rsi_14:
            if 40 <= technical.rsi_14 <= 60:
                score += 5  # Neutral is safe
            elif technical.rsi_14 < 30:
                score += 10  # Oversold - good for buy
            elif technical.rsi_14 > 70:
                score -= 10  # Overbought - risky

        # MACD alignment
        if technical.macd and technical.macd_signal:
            if technical.macd > technical.macd_signal:
                score += 5  # Bullish
            else:
                score -= 5  # Bearish

        return max(0, min(100, score))

    def _determine_validity(self, atr: float, entry: float) -> TradeValidity:
        """
        Determine trade validity based on volatility.

        High volatility = shorter timeframe (intraday)
        Low volatility = longer timeframe (position)
        """
        atr_percent = (atr / entry) * 100

        if atr_percent > 3.0:
            return TradeValidity.INTRADAY
        elif atr_percent > 1.5:
            return TradeValidity.SWING
        else:
            return TradeValidity.POSITION

    def _generate_notes(
        self,
        technical: Any,
        entry: float,
        atr: float,
    ) -> list[str]:
        """Generate trading notes based on technical analysis."""
        notes = []

        # RSI note
        if technical.rsi_14:
            rsi = technical.rsi_14
            if rsi < 30:
                notes.append(f"RSI {rsi:.1f} - 超賣，可能反轉")
            elif rsi > 70:
                notes.append(f"RSI {rsi:.1f} - Overbought, caution advised")
            elif 45 <= rsi <= 55:
                notes.append(f"RSI {rsi:.1f} - 中性，可雙向移動")
            else:
                notes.append(
                    f"RSI {rsi:.1f} - {'多頭動能' if rsi > 55 else '空頭壓力'}"
                )

        # MACD note
        if technical.macd and technical.macd_signal:
            if technical.macd > technical.macd_signal:
                if technical.macd_histogram and technical.macd_histogram > 0:
                    notes.append("MACD 多頭交叉，動能增強")
                else:
                    notes.append("MACD 多頭但動能減弱")
            else:
                notes.append("MACD 空頭，等待交叉確認")

        # Trend note
        notes.append(f"趨勢：{technical.trend.value}")

        # ATR/Volatility note
        atr_percent = (atr / entry) * 100
        notes.append(f"ATR: NT$ {atr:,.0f} ({atr_percent:.2f}% 日波動率)")

        # Signal note
        notes.append(f"訊號：{technical.signal.value}")

        return notes

    def _generate_execution_strategy(
        self,
        entry: float,
        tp1: float,
        tp2: float | None,
        stop_loss: float,
    ) -> list[str]:
        """生成逐步執行策略。"""
        strategy = [
            f"1. 進場：以市價或限價 NT$ {entry:,.0f} 買進",
            f"2. 立即設定停損於 NT$ {stop_loss:,.0f}",
            f"3. TP1：於 NT$ {tp1:,.0f} 賣出 50% 倉位",
            f"4. TP1 觸及後：將停損移至保本價 (NT$ {entry:,.0f})",
        ]

        if tp2:
            strategy.append(f"5. TP2：於 NT$ {tp2:,.0f} 賣出剩餘 50%")

        strategy.append("6. 若觸及停損：全數出場，不攜平")

        return strategy

    def calculate_position_size(
        self,
        plan: TradingPlan,
        account_size: float = DEFAULT_ACCOUNT_SIZE,
        risk_percent: float | None = None,
    ) -> dict[str, Any]:
        """
        Calculate position size based on risk management.

        Formula:
        Max Risk Amount = Account Size * Risk Percent
        Risk Per Share = Entry - Stop Loss
        Shares = Max Risk Amount / Risk Per Share
        Lots = Shares / 100 (IDX lot size)
        """
        risk_pct = risk_percent or plan.suggested_risk_percent
        max_risk = account_size * (risk_pct / 100)
        risk_per_share = plan.risk_amount

        if risk_per_share <= 0:
            return {"error": "Invalid stop loss (above entry)"}

        shares = int(max_risk / risk_per_share)
        lots = shares // 100
        position_value = lots * 100 * plan.entry_price

        return {
            "account_size": account_size,
            "risk_percent": risk_pct,
            "max_risk_amount": max_risk,
            "risk_per_share": risk_per_share,
            "shares": shares,
            "lots": lots,
            "position_value": position_value,
            "position_percent": (position_value / account_size) * 100,
        }

    def format_plan(
        self,
        plan: TradingPlan,
        account_size: float | None = None,
        include_position_sizing: bool = True,
    ) -> str:
        """格式化交易計畫為可讀文字。"""
        lines = [
            f"交易計畫: {plan.ticker}",
            f"生成時間: {plan.generated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "=== 進場 ===",
            f"價格: NT$ {plan.entry_price:,.0f} (當前價)",
            f"類型: {plan.entry_type.title()}",
            f"趨勢: {plan.trend.value} | 訊號: {plan.signal.value}",
            "",
            "=== 停利目標 ===",
            f"TP1: NT$ {plan.tp1:,.0f} ({plan.tp1_percent:+.2f}%) - 保守",
        ]

        if plan.tp2:
            lines.append(f"TP2: NT$ {plan.tp2:,.0f} ({plan.tp2_percent:+.2f}%) - 適中")
        if plan.tp3:
            lines.append(f"TP3: NT$ {plan.tp3:,.0f} ({plan.tp3_percent:+.2f}%) - 積極")

        lines.extend(
            [
                "",
                "=== 停損 ===",
                f"SL: NT$ {plan.stop_loss:,.0f} ({plan.stop_loss_percent:.2f}%)",
                f"方法: {plan.stop_loss_method.title()}",
                "",
                "=== 風險/報酬 ===",
                f"風險: NT$ {plan.risk_amount:,.0f} 每股 ({abs(plan.stop_loss_percent):.2f}%)",
                f"報酬 (TP1): NT$ {plan.reward_tp1:,.0f} ({plan.tp1_percent:.2f}%)",
            ]
        )

        if plan.reward_tp2:
            lines.append(f"報酬 (TP2): NT$ {plan.reward_tp2:,.0f} ({plan.tp2_percent:.2f}%)")

        # R:R ratios with quality indicator
        rr1_quality = self._get_rr_quality_label(plan.rr_ratio_tp1)
        lines.append("")
        lines.append(f"R:R to TP1: 1:{plan.rr_ratio_tp1:.1f} [{rr1_quality}]")

        if plan.rr_ratio_tp2:
            rr2_quality = self._get_rr_quality_label(plan.rr_ratio_tp2)
            lines.append(f"R:R to TP2: 1:{plan.rr_ratio_tp2:.1f} [{rr2_quality}]")

        lines.extend(
            [
                "",
                f"交易品質: {plan.trade_quality.value.upper()}",
                f"信心度: {plan.confidence}%",
            ]
        )

        # Position sizing
        if include_position_sizing:
            acc_size = account_size or self.DEFAULT_ACCOUNT_SIZE
            pos = self.calculate_position_size(plan, acc_size)

            if "error" not in pos:
                lines.extend(
                    [
                        "",
                        f"=== 倉位計算 ({plan.suggested_risk_percent}% 風險) ===",
                        f"帳戶: NT$ {pos['account_size']:,.0f}",
                        f"最大風險: NT$ {pos['max_risk_amount']:,.0f}",
                        f"每股風險: NT$ {pos['risk_per_share']:,.0f}",
                        f"建議: {pos['lots']:,} 張 ({pos['shares']:,} 股)",
                        f"倉位價值: NT$ {pos['position_value']:,.0f} (帳戶 {pos['position_percent']:.1f}%)",
                    ]
                )

        # Notes
        if plan.notes:
            lines.extend(["", "=== 備註 ==="])
            for note in plan.notes:
                lines.append(f"- {note}")

        # Execution strategy
        if plan.execution_strategy:
            lines.extend(["", "=== 執行策略 ==="])
            for step in plan.execution_strategy:
                lines.append(step)

        # Validity
        lines.extend(
            [
                "",
                f"有效期: {plan.validity.value}",
            ]
        )

        return "\n".join(lines)

    def _get_rr_quality_label(self, rr_ratio: float) -> str:
        """取得 R:R 比率品質標籤。"""
        if rr_ratio >= 3.0:
            return "優秀"
        elif rr_ratio >= 2.0:
            return "良好"
        elif rr_ratio >= 1.5:
            return "合理"
        else:
            return "不佳"
