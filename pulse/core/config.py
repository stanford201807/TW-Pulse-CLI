"""Configuration management for Pulse CLI."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """AI/LLM configuration."""

    base_url: str = Field(default="http://localhost:8317/v1", description="CLIProxyAPI base URL")
    api_key: str = Field(default="opencode", description="API key for CLIProxyAPI")
    default_model: str = Field(
        default="gemini-3-flash-preview", description="Default AI model to use"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Temperature for AI responses"
    )
    max_tokens: int = Field(
        default=4096, ge=100, le=32000, description="Maximum tokens for AI responses"
    )
    timeout: int = Field(default=120, description="Request timeout in seconds")

    # Available models from CLIProxyAPI
    available_models: dict[str, str] = Field(
        default={
            "gemini-3-flash-preview": "Gemini 3 Flash Preview [Antigravity]",
            "gemini-2.5-flash": "Gemini 2.5 Flash [Antigravity]",
            "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite [Antigravity]",
            "gemini-claude-sonnet-4-5": "Claude Sonnet 4.5 [Antigravity]",
            "gemini-claude-sonnet-4-5-thinking": "Claude Sonnet 4.5 Thinking [Antigravity]",
            "gemini-claude-opus-4-5-thinking": "Claude Opus 4.5 Thinking [Antigravity]",
            "gpt-oss-120b-medium": "GPT OSS 120B Medium [Antigravity]",
        }
    )


class StockbitSettings(BaseSettings):
    """Stockbit API configuration."""

    username: str | None = Field(default=None, description="Stockbit username")
    password: str | None = Field(default=None, description="Stockbit password")
    secrets_file: Path = Field(
        default=Path("data/stockbit/secrets.json"), description="Path to secrets file"
    )
    auth_state_file: Path = Field(
        default=Path("data/stockbit/auth_state.json"), description="Path to auth state file"
    )
    api_base_url: str = Field(
        default="https://exodus.stockbit.com", description="Stockbit API base URL"
    )
    headless: bool = Field(default=True, description="Run browser in headless mode")


class DataSettings(BaseSettings):
    """Data fetching and caching configuration."""

    cache_dir: Path = Field(default=Path("data/cache"), description="Cache directory")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds (1 hour)")
    yfinance_suffix: str = Field(default=".JK", description="yfinance ticker suffix for IDX")
    default_period: str = Field(default="3mo", description="Default historical data period")
    tickers_file: Path = Field(
        default=Path("data/tickers.json"), description="Path to tickers list file"
    )


class AnalysisSettings(BaseSettings):
    """Technical and fundamental analysis configuration."""

    # RSI settings
    rsi_period: int = Field(default=14, description="RSI period")
    rsi_oversold: float = Field(default=30.0, description="RSI oversold threshold")
    rsi_overbought: float = Field(default=70.0, description="RSI overbought threshold")

    # MACD settings
    macd_fast: int = Field(default=12, description="MACD fast period")
    macd_slow: int = Field(default=26, description="MACD slow period")
    macd_signal: int = Field(default=9, description="MACD signal period")

    # Moving averages
    sma_periods: list[int] = Field(default=[20, 50, 200], description="SMA periods")
    ema_periods: list[int] = Field(default=[9, 21, 55], description="EMA periods")

    # Bollinger Bands
    bb_period: int = Field(default=20, description="Bollinger Bands period")
    bb_std: float = Field(default=2.0, description="Bollinger Bands std deviation")

    # Volume
    volume_sma_period: int = Field(default=20, description="Volume SMA period")
    volume_spike_threshold: float = Field(
        default=2.0, description="Volume spike threshold (x times average)"
    )


class UISettings(BaseSettings):
    """UI/TUI configuration."""

    theme: str = Field(default="dark", description="UI theme (dark/light)")
    show_welcome: bool = Field(default=True, description="Show welcome message")
    history_size: int = Field(default=100, description="Command history size")
    max_results: int = Field(default=50, description="Max results to display")
    chart_width: int = Field(default=60, description="ASCII chart width")
    chart_height: int = Field(default=15, description="ASCII chart height")


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="PULSE_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application info
    app_name: str = Field(default="Pulse CLI", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # Sub-configurations
    ai: AISettings = Field(default_factory=AISettings)
    stockbit: StockbitSettings = Field(default_factory=StockbitSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)
    ui: UISettings = Field(default_factory=UISettings)

    # Paths
    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent, description="Base directory"
    )
    config_file: Path = Field(default=Path("config/pulse.yaml"), description="Config file path")
    log_file: Path | None = Field(default=Path("data/logs/pulse.log"), description="Log file path")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._load_config_file()
        self._ensure_directories()

    def _load_config_file(self) -> None:
        """Load settings from YAML config file if exists."""
        config_path = self.base_dir / self.config_file

        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f)

            if yaml_config:
                self._merge_config(yaml_config)

    def _merge_config(self, config: dict[str, Any]) -> None:
        """Merge YAML config into settings."""
        for key, value in config.items():
            if hasattr(self, key):
                current = getattr(self, key)
                if isinstance(current, BaseSettings) and isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if hasattr(current, sub_key):
                            setattr(current, sub_key, sub_value)
                else:
                    setattr(self, key, value)

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        dirs_to_create = [
            self.data.cache_dir,
            self.stockbit.secrets_file.parent,
            Path("data/broker_summary"),
            Path("data/reports"),
        ]

        if self.log_file:
            dirs_to_create.append(self.log_file.parent)

        for dir_path in dirs_to_create:
            full_path = self.base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

    def get_model_display_name(self, model_id: str) -> str:
        """Get display name for a model."""
        return self.ai.available_models.get(model_id, model_id)

    def list_models(self) -> list[dict[str, str]]:
        """List all available AI models."""
        return [
            {"id": model_id, "name": name} for model_id, name in self.ai.available_models.items()
        ]


# Global settings instance
settings = Settings()
