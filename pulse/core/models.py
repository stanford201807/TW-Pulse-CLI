"""Data models for Pulse CLI."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BrokerType(str, Enum):
    """Broker type classification."""

    ASING = "Asing"
    LOKAL = "Lokal"
    UNKNOWN = "Unknown"


class AccDistType(str, Enum):
    """Accumulation/Distribution type."""

    ACCUMULATION = "Acc"
    DISTRIBUTION = "Dist"
    SMALL_ACC = "Small Acc"
    SMALL_DIST = "Small Dist"
    NEUTRAL = "Neutral"


class SignalType(str, Enum):
    """Trading signal type."""

    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    NEUTRAL = "Neutral"
    SELL = "Sell"
    STRONG_SELL = "Strong Sell"


class TrendType(str, Enum):
    """Trend direction."""

    BULLISH = "Bullish"
    BEARISH = "Bearish"
    SIDEWAYS = "Sideways"


# ============== Stock Data Models ==============


class OHLCV(BaseModel):
    """Single OHLCV data point."""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    @property
    def change(self) -> float:
        """Calculate price change."""
        return self.close - self.open

    @property
    def change_percent(self) -> float:
        """Calculate price change percentage."""
        if self.open == 0:
            return 0.0
        return ((self.close - self.open) / self.open) * 100


class StockData(BaseModel):
    """Complete stock data with historical prices."""

    ticker: str
    name: str | None = None
    sector: str | None = None
    industry: str | None = None

    # Current price info
    current_price: float = 0.0
    previous_close: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0

    # Volume info
    volume: int = 0
    avg_volume: int = 0

    # Price range
    day_low: float = 0.0
    day_high: float = 0.0
    week_52_low: float = 0.0
    week_52_high: float = 0.0

    # Market info
    market_cap: float | None = None
    shares_outstanding: int | None = None

    # Historical data
    history: list[OHLCV] = Field(default_factory=list)

    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============== Broker Data Models ==============


class BrokerTransaction(BaseModel):
    """Single broker transaction data."""

    broker_code: str
    broker_name: str | None = None
    broker_type: BrokerType = BrokerType.UNKNOWN

    # Buy side
    buy_lot: int = 0
    buy_value: float = 0.0
    buy_avg_price: float = 0.0

    # Sell side
    sell_lot: int = 0
    sell_value: float = 0.0
    sell_avg_price: float = 0.0

    # Net
    net_lot: int = 0
    net_value: float = 0.0

    @property
    def is_net_buyer(self) -> bool:
        return self.net_value > 0

    @property
    def is_net_seller(self) -> bool:
        return self.net_value < 0


class BandarDetector(BaseModel):
    """Bandar/smart money detection data."""

    average: float = 0.0
    broker_accdist: AccDistType = AccDistType.NEUTRAL

    # Top broker analysis
    top1_accdist: AccDistType | None = None
    top1_amount: float = 0.0
    top1_percent: float = 0.0

    top5_accdist: AccDistType | None = None
    top5_amount: float = 0.0
    top5_percent: float = 0.0

    # Broker counts
    total_buyer: int = 0
    total_seller: int = 0

    @property
    def buyer_seller_ratio(self) -> float:
        """Calculate buyer to seller ratio."""
        if self.total_seller == 0:
            return float("inf") if self.total_buyer > 0 else 0.0
        return self.total_buyer / self.total_seller


class BrokerSummary(BaseModel):
    """Complete broker summary for a ticker."""

    ticker: str
    date: datetime

    # Broker lists
    top_buyers: list[BrokerTransaction] = Field(default_factory=list)
    top_sellers: list[BrokerTransaction] = Field(default_factory=list)

    # Bandar detection
    bandar: BandarDetector | None = None

    # Foreign flow
    foreign_net_buy: float = 0.0
    foreign_net_lot: int = 0

    # Summary stats
    total_buy_value: float = 0.0
    total_sell_value: float = 0.0
    net_value: float = 0.0

    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.now)
    raw_data: dict[str, Any] | None = None


class BrokerData(BaseModel):
    """Broker flow data for analysis."""

    ticker: str
    summaries: list[BrokerSummary] = Field(default_factory=list)

    @property
    def latest(self) -> BrokerSummary | None:
        """Get latest broker summary."""
        if not self.summaries:
            return None
        return max(self.summaries, key=lambda x: x.date)

    def get_foreign_flow_trend(self, days: int = 5) -> list[float]:
        """Get foreign flow trend for last N days."""
        sorted_summaries = sorted(self.summaries, key=lambda x: x.date, reverse=True)
        return [s.foreign_net_buy for s in sorted_summaries[:days]]


# ============== Technical Indicators ==============


class TechnicalIndicators(BaseModel):
    """Technical analysis indicators."""

    ticker: str
    calculated_at: datetime = Field(default_factory=datetime.now)

    # Trend indicators
    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    ema_9: float | None = None
    ema_21: float | None = None
    ema_55: float | None = None

    # Momentum indicators
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    stoch_k: float | None = None
    stoch_d: float | None = None

    # Volatility indicators
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    bb_width: float | None = None
    atr_14: float | None = None

    # Volume indicators
    obv: float | None = None
    vwap: float | None = None
    mfi_14: float | None = None
    volume_sma_20: float | None = None

    # Support/Resistance
    support_1: float | None = None
    support_2: float | None = None
    resistance_1: float | None = None
    resistance_2: float | None = None

    # Signals
    trend: TrendType = TrendType.SIDEWAYS
    signal: SignalType = SignalType.NEUTRAL

    def to_summary(self) -> dict[str, Any]:
        """Generate summary dict for display."""
        return {
            "RSI": self.rsi_14,
            "MACD": self.macd,
            "SMA 20": self.sma_20,
            "SMA 50": self.sma_50,
            "SMA 200": self.sma_200,
            "BB Upper": self.bb_upper,
            "BB Lower": self.bb_lower,
            "ATR": self.atr_14,
            "Trend": self.trend.value,
            "Signal": self.signal.value,
        }


# ============== Fundamental Data ==============


class FundamentalData(BaseModel):
    """Fundamental analysis data."""

    ticker: str

    # Valuation ratios
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    ps_ratio: float | None = None
    peg_ratio: float | None = None
    ev_ebitda: float | None = None

    # Profitability
    roe: float | None = None
    roa: float | None = None
    npm: float | None = None  # Net Profit Margin
    opm: float | None = None  # Operating Profit Margin
    gpm: float | None = None  # Gross Profit Margin

    # Per share data
    eps: float | None = None
    bvps: float | None = None  # Book Value Per Share
    dps: float | None = None  # Dividend Per Share

    # Growth
    revenue_growth: float | None = None
    earnings_growth: float | None = None

    # Debt
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    quick_ratio: float | None = None

    # Dividend
    dividend_yield: float | None = None
    payout_ratio: float | None = None

    # Market data
    market_cap: float | None = None
    enterprise_value: float | None = None

    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.now)

    def to_summary(self) -> dict[str, Any]:
        """Generate summary dict for display."""
        return {
            "P/E Ratio": self.pe_ratio,
            "P/B Ratio": self.pb_ratio,
            "ROE": f"{self.roe:.2f}%" if self.roe else None,
            "ROA": f"{self.roa:.2f}%" if self.roa else None,
            "EPS": self.eps,
            "Debt/Equity": self.debt_to_equity,
            "Dividend Yield": f"{self.dividend_yield:.2f}%" if self.dividend_yield else None,
            "Market Cap": self.market_cap,
        }


# ============== Analysis Results ==============


class AnalysisResult(BaseModel):
    """Complete analysis result combining all data."""

    ticker: str
    analyzed_at: datetime = Field(default_factory=datetime.now)

    # Data components
    stock: StockData | None = None
    technical: TechnicalIndicators | None = None
    fundamental: FundamentalData | None = None
    broker: BrokerSummary | None = None

    # AI Analysis
    ai_summary: str | None = None
    ai_recommendation: SignalType | None = None
    ai_target_price: float | None = None
    ai_stop_loss: float | None = None
    ai_risk_level: str | None = None

    # Key insights
    key_insights: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)

    # Scores (0-100)
    technical_score: float | None = None
    fundamental_score: float | None = None
    broker_score: float | None = None
    overall_score: float | None = None


class ScreeningResult(BaseModel):
    """Stock screening result."""

    screened_at: datetime = Field(default_factory=datetime.now)
    criteria: dict[str, Any] = Field(default_factory=dict)

    # Results
    matches: list[str] = Field(default_factory=list)  # Matching tickers
    results: list[dict[str, Any]] = Field(default_factory=list)  # Detailed results

    # Stats
    total_screened: int = 0
    total_matches: int = 0

    @property
    def match_rate(self) -> float:
        """Calculate match rate percentage."""
        if self.total_screened == 0:
            return 0.0
        return (self.total_matches / self.total_screened) * 100


class SectorAnalysis(BaseModel):
    """Sector-level analysis."""

    sector: str
    analyzed_at: datetime = Field(default_factory=datetime.now)

    # Sector stats
    total_stocks: int = 0
    avg_change_percent: float = 0.0
    total_volume: int = 0
    total_value: float = 0.0

    # Top performers
    top_gainers: list[dict[str, Any]] = Field(default_factory=list)
    top_losers: list[dict[str, Any]] = Field(default_factory=list)
    most_active: list[dict[str, Any]] = Field(default_factory=list)

    # Foreign flow
    sector_foreign_net: float = 0.0

    # AI insights
    ai_summary: str | None = None
    outlook: str | None = None


class TradeQuality(str, Enum):
    """Trade quality based on risk/reward ratio."""

    EXCELLENT = "Excellent"  # RR >= 3.0
    GOOD = "Good"  # RR >= 2.0
    FAIR = "Fair"  # RR >= 1.5
    POOR = "Poor"  # RR < 1.5


class TradeValidity(str, Enum):
    """Trade validity/timeframe."""

    INTRADAY = "Intraday"  # Same day
    SWING = "Swing"  # 3-10 days
    POSITION = "Position"  # Weeks to months


class TradingPlan(BaseModel):
    """Complete trading plan with entry, TP, SL, and RR calculations."""

    ticker: str
    generated_at: datetime = Field(default_factory=datetime.now)

    # Entry
    entry_price: float
    entry_type: str = "market"  # "market" | "limit" | "breakout"

    # Take Profit Levels (graduated exit strategy)
    tp1: float  # Conservative - nearest resistance
    tp1_percent: float  # % gain from entry
    tp2: float | None = None  # Moderate - resistance 2 or ATR-based
    tp2_percent: float | None = None
    tp3: float | None = None  # Aggressive - extended target
    tp3_percent: float | None = None

    # Stop Loss
    stop_loss: float
    stop_loss_percent: float  # % loss from entry (negative)
    stop_loss_method: str = "hybrid"  # "atr" | "support" | "percentage" | "hybrid"

    # Risk/Reward Analysis
    risk_amount: float  # Entry - SL (per share)
    reward_tp1: float  # TP1 - Entry (per share)
    reward_tp2: float | None = None
    rr_ratio_tp1: float  # e.g., 1.5 means 1:1.5
    rr_ratio_tp2: float | None = None

    # Trade Assessment
    trade_quality: TradeQuality = TradeQuality.FAIR
    confidence: int = 50  # 0-100
    validity: TradeValidity = TradeValidity.SWING

    # Position Sizing
    suggested_risk_percent: float = 2.0  # Default 2% of portfolio

    # Technical Context
    trend: TrendType = TrendType.SIDEWAYS
    signal: SignalType = SignalType.NEUTRAL
    rsi: float | None = None
    atr: float | None = None
    support_1: float | None = None
    support_2: float | None = None
    resistance_1: float | None = None
    resistance_2: float | None = None

    # Notes and Strategy
    notes: list[str] = Field(default_factory=list)
    execution_strategy: list[str] = Field(default_factory=list)
