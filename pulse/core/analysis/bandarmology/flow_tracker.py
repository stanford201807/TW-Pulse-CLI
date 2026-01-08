"""Multi-day flow tracking for bandarmology analysis."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from pulse.core.analysis.bandarmology.broker_profiles import (
    BrokerProfile,
    BrokerProfiler,
)
from pulse.core.analysis.bandarmology.models import (
    AccumulationPhase,
    CumulativeFlow,
    DailyFlow,
    BrokerComposition,
)
from pulse.core.data.stockbit import StockbitClient
from pulse.core.models import BrokerSummary, AccDistType
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class FlowTracker:
    """Track and analyze broker flow over multiple days."""

    def __init__(self):
        self.client = StockbitClient()
        self.profiler = BrokerProfiler()

    async def fetch_historical(
        self,
        ticker: str,
        days: int = 10,
        end_date: Optional[str] = None,
    ) -> List[BrokerSummary]:
        """
        Fetch broker summaries for last N trading days.

        Args:
            ticker: Stock ticker
            days: Number of trading days to fetch
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            List of BrokerSummary sorted by date (oldest first)
        """
        return await self.client.fetch_historical(ticker, days, end_date)

    def calculate_daily_flow(self, summary: BrokerSummary) -> DailyFlow:
        """Calculate flow metrics for a single day."""
        # Initialize profile nets
        profile_nets: Dict[BrokerProfile, float] = {p: 0.0 for p in BrokerProfile}

        # Process buyers
        for buyer in summary.top_buyers:
            profile = self.profiler.get_profile(buyer.broker_code)
            profile_nets[profile] += buyer.buy_value

        # Process sellers (subtract)
        for seller in summary.top_sellers:
            profile = self.profiler.get_profile(seller.broker_code)
            profile_nets[profile] -= seller.sell_value

        # Get top buyer/seller
        top_buyer_code = summary.top_buyers[0].broker_code if summary.top_buyers else None
        top_buyer_value = summary.top_buyers[0].buy_value if summary.top_buyers else 0.0
        top_seller_code = summary.top_sellers[0].broker_code if summary.top_sellers else None
        top_seller_value = summary.top_sellers[0].sell_value if summary.top_sellers else 0.0

        # Accumulation/Distribution detection
        accdist = "Neutral"
        is_acc = False
        is_dist = False

        if summary.bandar:
            accdist = summary.bandar.broker_accdist.value
            is_acc = summary.bandar.broker_accdist in [
                AccDistType.ACCUMULATION,
                AccDistType.SMALL_ACC,
            ]
            is_dist = summary.bandar.broker_accdist in [
                AccDistType.DISTRIBUTION,
                AccDistType.SMALL_DIST,
            ]

        return DailyFlow(
            date=summary.date,
            ticker=summary.ticker,
            total_buy_value=summary.total_buy_value,
            total_sell_value=summary.total_sell_value,
            net_value=summary.net_value,
            foreign_net_value=summary.foreign_net_buy,
            foreign_net_lot=summary.foreign_net_lot,
            smart_money_net=profile_nets.get(BrokerProfile.SMART_MONEY_FOREIGN, 0.0),
            bandar_net=profile_nets.get(BrokerProfile.BANDAR_GORENGAN, 0.0),
            retail_net=profile_nets.get(BrokerProfile.RETAIL, 0.0),
            local_inst_net=profile_nets.get(BrokerProfile.LOCAL_INSTITUTIONAL, 0.0),
            market_maker_net=profile_nets.get(BrokerProfile.MARKET_MAKER, 0.0),
            accdist=accdist,
            is_accumulation=is_acc,
            is_distribution=is_dist,
            top_buyer_code=top_buyer_code,
            top_buyer_value=top_buyer_value,
            top_seller_code=top_seller_code,
            top_seller_value=top_seller_value,
            top1_percent=summary.bandar.top1_percent if summary.bandar else 0.0,
            top5_percent=summary.bandar.top5_percent if summary.bandar else 0.0,
            total_buyers=summary.bandar.total_buyer if summary.bandar else 0,
            total_sellers=summary.bandar.total_seller if summary.bandar else 0,
        )

    def calculate_cumulative_flow(self, summaries: List[BrokerSummary]) -> CumulativeFlow:
        """
        Calculate cumulative flow metrics over multiple days.

        Args:
            summaries: List of BrokerSummary (should be sorted by date)

        Returns:
            CumulativeFlow with aggregated metrics
        """
        if not summaries:
            return CumulativeFlow(
                ticker="",
                period_days=0,
                start_date=datetime.now(),
                end_date=datetime.now(),
            )

        ticker = summaries[0].ticker

        # Calculate daily flows
        daily_flows = [self.calculate_daily_flow(s) for s in summaries]

        # Aggregate totals
        total_foreign_net = sum(df.foreign_net_value for df in daily_flows)
        total_smart_money = sum(df.smart_money_net for df in daily_flows)
        total_bandar = sum(df.bandar_net for df in daily_flows)
        total_retail = sum(df.retail_net for df in daily_flows)
        total_local_inst = sum(df.local_inst_net for df in daily_flows)

        # Calculate streaks
        acc_days = sum(1 for df in daily_flows if df.is_accumulation)
        dist_days = sum(1 for df in daily_flows if df.is_distribution)

        # Current streak (from most recent day backwards)
        current_streak = 0
        if daily_flows:
            reversed_flows = list(reversed(daily_flows))
            if reversed_flows[0].is_accumulation:
                for df in reversed_flows:
                    if df.is_accumulation:
                        current_streak += 1
                    else:
                        break
            elif reversed_flows[0].is_distribution:
                for df in reversed_flows:
                    if df.is_distribution:
                        current_streak -= 1
                    else:
                        break

        # Broker consistency tracking
        buyer_counts: Dict[str, int] = {}
        seller_counts: Dict[str, int] = {}

        for summary in summaries:
            # Count days each broker appears in top buyers
            for buyer in summary.top_buyers[:5]:
                code = buyer.broker_code
                buyer_counts[code] = buyer_counts.get(code, 0) + 1

            # Count days each broker appears in top sellers
            for seller in summary.top_sellers[:5]:
                code = seller.broker_code
                seller_counts[code] = seller_counts.get(code, 0) + 1

        # Filter to only consistent brokers (appear more than once)
        consistent_buyers = {k: v for k, v in buyer_counts.items() if v > 1}
        consistent_sellers = {k: v for k, v in seller_counts.items() if v > 1}

        # Trends
        foreign_trend = [df.foreign_net_value for df in daily_flows]
        volume_trend = [df.total_buy_value + df.total_sell_value for df in daily_flows]

        return CumulativeFlow(
            ticker=ticker,
            period_days=len(summaries),
            start_date=summaries[0].date,
            end_date=summaries[-1].date,
            total_foreign_net=total_foreign_net,
            total_smart_money_net=total_smart_money,
            total_bandar_net=total_bandar,
            total_retail_net=total_retail,
            total_local_inst_net=total_local_inst,
            daily_flows=daily_flows,
            accumulation_days=acc_days,
            distribution_days=dist_days,
            current_streak=current_streak,
            consistent_buyers=consistent_buyers,
            consistent_sellers=consistent_sellers,
            foreign_trend=foreign_trend,
            volume_trend=volume_trend,
        )

    def calculate_broker_composition(self, summaries: List[BrokerSummary]) -> BrokerComposition:
        """Calculate broker composition by profile."""
        if not summaries:
            return BrokerComposition()

        # Aggregate by profile
        profile_values: Dict[BrokerProfile, float] = {p: 0.0 for p in BrokerProfile}
        profile_nets: Dict[BrokerProfile, float] = {p: 0.0 for p in BrokerProfile}
        total_volume = 0.0

        for summary in summaries:
            # Buyers
            for buyer in summary.top_buyers:
                profile = self.profiler.get_profile(buyer.broker_code)
                profile_values[profile] += buyer.buy_value
                profile_nets[profile] += buyer.buy_value
                total_volume += buyer.buy_value

            # Sellers
            for seller in summary.top_sellers:
                profile = self.profiler.get_profile(seller.broker_code)
                profile_values[profile] += seller.sell_value
                profile_nets[profile] -= seller.sell_value
                total_volume += seller.sell_value

        # Calculate percentages
        def pct(val: float) -> float:
            return (val / total_volume * 100) if total_volume > 0 else 0.0

        return BrokerComposition(
            smart_money_percent=pct(profile_values[BrokerProfile.SMART_MONEY_FOREIGN]),
            smart_money_net=profile_nets[BrokerProfile.SMART_MONEY_FOREIGN],
            bandar_percent=pct(profile_values[BrokerProfile.BANDAR_GORENGAN]),
            bandar_net=profile_nets[BrokerProfile.BANDAR_GORENGAN],
            retail_percent=pct(profile_values[BrokerProfile.RETAIL]),
            retail_net=profile_nets[BrokerProfile.RETAIL],
            local_inst_percent=pct(profile_values[BrokerProfile.LOCAL_INSTITUTIONAL]),
            local_inst_net=profile_nets[BrokerProfile.LOCAL_INSTITUTIONAL],
            market_maker_percent=pct(profile_values[BrokerProfile.MARKET_MAKER]),
            market_maker_net=profile_nets[BrokerProfile.MARKET_MAKER],
            unknown_percent=pct(profile_values[BrokerProfile.UNKNOWN]),
            unknown_net=profile_nets[BrokerProfile.UNKNOWN],
        )

    def detect_accumulation_phase(self, cumulative_flow: CumulativeFlow) -> AccumulationPhase:
        """
        Detect accumulation/distribution phase based on flow patterns.

        Phase detection logic:
        - EARLY_ACCUMULATION: 2-3 days consistent buying
        - MID_ACCUMULATION: 4-6 days
        - LATE_ACCUMULATION: 7+ days, almost ready
        - MARKUP_READY: All signals align
        - DISTRIBUTION phases: reverse logic
        """
        streak = cumulative_flow.current_streak
        acc_days = cumulative_flow.accumulation_days
        dist_days = cumulative_flow.distribution_days
        total_days = cumulative_flow.period_days

        # Check for markup ready conditions
        if streak >= 5:
            # Strong accumulation streak
            smart_money_positive = cumulative_flow.total_smart_money_net > 0
            retail_negative = cumulative_flow.total_retail_net < 0

            if smart_money_positive and retail_negative:
                # Smart money buying, retail selling = contrarian bullish
                return AccumulationPhase.MARKUP_READY
            elif streak >= 7:
                return AccumulationPhase.LATE_ACCUMULATION
            else:
                return AccumulationPhase.MID_ACCUMULATION

        # Accumulation phases
        if streak >= 2:
            if streak >= 7:
                return AccumulationPhase.LATE_ACCUMULATION
            elif streak >= 4:
                return AccumulationPhase.MID_ACCUMULATION
            else:
                return AccumulationPhase.EARLY_ACCUMULATION

        # Distribution phases (negative streak)
        if streak <= -2:
            if streak <= -7:
                return AccumulationPhase.LATE_DISTRIBUTION
            elif streak <= -4:
                return AccumulationPhase.MID_DISTRIBUTION
            else:
                return AccumulationPhase.EARLY_DISTRIBUTION

        # Check overall ratio
        if total_days > 0:
            acc_ratio = acc_days / total_days
            dist_ratio = dist_days / total_days

            if acc_ratio >= 0.7:
                return AccumulationPhase.MID_ACCUMULATION
            elif dist_ratio >= 0.7:
                return AccumulationPhase.MID_DISTRIBUTION

        return AccumulationPhase.NEUTRAL

    def calculate_top5_consistency(self, summaries: List[BrokerSummary]) -> float:
        """
        Calculate how consistent the top 5 brokers are across days.

        Returns:
            Score 0-100, higher = more consistent
        """
        if len(summaries) < 2:
            return 0.0

        # Get top 5 buyers for each day
        daily_top5: List[set] = []
        for summary in summaries:
            top5 = {b.broker_code for b in summary.top_buyers[:5]}
            daily_top5.append(top5)

        # Calculate pairwise overlap
        total_overlap = 0
        comparisons = 0

        for i in range(len(daily_top5) - 1):
            overlap = len(daily_top5[i] & daily_top5[i + 1])
            total_overlap += overlap
            comparisons += 1

        if comparisons == 0:
            return 0.0

        # Average overlap out of 5 possible
        avg_overlap = total_overlap / comparisons
        return (avg_overlap / 5) * 100
