"""
SAPTA Data Models.

Defines all data structures for SAPTA decision engine.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SaptaStatus(str, Enum):
    """SAPTA decision status."""
    PRE_MARKUP = "PRE-MARKUP"   # >= threshold_high: Ready to breakout
    SIAP = "SIAP"               # >= threshold_mid: Almost ready
    WATCHLIST = "WATCHLIST"     # >= threshold_low: Monitor
    ABAIKAN = "ABAIKAN"         # < threshold_low: Skip


class ConfidenceLevel(str, Enum):
    """Confidence level based on score and ML prediction."""
    HIGH = "HIGH"       # High probability of success
    MEDIUM = "MEDIUM"   # Moderate probability
    LOW = "LOW"         # Low probability, more risk


class WavePhase(str, Enum):
    """Elliott Wave phase."""
    WAVE_1 = "wave1"
    WAVE_2 = "wave2"
    WAVE_3 = "wave3"
    WAVE_4 = "wave4"
    WAVE_5 = "wave5"
    WAVE_A = "wave_a"
    WAVE_B = "wave_b"
    WAVE_C = "wave_c"
    UNKNOWN = "unknown"


@dataclass
class ModuleScore:
    """Score from a single SAPTA module."""
    module_name: str
    score: float                 # Actual score
    max_score: float             # Maximum possible score
    status: bool                 # True if condition met
    details: str                 # Human-readable explanation
    signals: list[str] = field(default_factory=list)
    raw_features: dict[str, Any] = field(default_factory=dict)  # For ML

    @property
    def score_pct(self) -> float:
        """Score as percentage of max."""
        if self.max_score == 0:
            return 0.0
        return (self.score / self.max_score) * 100


@dataclass
class ModuleFeatures:
    """Raw features extracted by a module (for ML training)."""
    module_name: str
    features: dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


class SaptaConfig(BaseModel):
    """Configuration for SAPTA engine."""

    # Threshold settings (will be learned by ML)
    threshold_pre_markup: float = 80.0
    threshold_siap: float = 65.0
    threshold_watchlist: float = 50.0

    # Module weights (will be learned by ML)
    weight_absorption: float = 1.0
    weight_compression: float = 1.0
    weight_bb_squeeze: float = 1.0
    weight_elliott: float = 1.0
    weight_time_projection: float = 1.0
    weight_anti_distribution: float = 1.0

    # Module max scores
    max_absorption: float = 20.0
    max_compression: float = 15.0
    max_bb_squeeze: float = 15.0
    max_elliott: float = 20.0
    max_time_projection: float = 15.0
    max_anti_distribution: float = 15.0

    # Target for ML labeling
    target_gain_pct: float = 10.0       # 10% gain
    target_days: int = 20               # within 20 trading days

    # Fibonacci time windows
    fib_time_windows: list[int] = Field(default=[21, 34, 55, 89, 144])
    fib_time_tolerance: int = 3         # days

    # False breakout filter
    false_break_candles: int = 3        # min candles to confirm breakout
    false_break_penalty: float = 10.0   # score penalty

    # Minimum data requirements
    min_history_days: int = 120

    @property
    def max_total_score(self) -> float:
        """Maximum possible total score."""
        return (
            self.max_absorption +
            self.max_compression +
            self.max_bb_squeeze +
            self.max_elliott +
            self.max_time_projection +
            self.max_anti_distribution
        )


class SaptaResult(BaseModel):
    """Complete SAPTA analysis result."""
    ticker: str
    timeframe: str = "D"
    analyzed_at: datetime = Field(default_factory=datetime.now)

    # Scores
    total_score: float = 0.0
    weighted_score: float = 0.0  # After applying ML weights
    max_possible_score: float = 100.0

    # Module results
    absorption: dict[str, Any] | None = None
    compression: dict[str, Any] | None = None
    bb_squeeze: dict[str, Any] | None = None
    elliott: dict[str, Any] | None = None
    time_projection: dict[str, Any] | None = None
    anti_distribution: dict[str, Any] | None = None

    # Decision
    status: SaptaStatus = SaptaStatus.ABAIKAN
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    ml_probability: float | None = None  # ML model prediction probability

    # Time projection
    projected_breakout_window: str | None = None
    projected_dates: tuple[str, str] | None = None
    days_to_window: int | None = None

    # Elliott context
    wave_phase: str | None = None
    fib_retracement: float | None = None

    # Explainability (critical for SAPTA)
    notes: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Penalties
    penalties: list[str] = Field(default_factory=list)
    penalty_score: float = 0.0

    # Raw features (for ML) - can be float, int, bool, or None
    features: dict[str, Any] = Field(default_factory=dict)

    @property
    def final_score(self) -> float:
        """Score after penalties."""
        return max(0, self.weighted_score - self.penalty_score)

    @property
    def score_pct(self) -> float:
        """Final score as percentage."""
        return (self.final_score / self.max_possible_score) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ticker": self.ticker,
            "timeframe": self.timeframe,
            "sapta_score": round(self.final_score, 1),
            "status": self.status.value,
            "confidence": self.confidence.value,
            "ml_probability": round(self.ml_probability, 3) if self.ml_probability else None,
            "projected_breakout_window": self.projected_breakout_window,
            "wave_phase": self.wave_phase,
            "notes": self.notes,
            "warnings": self.warnings,
        }


@dataclass
class BacktestTrade:
    """Single trade in backtest."""
    ticker: str
    entry_date: date
    entry_price: float
    exit_date: date | None = None
    exit_price: float | None = None
    sapta_score: float = 0.0
    sapta_status: str = ""
    pnl: float = 0.0
    return_pct: float = 0.0
    holding_days: int = 0
    hit_target: bool = False
    hit_stop: bool = False


@dataclass
class BacktestResult:
    """Backtest results."""
    start_date: date
    end_date: date
    initial_capital: float
    final_capital: float

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    # Performance metrics
    win_rate: float = 0.0
    avg_return: float = 0.0
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0

    # Trade details
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)

    # By status breakdown
    trades_by_status: dict[str, int] = field(default_factory=dict)
    returns_by_status: dict[str, float] = field(default_factory=dict)


@dataclass
class MLModelInfo:
    """Information about trained ML model."""
    model_version: str
    trained_at: datetime
    training_samples: int
    validation_samples: int

    # Performance on validation set
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    auc_roc: float = 0.0

    # Learned thresholds
    threshold_pre_markup: float = 80.0
    threshold_siap: float = 65.0
    threshold_watchlist: float = 50.0

    # Feature importance
    feature_importance: dict[str, float] = field(default_factory=dict)

    # Training config
    target_gain_pct: float = 10.0
    target_days: int = 20
    tickers_used: list[str] = field(default_factory=list)
