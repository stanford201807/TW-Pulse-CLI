"""Formatting utilities for Pulse CLI."""


def format_currency(
    value: int | float,
    currency: str = "NT$",
    decimal_places: int = 0,
) -> str:
    """
    Format a number as Taiwan Dollar or other currency.

    Args:
        value: The numeric value
        currency: Currency symbol (default: NT$)
        decimal_places: Number of decimal places

    Returns:
        Formatted currency string
    """
    if value is None:
        return "-"

    # Handle negative values
    sign = "-" if value < 0 else ""
    abs_value = abs(value)

    # Format with thousand separators
    if decimal_places > 0:
        formatted = f"{abs_value:,.{decimal_places}f}"
    else:
        formatted = f"{abs_value:,.0f}"

    return f"{sign}{currency} {formatted}"


def format_number(
    value: int | float,
    decimal_places: int = 2,
    use_separator: bool = True,
) -> str:
    """
    Format a number with proper separators.

    Args:
        value: The numeric value
        decimal_places: Number of decimal places
        use_separator: Whether to use thousand separators

    Returns:
        Formatted number string
    """
    if value is None:
        return "-"

    if use_separator:
        if decimal_places > 0:
            return f"{value:,.{decimal_places}f}"
        return f"{value:,.0f}"
    else:
        if decimal_places > 0:
            return f"{value:.{decimal_places}f}"
        return f"{value:.0f}"


def format_percent(
    value: int | float,
    decimal_places: int = 2,
    show_sign: bool = True,
) -> str:
    """
    Format a number as percentage.

    Args:
        value: The numeric value (already in percentage, not decimal)
        decimal_places: Number of decimal places
        show_sign: Whether to show + sign for positive values

    Returns:
        Formatted percentage string
    """
    if value is None:
        return "-"

    sign = ""
    if show_sign and value > 0:
        sign = "+"

    return f"{sign}{value:.{decimal_places}f}%"


def format_volume(value: int | float) -> str:
    """
    Format volume with appropriate suffix (K, M, B, T).

    Args:
        value: The volume value

    Returns:
        Formatted volume string
    """
    if value is None:
        return "-"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000_000:.2f}T"
    elif abs_value >= 1_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000:.2f}B"
    elif abs_value >= 1_000_000:
        return f"{sign}{abs_value / 1_000_000:.2f}M"
    elif abs_value >= 1_000:
        return f"{sign}{abs_value / 1_000:.2f}K"
    else:
        return f"{sign}{abs_value:.0f}"


def format_market_cap(value: int | float) -> str:
    """
    Format market cap in Taiwan style (兆 for trillion, 億 for hundred million).

    Args:
        value: Market cap value in TWD

    Returns:
        Formatted market cap string
    """
    if value is None:
        return "-"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    # 兆 = 10^12 (trillion)
    # 億 = 10^8 (hundred million)
    # 萬 = 10^4 (ten thousand)

    if abs_value >= 1_000_000_000_000:
        return f"{sign}NT$ {abs_value / 1_000_000_000_000:.2f} 兆"
    elif abs_value >= 100_000_000:
        return f"{sign}NT$ {abs_value / 100_000_000:.2f} 億"
    elif abs_value >= 10_000:
        return f"{sign}NT$ {abs_value / 10_000:.2f} 萬"
    else:
        return f"{sign}NT$ {abs_value:,.0f}"


def format_lots(shares: int, lot_size: int = 1000) -> str:
    """
    Convert shares to lots (Taiwan standard: 1 lot = 1000 shares).

    Args:
        shares: Number of shares
        lot_size: Shares per lot (default: 1000 for Taiwan)

    Returns:
        Formatted lots string
    """
    if shares is None:
        return "-"

    lots = shares // lot_size
    return format_volume(lots) + " 張"


def format_shares(shares: int) -> str:
    """
    Format number of shares with appropriate suffix.

    Args:
        shares: Number of shares

    Returns:
        Formatted shares string
    """
    if shares is None:
        return "-"

    return format_volume(shares) + " 股"


def colorize_change(value: int | float, formatted: str) -> str:
    """
    Add color markup based on positive/negative value.

    Args:
        value: The numeric value
        formatted: Already formatted string

    Returns:
        String with Rich color markup
    """
    if value is None:
        return formatted

    if value > 0:
        return f"[green]{formatted}[/green]"
    elif value < 0:
        return f"[red]{formatted}[/red]"
    else:
        return f"[dim]{formatted}[/dim]"


def format_price(value: float, decimal_places: int = 2) -> str:
    """
    Format stock price.

    Args:
        value: Price value
        decimal_places: Number of decimal places

    Returns:
        Formatted price string
    """
    if value is None:
        return "-"

    return f"{value:,.{decimal_places}f}"


def format_institutional_flow(value: int | float, investor_type: str = "") -> str:
    """
    Format institutional investor flow with appropriate sign and suffix.

    Args:
        value: Net buy/sell value
        investor_type: Type of investor (外資/投信/自營商)

    Returns:
        Formatted flow string with color markup
    """
    if value is None:
        return "-"

    formatted = format_volume(value)

    if investor_type:
        formatted = f"{investor_type}: {formatted}"

    return colorize_change(value, formatted)
