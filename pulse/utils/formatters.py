"""Formatting utilities for Pulse CLI."""



def format_currency(
    value: int | float,
    currency: str = "Rp",
    decimal_places: int = 0,
) -> str:
    """
    Format a number as Indonesian Rupiah or other currency.
    
    Args:
        value: The numeric value
        currency: Currency symbol (default: Rp)
        decimal_places: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    if value is None:
        return "-"

    # Handle negative values
    sign = "-" if value < 0 else ""
    abs_value = abs(value)

    # Format with thousand separators (Indonesian style uses dot)
    if decimal_places > 0:
        formatted = f"{abs_value:,.{decimal_places}f}"
    else:
        formatted = f"{abs_value:,.0f}"

    # Replace comma with dot for Indonesian format
    formatted = formatted.replace(",", ".")

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
    Format market cap in Indonesian style (T for Triliun, M for Miliar).
    
    Args:
        value: Market cap value in IDR
        
    Returns:
        Formatted market cap string
    """
    if value is None:
        return "-"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000_000:
        return f"{sign}Rp {abs_value / 1_000_000_000_000:.2f} T"
    elif abs_value >= 1_000_000_000:
        return f"{sign}Rp {abs_value / 1_000_000_000:.2f} M"
    elif abs_value >= 1_000_000:
        return f"{sign}Rp {abs_value / 1_000_000:.2f} Jt"
    else:
        return f"{sign}Rp {abs_value:,.0f}"


def format_lots(shares: int, lot_size: int = 100) -> str:
    """
    Convert shares to lots (IDX standard: 1 lot = 100 shares).
    
    Args:
        shares: Number of shares
        lot_size: Shares per lot (default: 100)
        
    Returns:
        Formatted lots string
    """
    if shares is None:
        return "-"

    lots = shares // lot_size
    return format_volume(lots) + " lot"


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
