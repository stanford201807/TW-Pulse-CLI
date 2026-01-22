"""Configuration management for Pulse CLI."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Load .env file early before settings initialization
_env_loaded = False
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(_env_path)
        _env_loaded = True
    except ImportError:
        pass


class AISettings(BaseSettings):
    """AI/LLM configuration using LiteLLM for multi-provider support."""

    # Default provider and model (uses LiteLLM format: provider/model)
    default_model: str = Field(
        default="deepseek/deepseek-chat",
        description="Default AI model (format: provider/model)",
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Temperature for AI responses"
    )
    max_tokens: int = Field(
        default=4096, ge=100, le=32000, description="Maximum tokens for AI responses"
    )
    timeout: int = Field(default=120, description="Request timeout in seconds")

    # API endpoint customization (for proxies or custom deployments)
    gemini_api_base: str | None = Field(
        default=None,
        description="Custom API base URL for Gemini (e.g., http://127.0.0.1:8045)",
    )

    # Available models (LiteLLM format)
    # Users can set API keys via environment variables:
    # - ANTHROPIC_API_KEY for Anthropic models
    # - OPENAI_API_KEY for OpenAI models
    # - GEMINI_API_KEY for Google models
    # - GROQ_API_KEY for Groq models
    # - DEEPSEEK_API_KEY for DeepSeek models
    available_models: dict[str, str] = Field(
        default={
            # DeepSeek (Cost-effective, high performance)
            "deepseek/deepseek-chat": "DeepSeek Chat (DeepSeek)",
            # Anthropic
            "anthropic/claude-sonnet-4-20250514": "Claude Sonnet 4 (Anthropic)",
            "anthropic/claude-haiku-4-20250514": "Claude Haiku 4 (Anthropic)",
            # OpenAI
            "openai/gpt-4o": "GPT-4o (OpenAI)",
            "openai/gpt-4o-mini": "GPT-4o Mini (OpenAI)",
            # Google
            "gemini/gemini-2.0-flash": "Gemini 2.0 Flash (Google)",
            "gemini/gemini-2.5-flash-preview-05-20": "Gemini 2.5 Flash (Google)",
            "gemini/gemini-3-flash": "Gemini 3 Flash (Google)",
            "gemini/gemini-3-pro-high": "Gemini 3 Pro High (Google)",
            # Groq (free tier available)
            "groq/llama-3.3-70b-versatile": "Llama 3.3 70B (Groq)",
            "groq/llama-3.1-8b-instant": "Llama 3.1 8B (Groq)",
        }
    )


class DataSettings(BaseSettings):
    """Data fetching and caching configuration."""

    cache_dir: Path = Field(default=Path("data/cache"), description="Cache directory")
    cache_ttl: int = Field(default=3600, description="Default cache TTL in seconds (1 hour)")

    # Specific TTL configurations (in seconds)
    stock_cache_ttl: int = Field(default=1800, description="Stock price data TTL (30 minutes)")
    technical_cache_ttl: int = Field(default=3600, description="Technical indicators TTL (1 hour)")
    fundamental_cache_ttl: int = Field(default=86400, description="Fundamental data TTL (24 hours)")
    broker_cache_ttl: int = Field(
        default=86400, description="Broker/institutional data TTL (24 hours)"
    )

    # Cache optimization settings
    cache_preload_count: int = Field(default=10, description="Number of top stocks to preload")
    cache_warmup: bool = Field(default=True, description="Enable cache warmup on startup")

    yfinance_suffix: str = Field(default=".TW", description="yfinance ticker suffix for Taiwan")
    default_period: str = Field(default="3mo", description="Default historical data period")
    tickers_file: Path = Field(
        default=Path("data/tw_tickers.json"), description="Path to tickers list file"
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
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application info
    app_name: str = Field(default="Pulse CLI", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # Sub-configurations
    ai: AISettings = Field(default_factory=AISettings)
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
        # Set env_file to absolute path before initialization
        if "env_file" not in data:
            base = data.get("base_dir", Path(__file__).parent.parent.parent)
            data["env_file"] = str(base / ".env")
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
