"""Data models for bandarmology analysis."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, List, Dict

from pydantic import BaseModel, Field

from pulse.core.analysis.bandarmology.broker_profiles import BrokerProfile
from pulse.core.models import SignalType, BrokerSummary


class AccumulationPhase(str, Enum):
    """Accumulation/distribution phase detection."""

    EARLY_ACCUMULATION = "Early Accumulation"  # 2-3 days consistent buying
    MID_ACCUMULATION = "Mid Accumulation"  # 4-6 days
    LATE_ACCUMULATION = "Late Accumulation"  # 7+ days, almost ready
    MARKUP_READY = "Markup Ready"  # All signals align, go time!
    MARKUP = "Markup"  # Price rising with volume
    EARLY_DISTRIBUTION = "Early Distribution"  # Smart money starting to exit
    MID_DISTRIBUTION = "Mid Distribution"  # Distribution ongoing
    LATE_DISTRIBUTION = "Late Distribution"  # Almost done distributing
    MARKDOWN = "Markdown"  # Price falling
    NEUTRAL = "Neutral"  # No clear phase
    UNKNOWN = "Unknown"


class BandarPattern(str, Enum):
    """Detected bandarmology patterns."""

    CROSSING = "Crossing"  # Same broker on both sides
    DOMINASI = "Dominasi"  # Single broker > 30% volume
    ROTASI = "Rotasi"  # Foreign out, local in (or vice versa)
    RETAIL_TRAP = "Retail Trap"  # Retail buy while smart sell
    SMART_MONEY_ENTRY = "Smart Money Entry"  # Smart money accumulating
    SMART_MONEY_EXIT = "Smart Money Exit"  # Smart money distributing
    SILENT_ACCUMULATION = "Silent Accumulation"  # Low volume consistent buying
    VOLUME_SPIKE = "Volume Spike"  # Sudden volume increase
    DISTRIBUTION_SETUP = "Distribution Setup"  # Signs of upcoming distribution
    MARKUP_SIGNAL = "Markup Signal"  # Ready for markup
    BROKER_CONSISTENCY = "Broker Consistency"  # Same brokers multiple days


class PatternSeverity(str, Enum):
    """Severity/importance of detected pattern."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class PatternAlert(BaseModel):
    """Alert for a detected pattern."""

    pattern: BandarPattern
    severity: PatternSeverity
    description: str
    brokers_involved: List[str] = Field(default_factory=list)
    value: Optional[float] = None  # Relevant value (e.g., percentage)
    is_bullish: bool = True

    def to_string(self) -> str:
        """Format alert as string."""
        icon = "+" if self.is_bullish else "!"
        return f"[{icon}] [{self.pattern.value}] {self.description}"


class BrokerDayActivity(BaseModel):
    """Single broker's activity for one day."""

    code: str
    name: Optional[str] = None
    profile: BrokerProfile = BrokerProfile.UNKNOWN

    buy_lot: int = 0
    buy_value: float = 0.0
    sell_lot: int = 0
    sell_value: float = 0.0

    @property
    def net_lot(self) -> int:
        return self.buy_lot - self.sell_lot

    @property
    def net_value(self) -> float:
        return self.buy_value - self.sell_value

    @property
    def is_net_buyer(self) -> bool:
        return self.net_value > 0


class DailyFlow(BaseModel):
    """Flow data for a single day."""

    date: datetime
    ticker: str

    # Overall flow
    total_buy_value: float = 0.0
    total_sell_value: float = 0.0
    net_value: float = 0.0

    # Foreign flow
    foreign_net_value: float = 0.0
    foreign_net_lot: int = 0

    # By profile
    smart_money_net: float = 0.0
    bandar_net: float = 0.0
    retail_net: float = 0.0
    local_inst_net: float = 0.0
    market_maker_net: float = 0.0

    # Accumulation/Distribution
    accdist: str = "Neutral"
    is_accumulation: bool = False
    is_distribution: bool = False

    # Top brokers
    top_buyer_code: Optional[str] = None
    top_buyer_value: float = 0.0
    top_seller_code: Optional[str] = None
    top_seller_value: float = 0.0

    # Concentration
    top1_percent: float = 0.0
    top5_percent: float = 0.0

    # Counts
    total_buyers: int = 0
    total_sellers: int = 0

    @property
    def buyer_seller_ratio(self) -> float:
        if self.total_sellers == 0:
            return float("inf") if self.total_buyers > 0 else 0.0
        return self.total_buyers / self.total_sellers


