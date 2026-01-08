"""Price forecasting using Prophet and statistical models."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pulse.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class ForecastResult:
    """Forecast result container."""

    ticker: str
    forecast_days: int
    predictions: list[float]
    lower_bound: list[float]
    upper_bound: list[float]
    trend: str  # "bullish", "bearish", "sideways"
    confidence: float
    target_price: float
    support: float
    resistance: float


class PriceForecaster:
    """Price forecasting using multiple models."""

    def __init__(self):
        self._prophet_available = self._check_prophet()

    def _check_prophet(self) -> bool:
        """Check if Prophet is available."""
        try:
            from prophet import Prophet  # noqa: F401

            return True
        except ImportError:
            log.warning("Prophet not available, using fallback methods")
            return False

    async def forecast(
        self,
        ticker: str,
        prices: list[float],
        dates: list[str],
        days: int = 7,
    ) -> ForecastResult | None:
        """
        Forecast future prices.

        Args:
            ticker: Stock ticker
            prices: Historical closing prices
            dates: Historical dates
            days: Days to forecast

        Returns:
            ForecastResult or None
        """
        if len(prices) < 30:
            log.warning(f"Not enough data for forecasting: {len(prices)} points")
            return None

        if self._prophet_available:
            return await self._forecast_prophet(ticker, prices, dates, days)
        else:
            return await self._forecast_simple(ticker, prices, dates, days)

    async def _forecast_prophet(
        self,
        ticker: str,
        prices: list[float],
        dates: list[str],
        days: int,
    ) -> ForecastResult | None:
        """Forecast using Facebook Prophet."""
        try:
            from prophet import Prophet

            # Prepare data for Prophet
            df = pd.DataFrame({"ds": pd.to_datetime(dates), "y": prices})

            # Create and fit model
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05,
            )
            model.fit(df)

            # Make future dataframe
            future = model.make_future_dataframe(periods=days)
            forecast = model.predict(future)

            # Extract predictions
            predictions = forecast["yhat"].tail(days).tolist()
            lower_bound = forecast["yhat_lower"].tail(days).tolist()
            upper_bound = forecast["yhat_upper"].tail(days).tolist()

            # Determine trend
            current_price = prices[-1]
            target_price = predictions[-1]
            change_pct = (target_price - current_price) / current_price * 100

            if change_pct > 3:
                trend = "bullish"
            elif change_pct < -3:
                trend = "bearish"
            else:
                trend = "sideways"

            # Calculate confidence based on prediction interval width
            avg_interval = np.mean([u - l for u, l in zip(upper_bound, lower_bound)])
            confidence = max(0, min(100, 100 - (avg_interval / current_price * 100)))

            # Support and resistance from bounds
            support = min(lower_bound)
            resistance = max(upper_bound)

            return ForecastResult(
                ticker=ticker,
                forecast_days=days,
                predictions=predictions,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                trend=trend,
                confidence=round(confidence, 1),
                target_price=round(target_price, 2),
                support=round(support, 2),
                resistance=round(resistance, 2),
            )

        except Exception as e:
            log.error(f"Prophet forecast failed: {e}")
            return await self._forecast_simple(ticker, prices, dates, days)

    async def _forecast_simple(
        self,
        ticker: str,
        prices: list[float],
        dates: list[str],
        days: int,
    ) -> ForecastResult | None:
        """Simple moving average based forecast."""
        try:
            # Calculate moving averages
            ma_short = np.mean(prices[-5:])
            ma_medium = np.mean(prices[-20:])
            ma_long = np.mean(prices[-50:]) if len(prices) >= 50 else np.mean(prices)

            # Simple trend extrapolation
            recent_trend = (prices[-1] - prices[-5]) / 5

            predictions = []
            for i in range(1, days + 1):
                # Dampen the trend over time
                dampening = 0.9**i
                pred = prices[-1] + (recent_trend * i * dampening)
                predictions.append(pred)

            # Calculate volatility for bounds
            volatility = np.std(prices[-20:])
            lower_bound = [p - volatility * 1.5 for p in predictions]
            upper_bound = [p + volatility * 1.5 for p in predictions]

            # Determine trend
            current_price = prices[-1]
            target_price = predictions[-1]
            change_pct = (target_price - current_price) / current_price * 100

            if change_pct > 2:
                trend = "bullish"
            elif change_pct < -2:
                trend = "bearish"
            else:
                trend = "sideways"

            # Lower confidence for simple method
            confidence = 50.0

            return ForecastResult(
                ticker=ticker,
                forecast_days=days,
                predictions=predictions,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                trend=trend,
                confidence=confidence,
                target_price=round(target_price, 2),
                support=round(min(lower_bound), 2),
                resistance=round(max(upper_bound), 2),
            )

        except Exception as e:
            log.error(f"Simple forecast failed: {e}")
            return None

    def format_forecast(self, result: ForecastResult) -> str:
        """Format forecast result as text."""
        trend_symbol = {"bullish": "UP", "bearish": "DOWN", "sideways": "SIDEWAYS"}

        lines = [
            f"Forecast: {result.ticker} ({result.forecast_days} hari)",
            "",
            f"Trend: {trend_symbol.get(result.trend, result.trend)}",
            f"Target: {result.target_price:,.0f}",
            f"Support: {result.support:,.0f}",
            f"Resistance: {result.resistance:,.0f}",
            f"Confidence: {result.confidence:.0f}%",
        ]

        return "\n".join(lines)
