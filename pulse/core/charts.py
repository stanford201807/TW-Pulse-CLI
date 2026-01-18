"""Terminal chart visualization using plotext."""

import plotext as plt


class TerminalChart:
    """Generate ASCII charts for terminal display."""

    def __init__(self, width: int = 80, height: int = 20):
        self.width = width
        self.height = height

    def price_chart(
        self,
        dates: list[str],
        prices: list[float],
        title: str = "Price",
        color: str = "cyan",
    ) -> str:
        """
        Generate price line chart.

        Args:
            dates: List of date strings
            prices: List of prices
            title: Chart title
            color: Line color

        Returns:
            ASCII chart string
        """
        plt.clear_figure()
        plt.plot_size(self.width, self.height)
        plt.plot(prices, marker="braille", color=color)
        plt.title(title)
        plt.theme("dark")

        # Get chart as string
        return plt.build()

    def candlestick_chart(
        self,
        dates: list[str],
        opens: list[float],
        highs: list[float],
        lows: list[float],
        closes: list[float],
        title: str = "OHLC",
    ) -> str:
        """
        Generate candlestick-style chart.

        Args:
            dates: List of date strings
            opens, highs, lows, closes: OHLC data
            title: Chart title

        Returns:
            ASCII chart string
        """
        plt.clear_figure()
        plt.plot_size(self.width, self.height)
        plt.candlestick(dates, {"Open": opens, "High": highs, "Low": lows, "Close": closes})
        plt.title(title)
        plt.theme("dark")

        return plt.build()

    def volume_chart(
        self,
        dates: list[str],
        volumes: list[float],
        title: str = "Volume",
    ) -> str:
        """
        Generate volume bar chart.

        Args:
            dates: List of date strings
            volumes: List of volumes
            title: Chart title

        Returns:
            ASCII chart string
        """
        plt.clear_figure()
        plt.plot_size(self.width, self.height // 2)
        plt.bar(volumes, color="blue")
        plt.title(title)
        plt.theme("dark")

        return plt.build()

    def multi_line_chart(
        self,
        data: dict,
        title: str = "Indicators",
        labels: list[str] | None = None,
    ) -> str:
        """
        Generate multi-line chart for indicators.

        Args:
            data: Dict of {label: values}
            title: Chart title
            labels: Optional x-axis labels

        Returns:
            ASCII chart string
        """
        plt.clear_figure()
        plt.plot_size(self.width, self.height)

        colors = ["cyan", "yellow", "green", "red", "magenta"]
        for i, (label, values) in enumerate(data.items()):
            color = colors[i % len(colors)]
            plt.plot(values, label=label, color=color, marker="braille")

        plt.title(title)
        plt.theme("dark")

        return plt.build()

    def forecast_chart(
        self,
        historical: list[float],
        forecast: list[float],
        lower_bound: list[float] | None = None,
        upper_bound: list[float] | None = None,
        title: str = "Forecast",
    ) -> str:
        """
        Generate forecast chart with confidence interval.

        Args:
            historical: Historical price data
            forecast: Forecasted values
            lower_bound: Lower confidence bound
            upper_bound: Upper confidence bound
            title: Chart title

        Returns:
            ASCII chart string
        """
        plt.clear_figure()
        plt.plot_size(self.width, self.height)

        # Historical data
        plt.plot(historical, label="Historical", color="cyan", marker="braille")

        # Forecast data (offset by historical length)
        forecast_x = list(range(len(historical) - 1, len(historical) + len(forecast) - 1))
        plt.plot(forecast_x, forecast, label="Forecast", color="yellow", marker="braille")

        # Confidence interval
        if lower_bound and upper_bound:
            plt.plot(forecast_x, lower_bound, color="gray", marker="braille")
            plt.plot(forecast_x, upper_bound, color="gray", marker="braille")

        plt.title(title)
        plt.theme("dark")

        return plt.build()

    def rsi_chart(
        self,
        rsi_values: list[float],
        title: str = "RSI",
    ) -> str:
        """
        Generate RSI chart with overbought/oversold lines.

        Args:
            rsi_values: RSI values
            title: Chart title

        Returns:
            ASCII chart string
        """
        plt.clear_figure()
        plt.plot_size(self.width, self.height // 2)

        plt.plot(rsi_values, color="cyan", marker="braille")
        # Overbought/oversold lines
        plt.hline(70, color="red")
        plt.hline(30, color="green")

        plt.title(title)
        plt.ylim(0, 100)
        plt.theme("dark")

        return plt.build()


def generate_sparkline(values: list[float], width: int = 20) -> str:
    """
    Generate simple sparkline using Unicode blocks.

    Args:
        values: List of values
        width: Sparkline width

    Returns:
        Sparkline string
    """
    if not values:
        return ""

    blocks = " ▁▂▃▄▅▆▇█"
    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        return blocks[4] * min(len(values), width)

    # Normalize and sample
    step = max(1, len(values) // width)
    sampled = values[::step][:width]

    result = ""
    for v in sampled:
        normalized = (v - min_val) / (max_val - min_val)
        idx = int(normalized * (len(blocks) - 1))
        result += blocks[idx]

    return result
