"""Input validators for Pulse CLI."""

import re
from datetime import datetime, timedelta


def validate_ticker(ticker: str) -> tuple[bool, str]:
    """
    Validate an Indonesian stock ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Tuple of (is_valid, normalized_ticker or error_message)
    """
    if not ticker:
        return False, "Ticker cannot be empty"

    # Normalize: uppercase, strip whitespace
    normalized = ticker.upper().strip()

    # Remove .JK suffix if present (yfinance format)
    if normalized.endswith(".JK"):
        normalized = normalized[:-3]

    # IDX tickers are 4 characters, alphabetic
    if not re.match(r"^[A-Z]{4}$", normalized):
        return False, f"Invalid ticker format: {ticker}. Expected 4 letters (e.g., BBCA)"

    return True, normalized


def validate_date(date_str: str) -> tuple[bool, str]:
    """
    Validate and normalize a date string.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Tuple of (is_valid, YYYY-MM-DD format or error_message)
    """
    if not date_str:
        return False, "Date cannot be empty"

    # Try various formats
    formats = [
        "%Y-%m-%d",  # 2024-01-15
        "%d-%m-%Y",  # 15-01-2024
        "%d/%m/%Y",  # 15/01/2024
        "%Y/%m/%d",  # 2024/01/15
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return True, dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try relative dates
    date_lower = date_str.lower().strip()
    today = datetime.now()

    if date_lower in ("today", "hari ini"):
        return True, today.strftime("%Y-%m-%d")
    elif date_lower in ("yesterday", "kemarin"):
        return True, (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_lower in ("last week", "minggu lalu"):
        return True, (today - timedelta(weeks=1)).strftime("%Y-%m-%d")
    elif date_lower in ("last month", "bulan lalu"):
        return True, (today - timedelta(days=30)).strftime("%Y-%m-%d")

    return False, f"Invalid date format: {date_str}. Use YYYY-MM-DD"


def validate_date_range(
    start_date: str,
    end_date: str,
) -> tuple[bool, tuple[str, str] | str]:
    """
    Validate a date range.
    
    Args:
        start_date: Start date string
        end_date: End date string
        
    Returns:
        Tuple of (is_valid, (start, end) or error_message)
    """
    valid_start, result_start = validate_date(start_date)
    if not valid_start:
        return False, result_start

    valid_end, result_end = validate_date(end_date)
    if not valid_end:
        return False, result_end

    # Check that start <= end
    if result_start > result_end:
        return False, f"Start date ({result_start}) must be before end date ({result_end})"

    return True, (result_start, result_end)


def validate_period(period: str) -> tuple[bool, str]:
    """
    Validate a period string for yfinance.
    
    Args:
        period: Period string (e.g., "1d", "5d", "1mo", "3mo", "1y")
        
    Returns:
        Tuple of (is_valid, normalized_period or error_message)
    """
    valid_periods = {
        "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
    }

    normalized = period.lower().strip()

    if normalized in valid_periods:
        return True, normalized

    return False, f"Invalid period: {period}. Valid: {', '.join(sorted(valid_periods))}"


def validate_indicator(indicator: str) -> tuple[bool, str]:
    """
    Validate a technical indicator name.
    
    Args:
        indicator: Indicator name
        
    Returns:
        Tuple of (is_valid, normalized_indicator or error_message)
    """
    valid_indicators = {
        "rsi", "macd", "sma", "ema", "bb", "bollinger",
        "stoch", "stochastic", "atr", "adx", "obv",
        "vwap", "mfi", "cci", "williams", "roc",
    }

    normalized = indicator.lower().strip()

    # Handle aliases
    aliases = {
        "bollinger": "bb",
        "stochastic": "stoch",
    }

    if normalized in aliases:
        normalized = aliases[normalized]

    if normalized in valid_indicators:
        return True, normalized

    return False, f"Invalid indicator: {indicator}. Valid: {', '.join(sorted(valid_indicators))}"


def validate_broker_code(code: str) -> tuple[bool, str]:
    """
    Validate a broker code.
    
    Args:
        code: Broker code (e.g., "YU", "PD")
        
    Returns:
        Tuple of (is_valid, normalized_code or error_message)
    """
    if not code:
        return False, "Broker code cannot be empty"

    normalized = code.upper().strip()

    if not re.match(r"^[A-Z]{2}$", normalized):
        return False, f"Invalid broker code: {code}. Expected 2 letters (e.g., YU)"

    return True, normalized


def parse_screening_criteria(criteria: str) -> tuple[bool, dict | str]:
    """
    Parse screening criteria string into structured format.
    
    Args:
        criteria: Criteria string (e.g., "rsi<30 and volume>1m")
        
    Returns:
        Tuple of (is_valid, parsed_criteria or error_message)
    """
    if not criteria:
        return False, "Criteria cannot be empty"

    # Simple parser for basic criteria
    # Format: indicator operator value [and/or indicator operator value]...

    parsed = {
        "conditions": [],
        "logic": "and",
    }

    # Split by 'and' / 'or'
    if " or " in criteria.lower():
        parts = re.split(r"\s+or\s+", criteria, flags=re.IGNORECASE)
        parsed["logic"] = "or"
    else:
        parts = re.split(r"\s+and\s+", criteria, flags=re.IGNORECASE)
        parsed["logic"] = "and"

    # Parse each condition
    pattern = r"^(\w+)\s*(>=|<=|>|<|=|==)\s*(\d+(?:\.\d+)?[kmbt]?)$"

    for part in parts:
        part = part.strip()
        match = re.match(pattern, part, re.IGNORECASE)

        if not match:
            return False, f"Invalid condition: {part}. Use format: indicator<operator>value"

        indicator = match.group(1).lower()
        operator = match.group(2)
        value_str = match.group(3).lower()

        # Parse value with suffix (k, m, b, t)
        multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000, "t": 1_000_000_000_000}

        if value_str[-1] in multipliers:
            value = float(value_str[:-1]) * multipliers[value_str[-1]]
        else:
            value = float(value_str)

        parsed["conditions"].append({
            "indicator": indicator,
            "operator": operator,
            "value": value,
        })

    return True, parsed
