"""
Pulse CLI - AI-powered Indonesian Stock Market Analysis

A powerful terminal-based stock analysis tool with:
- Multi-agent AI system for intelligent analysis
- Broker flow / bandar detection
- Technical & fundamental analysis
- Real-time market data from yfinance
- Interactive TUI with rich widgets
"""

__version__ = "0.1.0"
__author__ = "pulse-cli"

from pulse.core.config import settings

__all__ = ["settings", "__version__"]
