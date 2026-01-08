"""Technical analysis engine."""

from datetime import datetime

import pandas as pd

try:
    from ta.momentum import RSIIndicator, StochasticOscillator
    from ta.trend import MACD, EMAIndicator, SMAIndicator
    from ta.volatility import AverageTrueRange, BollingerBands
    from ta.volume import MFIIndicator, OnBalanceVolumeIndicator

    HAS_TA = True
except ImportError:
    HAS_TA = False

from pulse.core.config import settings
from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.models import SignalType, TechnicalIndicators, TrendType
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class TechnicalAnalyzer:
    """Technical analysis engine using ta library."""

    def __init__(self):
        """Initialize technical analyzer."""
        self.fetcher = YFinanceFetcher()
        self.settings = settings.analysis

    async def analyze(
        self,
        ticker: str,
        period: str = "1y",
    ) -> TechnicalIndicators | None:
        """
        Perform full technical analysis on a stock.

        Args:
            ticker: Stock ticker
            period: Historical data period

        Returns:
            TechnicalIndicators object or None
        """
        if not HAS_TA:
            log.error("ta library not installed. Run: pip install ta")
            return None

        # Get historical data
        df = self.fetcher.get_history_df(ticker, period)

        if df is None or df.empty:
            log.warning(f"No data available for {ticker}")
            return None

        try:
            return self._calculate_indicators(ticker, df)
        except Exception as e:
            log.error(f"Error calculating indicators for {ticker}: {e}")
            return None

    def _calculate_indicators(
        self,
        ticker: str,
        df: pd.DataFrame,
    ) -> TechnicalIndicators:
        """Calculate all technical indicators."""
        # Ensure we have the required columns
        df = df.copy()

        # Get latest values
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        latest_close = float(close.iloc[-1])

        # === Trend Indicators ===

        # SMA
        sma_20 = SMAIndicator(close, window=20).sma_indicator().iloc[-1]
        sma_50 = SMAIndicator(close, window=50).sma_indicator().iloc[-1]
        sma_200 = (
            SMAIndicator(close, window=200).sma_indicator().iloc[-1] if len(df) >= 200 else None
        )

        # EMA
        ema_9 = EMAIndicator(close, window=9).ema_indicator().iloc[-1]
        ema_21 = EMAIndicator(close, window=21).ema_indicator().iloc[-1]
        ema_55 = EMAIndicator(close, window=55).ema_indicator().iloc[-1] if len(df) >= 55 else None

        # === Momentum Indicators ===

        # RSI
        rsi = RSIIndicator(close, window=14)
        rsi_14 = float(rsi.rsi().iloc[-1])

        # MACD
        macd_indicator = MACD(close)
        macd_val = float(macd_indicator.macd().iloc[-1])
        macd_signal = float(macd_indicator.macd_signal().iloc[-1])
        macd_histogram = float(macd_indicator.macd_diff().iloc[-1])

        # Stochastic
        stoch = StochasticOscillator(high, low, close)
        stoch_k = float(stoch.stoch().iloc[-1])
        stoch_d = float(stoch.stoch_signal().iloc[-1])

        # === Volatility Indicators ===

        # Bollinger Bands
        bb = BollingerBands(close, window=20, window_dev=2)
        bb_upper = float(bb.bollinger_hband().iloc[-1])
        bb_middle = float(bb.bollinger_mavg().iloc[-1])
        bb_lower = float(bb.bollinger_lband().iloc[-1])
        bb_width = float(bb.bollinger_wband().iloc[-1])

        # ATR
        atr = AverageTrueRange(high, low, close, window=14)
        atr_14 = float(atr.average_true_range().iloc[-1])

        # === Volume Indicators ===

        # OBV
        obv = OnBalanceVolumeIndicator(close, volume)
        obv_val = float(obv.on_balance_volume().iloc[-1])

        # MFI
        mfi = MFIIndicator(high, low, close, volume, window=14)
        mfi_14 = float(mfi.money_flow_index().iloc[-1])

        # Volume SMA
        volume_sma = SMAIndicator(volume.astype(float), window=20).sma_indicator().iloc[-1]

        # === Support/Resistance ===
        support_1, support_2, resistance_1, resistance_2 = self._calculate_support_resistance(df)

        # === Determine Trend and Signal ===
        trend = self._determine_trend(latest_close, sma_20, sma_50, sma_200, ema_9, ema_21)
        signal = self._determine_signal(
            rsi_14, macd_val, macd_signal, stoch_k, stoch_d, latest_close, bb_upper, bb_lower, trend
        )

        return TechnicalIndicators(
            ticker=ticker,
            calculated_at=datetime.now(),
            sma_20=float(sma_20) if pd.notna(sma_20) else None,
            sma_50=float(sma_50) if pd.notna(sma_50) else None,
            sma_200=float(sma_200) if sma_200 and pd.notna(sma_200) else None,
            ema_9=float(ema_9) if pd.notna(ema_9) else None,
            ema_21=float(ema_21) if pd.notna(ema_21) else None,
            ema_55=float(ema_55) if ema_55 and pd.notna(ema_55) else None,
            rsi_14=rsi_14,
            macd=macd_val,
            macd_signal=macd_signal,
            macd_histogram=macd_histogram,
            stoch_k=stoch_k,
            stoch_d=stoch_d,
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower,
            bb_width=bb_width,
            atr_14=atr_14,
            obv=obv_val,
            mfi_14=mfi_14,
            volume_sma_20=float(volume_sma) if pd.notna(volume_sma) else None,
            support_1=support_1,
            support_2=support_2,
            resistance_1=resistance_1,
            resistance_2=resistance_2,
            trend=trend,
            signal=signal,
        )

    def _calculate_support_resistance(
        self,
        df: pd.DataFrame,
        window: int = 20,
    ) -> tuple:
        """Calculate support and resistance levels using pivot points."""
        recent = df.tail(window)

        high = recent["high"].max()
        low = recent["low"].min()
        close = recent["close"].iloc[-1]

        # Pivot point
        pivot = (high + low + close) / 3

        # Support levels
        support_1 = (2 * pivot) - high
        support_2 = pivot - (high - low)

        # Resistance levels
        resistance_1 = (2 * pivot) - low
        resistance_2 = pivot + (high - low)

        return (
            float(support_1),
            float(support_2),
            float(resistance_1),
            float(resistance_2),
        )

    def _determine_trend(
        self,
        price: float,
        sma_20: float,
        sma_50: float,
        sma_200: float | None,
        ema_9: float,
        ema_21: float,
    ) -> TrendType:
        """Determine overall trend direction."""
        bullish_signals = 0
        bearish_signals = 0

        # Price vs SMAs
        if price > sma_20:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if price > sma_50:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if sma_200 and price > sma_200:
            bullish_signals += 2  # More weight
        elif sma_200:
            bearish_signals += 2

        # EMA crossover
        if ema_9 > ema_21:
            bullish_signals += 1
        else:
            bearish_signals += 1

        # SMA alignment
        if sma_20 > sma_50:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if bullish_signals >= bearish_signals + 2:
            return TrendType.BULLISH
        elif bearish_signals >= bullish_signals + 2:
            return TrendType.BEARISH
        else:
            return TrendType.SIDEWAYS

    def _determine_signal(
        self,
        rsi: float,
        macd: float,
        macd_signal: float,
        stoch_k: float,
        stoch_d: float,
        price: float,
        bb_upper: float,
        bb_lower: float,
        trend: TrendType,
    ) -> SignalType:
        """Determine trading signal."""
        buy_signals = 0
        sell_signals = 0

        # RSI
        if rsi < 30:
            buy_signals += 2  # Oversold
        elif rsi < 40:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 2  # Overbought
        elif rsi > 60:
            sell_signals += 1

        # MACD
        if macd > macd_signal:
            buy_signals += 1
        else:
            sell_signals += 1

        # Stochastic
        if stoch_k < 20 and stoch_k > stoch_d:
            buy_signals += 1
        elif stoch_k > 80 and stoch_k < stoch_d:
            sell_signals += 1

        # Bollinger Bands
        if price < bb_lower:
            buy_signals += 1
        elif price > bb_upper:
            sell_signals += 1

        # Trend influence
        if trend == TrendType.BULLISH:
            buy_signals += 1
        elif trend == TrendType.BEARISH:
            sell_signals += 1

        # Determine final signal
        diff = buy_signals - sell_signals

        if diff >= 4:
            return SignalType.STRONG_BUY
        elif diff >= 2:
            return SignalType.BUY
        elif diff <= -4:
            return SignalType.STRONG_SELL
        elif diff <= -2:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL

    def get_indicator_summary(
        self,
        indicators: TechnicalIndicators,
    ) -> list[dict]:
        """
        Generate human-readable indicator summary.

        Args:
            indicators: TechnicalIndicators object

        Returns:
            List of indicator summaries
        """
        summary = []

        # RSI
        if indicators.rsi_14:
            rsi_status = (
                "Oversold"
                if indicators.rsi_14 < 30
                else "Overbought"
                if indicators.rsi_14 > 70
                else "Neutral"
            )
            summary.append(
                {
                    "name": "RSI (14)",
                    "value": f"{indicators.rsi_14:.2f}",
                    "status": rsi_status,
                }
            )

        # MACD
        if indicators.macd is not None and indicators.macd_signal is not None:
            macd_status = "Bullish" if indicators.macd > indicators.macd_signal else "Bearish"
            summary.append(
                {
                    "name": "MACD",
                    "value": f"{indicators.macd:.2f}",
                    "status": macd_status,
                }
            )

        # Moving Averages
        if indicators.sma_20:
            summary.append(
                {
                    "name": "SMA 20",
                    "value": f"{indicators.sma_20:,.0f}",
                    "status": "",
                }
            )

        if indicators.sma_50:
            summary.append(
                {
                    "name": "SMA 50",
                    "value": f"{indicators.sma_50:,.0f}",
                    "status": "",
                }
            )

        # Bollinger Bands
        if indicators.bb_upper and indicators.bb_lower:
            summary.append(
                {
                    "name": "BB Upper",
                    "value": f"{indicators.bb_upper:,.0f}",
                    "status": "",
                }
            )
            summary.append(
                {
                    "name": "BB Lower",
                    "value": f"{indicators.bb_lower:,.0f}",
                    "status": "",
                }
            )

        # Trend & Signal
        summary.append(
            {
                "name": "Trend",
                "value": indicators.trend.value,
                "status": "",
            }
        )
        summary.append(
            {
                "name": "Signal",
                "value": indicators.signal.value,
                "status": "",
            }
        )

        return summary
