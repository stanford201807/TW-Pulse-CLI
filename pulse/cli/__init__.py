"""CLI module for Pulse TUI application."""

# Avoid circular import when running with python -m pulse.cli.app
# Import PulseApp and main only when explicitly needed
__all__ = [
    "PulseApp",
    "main",
]


def __getattr__(name):
    """Lazy import to avoid circular import issues."""
    if name in ("PulseApp", "main"):
        from pulse.cli.app import PulseApp, main

        return PulseApp if name == "PulseApp" else main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
