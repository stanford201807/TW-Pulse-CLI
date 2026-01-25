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
from pulse.core.data.stock_data_provider import StockDataProvider
from pulse.core.models import SignalType, TechnicalIndicators, TrendType
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class TechnicalAnalyzer:
    """Technical analysis engine using ta library."""

    def __init__(self):
        """Initialize technical analyzer."""
        self.fetcher = StockDataProvider()
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

        from datetime import datetime, timedelta

        # Define date range for fetching data (e.g., 1 year history)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Get historical data
        df = await self.fetcher.fetch_history(
            ticker, period, start_date=start_date_str, end_date=end_date_str
        )

        if df is None or df.empty:
            log.warning(f"No data available for {ticker}")
            return None

        try:
            return self._calculate_indicators(ticker, df)
        except Exception as e:
            log.error(f"Error calculating indicators for {ticker}: {e}")
            return None

    async def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame | None:
        """
        計算技術指標並附加到 DataFrame（用於回測）。

        Args:
            df: OHLCV DataFrame（必須包含 Open, High, Low, Close, Volume 欄位）

        Returns:
            帶有技術指標欄位的 DataFrame
        """
        if not HAS_TA:
            log.error("ta library not installed. Run: pip install ta")
            return None

        if df is None or df.empty:
            return None

        try:
            df = df.copy()

            # 確保欄位名稱為小寫
            df.columns = df.columns.str.lower()

            close = df["close"]
            high = df["high"]
            low = df["low"]
            volume = df["volume"]

            # 計算移動平均線
            df["MA_20"] = SMAIndicator(close, n=20).sma_indicator()
            df["MA_50"] = SMAIndicator(close, n=50).sma_indicator()
            df["MA_200"] = SMAIndicator(close, n=200).sma_indicator()

            # 計算 RSI
            df["RSI_14"] = RSIIndicator(close, n=14).rsi()

            # 計算 MACD
            macd = MACD(close)
            df["MACD"] = macd.macd()
            df["MACD_Signal"] = macd.macd_signal()
            df["MACD_Histogram"] = macd.macd_diff()

            # 計算布林通道
            bb = BollingerBands(close, n=20, ndev=2)
            df["BB_Upper"] = bb.bollinger_hband()
            df["BB_Middle"] = bb.bollinger_mavg()
            df["BB_Lower"] = bb.bollinger_lband()

            # 計算 ATR
            df["ATR_14"] = AverageTrueRange(high, low, close, n=14).average_true_range()

            return df

        except Exception as e:
            log.error(f"Error calculating indicators for DataFrame: {e}")
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
        sma_20 = SMAIndicator(close, n=20).sma_indicator().iloc[-1]
        sma_50 = SMAIndicator(close, n=50).sma_indicator().iloc[-1]
        sma_200 = SMAIndicator(close, n=200).sma_indicator().iloc[-1] if len(df) >= 200 else None

        # EMA
        ema_9 = EMAIndicator(close, n=9).ema_indicator().iloc[-1]
        ema_21 = EMAIndicator(close, n=21).ema_indicator().iloc[-1]
        ema_55 = EMAIndicator(close, n=55).ema_indicator().iloc[-1] if len(df) >= 55 else None

        # === Momentum Indicators ===

        # RSI
        rsi = RSIIndicator(close, n=14)
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
        bb = BollingerBands(close, n=20, ndev=2)
        bb_upper = float(bb.bollinger_hband().iloc[-1])
        bb_middle = float(bb.bollinger_mavg().iloc[-1])
        bb_lower = float(bb.bollinger_lband().iloc[-1])
        bb_width = float(bb.bollinger_wband().iloc[-1])

        # ATR
        atr = AverageTrueRange(high, low, close, n=14)
        atr_14 = float(atr.average_true_range().iloc[-1])

        # === Volume Indicators ===

        # OBV
        obv = OnBalanceVolumeIndicator(close, volume)
        obv_val = float(obv.on_balance_volume().iloc[-1])

        # MFI
        mfi = MFIIndicator(high, low, close, volume, n=14)
        mfi_14 = float(mfi.money_flow_index().iloc[-1])

        # === Advanced Momentum Indicators ===

        # ADX (Average Directional Index) - Manual implementation
        adx_val, adx_pos, adx_neg = self._calculate_adx(high, low, close, n=14)

        # CCI (Commodity Channel Index) - Manual implementation
        cci_val = self._calculate_cci(high, low, close, n=20)

        # Ichimoku Cloud (一目均衡表)
        ichimoku = self._calculate_ichimoku(df)

        # Volume SMA
        volume_sma = SMAIndicator(volume.astype(float), n=20).sma_indicator().iloc[-1]

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
            # Advanced momentum indicators
            adx=adx_val,
            adx_pos=adx_pos,
            adx_neg=adx_neg,
            cci=cci_val,
            # Ichimoku Cloud
            ichimoku_tenkan=ichimoku.get("tenkan"),
            ichimoku_kijun=ichimoku.get("kijun"),
            ichimoku_senkou_a=ichimoku.get("senkou_a"),
            ichimoku_senkou_b=ichimoku.get("senkou_b"),
            ichimoku_chikou=ichimoku.get("chikou"),
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

    def _calculate_ichimoku(self, df: pd.DataFrame) -> dict[str, float | None]:
        """
        Calculate Ichimoku Cloud (一目均衡表) indicators.

        Tenkan-sen (Conversion Line): (Highest High + Lowest Low) / 2 for 9 periods
        Kijun-sen (Base Line): (Highest High + Lowest Low) / 2 for 26 periods
        Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, plotted 26 periods ahead
        Senkou Span B (Leading Span B): (Highest High + Lowest Low) / 2 for 52 periods, plotted 26 ahead
        Chikou Span (Lagging Span): Close plotted 26 periods behind

        Returns:
            Dictionary with tenkan, kijun, senkou_a, senkou_b, chikou
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Need sufficient data for Ichimoku calculations (at least 52 periods)
        # Senkou Span A/B are plotted 26 periods ahead

        try:
            # Tenkan-sen (Conversion Line) - 9 periods
            tenkan_high = high.rolling(window=9).max()
            tenkan_low = low.rolling(window=9).min()
            tenkan = (tenkan_high + tenkan_low) / 2

            # Kijun-sen (Base Line) - 26 periods
            kijun_high = high.rolling(window=26).max()
            kijun_low = low.rolling(window=26).min()
            kijun = (kijun_high + kijun_low) / 2

            # Senkou Span B (Leading Span B) - 52 periods
            senkou_b_high = high.rolling(window=52).max()
            senkou_b_low = low.rolling(window=52).min()
            senkou_b = (senkou_b_high + senkou_b_low) / 2

            # Senkou Span A (Leading Span A) - plotted 26 periods ahead
            senkou_a = (tenkan + kijun) / 2

            # Get latest values (shifted 26 periods ahead for leading indicators)
            latest_tenkan = float(tenkan.iloc[-1]) if len(tenkan) > 0 else None
            latest_kijun = float(kijun.iloc[-1]) if len(kijun) > 0 else None
            latest_senkou_a = float(senkou_a.iloc[-26]) if len(senkou_a) > 26 else None
            latest_senkou_b = float(senkou_b.iloc[-26]) if len(senkou_b) > 26 else None
            latest_chikou = float(close.iloc[-26]) if len(close) > 26 else None

            return {
                "tenkan": latest_tenkan,
                "kijun": latest_kijun,
                "senkou_a": latest_senkou_a,
                "senkou_b": latest_senkou_b,
                "chikou": latest_chikou,
            }
        except Exception:
            return {
                "tenkan": None,
                "kijun": None,
                "senkou_a": None,
                "senkou_b": None,
                "chikou": None,
            }

    def _calculate_adx(
        self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14
    ) -> tuple[float | None, float | None, float | None]:
        """
        Calculate ADX (Average Directional Index) and +/- DI.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            n: Period for calculation

        Returns:
            Tuple of (adx, plus_di, minus_di)
        """
        try:
            # Calculate True Range (TR)
            prev_close = close.shift(1)
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # Calculate +DM and -DM
            plus_dm = high.diff()
            minus_dm = -low.diff()

            # Only consider positive values for +DM, negative for -DM
            plus_dm = plus_dm.where(plus_dm > minus_dm, 0)
            plus_dm = plus_dm.where(plus_dm > 0, 0)
            minus_dm = minus_dm.where(minus_dm > plus_dm, 0)
            minus_dm = minus_dm.where(minus_dm > 0, 0)

            # Smooth using rolling mean
            atr = tr.rolling(window=n).mean()
            plus_di = (plus_dm.rolling(window=n).mean() / atr) * 100
            minus_di = (minus_dm.rolling(window=n).mean() / atr) * 100

            # Calculate DX
            dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100

            # Calculate ADX (smoothed DX)
            adx = dx.rolling(window=n).mean()

            return (
                float(adx.iloc[-1]) if len(adx) > 0 and not pd.isna(adx.iloc[-1]) else None,
                float(plus_di.iloc[-1])
                if len(plus_di) > 0 and not pd.isna(plus_di.iloc[-1])
                else None,
                float(minus_di.iloc[-1])
                if len(minus_di) > 0 and not pd.isna(minus_di.iloc[-1])
                else None,
            )
        except Exception:
            return None, None, None

    def _calculate_cci(
        self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 20
    ) -> float | None:
        """
        Calculate CCI (Commodity Channel Index).

        CCI = (Typical Price - SMA of TP) / (0.015 * Mean Deviation)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            n: Period for calculation

        Returns:
            CCI value or None
        """
        try:
            # Typical Price
            tp = (high + low + close) / 3

            # SMA of Typical Price
            tp_sma = tp.rolling(window=n).mean()

            # Mean Deviation
            mean_dev = tp.rolling(window=n).apply(lambda x: abs(x - x.mean()).mean(), raw=True)

            # CCI
            cci = (tp - tp_sma) / (0.015 * mean_dev)

            return float(cci.iloc[-1]) if len(cci) > 0 and not pd.isna(cci.iloc[-1]) else None
        except Exception:
            return None

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