class CumulativeFlow(BaseModel):
    """Cumulative flow over multiple days."""

    ticker: str
    period_days: int
    start_date: datetime
    end_date: datetime

    # Cumulative values
    total_foreign_net: float = 0.0
    total_smart_money_net: float = 0.0
    total_bandar_net: float = 0.0
    total_retail_net: float = 0.0
    total_local_inst_net: float = 0.0

    # Daily flows
    daily_flows: List[DailyFlow] = Field(default_factory=list)

    # Streaks
    accumulation_days: int = 0
    distribution_days: int = 0
    current_streak: int = 0  # Positive = acc streak, negative = dist streak

    # Broker consistency
    consistent_buyers: Dict[str, int] = Field(default_factory=dict)  # code -> days
    consistent_sellers: Dict[str, int] = Field(default_factory=dict)

    # Trends
    foreign_trend: List[float] = Field(default_factory=list)  # Daily foreign net
    volume_trend: List[float] = Field(default_factory=list)  # Daily volume

    @property
    def is_accumulating(self) -> bool:
        return self.current_streak > 0

    @property
    def is_distributing(self) -> bool:
        return self.current_streak < 0

    @property
    def most_consistent_buyer(self) -> Optional[str]:
        if not self.consistent_buyers:
            return None
        return max(self.consistent_buyers, key=self.consistent_buyers.get)

    @property
    def most_consistent_seller(self) -> Optional[str]:
        if not self.consistent_sellers:
            return None
        return max(self.consistent_sellers, key=self.consistent_sellers.get)


class BrokerComposition(BaseModel):
    """Composition of broker activity by profile."""

    smart_money_percent: float = 0.0
    smart_money_net: float = 0.0

    bandar_percent: float = 0.0
    bandar_net: float = 0.0

    retail_percent: float = 0.0
    retail_net: float = 0.0

    local_inst_percent: float = 0.0
    local_inst_net: float = 0.0

    market_maker_percent: float = 0.0
    market_maker_net: float = 0.0

    unknown_percent: float = 0.0
    unknown_net: float = 0.0


class BandarmologyResult(BaseModel):
    """Complete bandarmology analysis result."""

    ticker: str
    analyzed_at: datetime = Field(default_factory=datetime.now)
    period_days: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # ========== Scores ==========
    flow_momentum_score: int = 50  # 0-100
    markup_readiness_score: int = 50  # 0-100
    confidence: int = 50  # 0-100

    # ========== Phase & Signal ==========
    accumulation_phase: AccumulationPhase = AccumulationPhase.UNKNOWN
    signal: SignalType = SignalType.NEUTRAL

    # ========== Flow Analysis ==========
    cumulative_flow: Optional[CumulativeFlow] = None
    broker_composition: Optional[BrokerComposition] = None

    # ========== Patterns ==========
    patterns: List[BandarPattern] = Field(default_factory=list)
    pattern_alerts: List[PatternAlert] = Field(default_factory=list)

    # ========== Key Metrics ==========
    foreign_net_total: float = 0.0
    smart_money_net_total: float = 0.0
    retail_net_total: float = 0.0

    accumulation_streak: int = 0
    distribution_warning: bool = False

    top5_consistency_score: float = 0.0  # How consistent top 5 brokers

    # ========== Top Brokers ==========
    most_consistent_buyer: Optional[str] = None
    most_consistent_buyer_days: int = 0
    most_consistent_seller: Optional[str] = None
    most_consistent_seller_days: int = 0

    # ========== Insights ==========
    insights: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommendation: str = ""

    # ========== Raw Data ==========
    raw_summaries: List[BrokerSummary] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def get_signal_emoji(self) -> str:
        """Get emoji for signal."""
        emoji_map = {
            SignalType.STRONG_BUY: "🟢🟢",
            SignalType.BUY: "🟢",
            SignalType.NEUTRAL: "🟡",
            SignalType.SELL: "🔴",
            SignalType.STRONG_SELL: "🔴🔴",
        }
        return emoji_map.get(self.signal, "⚪")

    def get_phase_emoji(self) -> str:
        """Get emoji for phase."""
        phase_emojis = {
            AccumulationPhase.EARLY_ACCUMULATION: "📥",
            AccumulationPhase.MID_ACCUMULATION: "📦",
            AccumulationPhase.LATE_ACCUMULATION: "📈",
            AccumulationPhase.MARKUP_READY: "🚀",
            AccumulationPhase.MARKUP: "💹",
            AccumulationPhase.EARLY_DISTRIBUTION: "📤",
            AccumulationPhase.MID_DISTRIBUTION: "⚠️",
            AccumulationPhase.LATE_DISTRIBUTION: "🔻",
            AccumulationPhase.MARKDOWN: "📉",
        }
        return phase_emojis.get(self.accumulation_phase, "❓")
