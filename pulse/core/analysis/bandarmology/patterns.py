"""Pattern detection for bandarmology analysis."""

from typing import List, Optional, Set

from pulse.core.analysis.bandarmology.broker_profiles import (
    BrokerProfile,
    BrokerProfiler,
)
from pulse.core.analysis.bandarmology.models import (
    BandarPattern,
    PatternAlert,
    PatternSeverity,
    CumulativeFlow,
    DailyFlow,
)
from pulse.core.models import BrokerSummary
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class PatternDetector:
    """Detect bandarmology patterns in broker flow data."""

    def __init__(self):
        self.profiler = BrokerProfiler()

    def detect_all_patterns(
        self,
        summaries: List[BrokerSummary],
        cumulative_flow: CumulativeFlow,
    ) -> List[PatternAlert]:
        """
        Detect all patterns in the broker flow data.

        Args:
            summaries: List of daily broker summaries
            cumulative_flow: Cumulative flow analysis

        Returns:
            List of detected pattern alerts
        """
        alerts: List[PatternAlert] = []

        if not summaries:
            return alerts

        # Latest day for single-day patterns
        latest = summaries[-1]

        # Single-day patterns
        crossing = self.detect_crossing(latest)
        if crossing:
            alerts.append(crossing)

        dominasi = self.detect_dominasi(latest)
        if dominasi:
            alerts.append(dominasi)

        retail_trap = self.detect_retail_trap(latest, cumulative_flow)
        if retail_trap:
            alerts.append(retail_trap)

        smart_money = self.detect_smart_money_activity(latest, cumulative_flow)
        if smart_money:
            alerts.append(smart_money)

        # Multi-day patterns
        consistency = self.detect_broker_consistency(cumulative_flow)
        if consistency:
            alerts.append(consistency)

        volume_spike = self.detect_volume_spike(cumulative_flow)
        if volume_spike:
            alerts.append(volume_spike)

        markup_signal = self.detect_markup_signal(cumulative_flow)
        if markup_signal:
            alerts.append(markup_signal)

        distribution_warning = self.detect_distribution_warning(cumulative_flow)
        if distribution_warning:
            alerts.append(distribution_warning)

        rotasi = self.detect_rotasi(summaries)
        if rotasi:
            alerts.append(rotasi)

        return alerts

    def detect_crossing(self, summary: BrokerSummary) -> Optional[PatternAlert]:
        """
        Detect crossing pattern - same broker on both buy and sell side.

        This can indicate:
        - Market making activity
        - Potential distribution disguised as trading
        """
        buyer_codes = {b.broker_code for b in summary.top_buyers[:10]}
        seller_codes = {s.broker_code for s in summary.top_sellers[:10]}

        crossing_brokers = buyer_codes & seller_codes

        if not crossing_brokers:
            return None

        # Check if any are bandar brokers
        bandar_crossing = [code for code in crossing_brokers if self.profiler.is_bandar(code)]

        if bandar_crossing:
            return PatternAlert(
                pattern=BandarPattern.CROSSING,
                severity=PatternSeverity.HIGH,
                description=f"Broker crossing terdeteksi: {', '.join(bandar_crossing)} di kedua sisi (potensi distribusi terselubung)",
                brokers_involved=list(bandar_crossing),
                is_bullish=False,
            )
        elif crossing_brokers:
            return PatternAlert(
                pattern=BandarPattern.CROSSING,
                severity=PatternSeverity.LOW,
                description=f"Market maker crossing: {', '.join(crossing_brokers)}",
                brokers_involved=list(crossing_brokers),
                is_bullish=True,  # Neutral, normal MM activity
            )

        return None

    def detect_dominasi(self, summary: BrokerSummary) -> Optional[PatternAlert]:
        """
        Detect single broker dominance > 25% of volume.
        """
        if not summary.bandar:
            return None

        top1_pct = summary.bandar.top1_percent

        if top1_pct < 25:
            return None

        # Get top buyer
        top_buyer = summary.top_buyers[0] if summary.top_buyers else None
        if not top_buyer:
            return None

        broker_code = top_buyer.broker_code
        broker_name = self.profiler.get_name(broker_code)
        profile = self.profiler.get_profile(broker_code)

        severity = PatternSeverity.HIGH if top1_pct >= 35 else PatternSeverity.MEDIUM

        # Determine if bullish based on profile
        is_bullish = profile in [
            BrokerProfile.SMART_MONEY_FOREIGN,
            BrokerProfile.LOCAL_INSTITUTIONAL,
        ]

        profile_note = ""
        if profile == BrokerProfile.BANDAR_GORENGAN:
            profile_note = " (hati-hati gorengan)"
            is_bullish = True  # Could go up but risky
        elif profile == BrokerProfile.SMART_MONEY_FOREIGN:
            profile_note = " (smart money)"

        return PatternAlert(
            pattern=BandarPattern.DOMINASI,
            severity=severity,
            description=f"{broker_code} ({broker_name}) menguasai {top1_pct:.1f}% volume{profile_note}",
            brokers_involved=[broker_code],
            value=top1_pct,
            is_bullish=is_bullish,
        )

    def detect_retail_trap(
        self,
        summary: BrokerSummary,
        cumulative_flow: CumulativeFlow,
    ) -> Optional[PatternAlert]:
        """
        Detect retail trap - retail buying while smart money selling.

        Strong contrarian bullish signal when:
        - Retail is NET SELL
        - Smart money is NET BUY

        Warning when:
        - Retail is NET BUY
        - Smart money is NET SELL
        """
        retail_net = cumulative_flow.total_retail_net
        smart_money_net = cumulative_flow.total_smart_money_net

        # Retail buying, smart money selling = TRAP (bearish for retail)
        if retail_net > 0 and smart_money_net < 0:
            return PatternAlert(
                pattern=BandarPattern.RETAIL_TRAP,
                severity=PatternSeverity.HIGH,
                description="RETAIL TRAP: Retail membeli sementara smart money menjual",
                brokers_involved=[],
                is_bullish=False,
            )

        # Retail selling, smart money buying = Contrarian bullish
        if retail_net < 0 and smart_money_net > 0:
            return PatternAlert(
                pattern=BandarPattern.RETAIL_TRAP,
                severity=PatternSeverity.MEDIUM,
                description="Contrarian bullish: Retail jual, smart money beli",
                brokers_involved=[],
                is_bullish=True,
            )

        return None

    def detect_smart_money_activity(
        self,
        summary: BrokerSummary,
        cumulative_flow: CumulativeFlow,
    ) -> Optional[PatternAlert]:
        """Detect significant smart money activity."""
        smart_money_net = cumulative_flow.total_smart_money_net

        # Find smart money brokers in top buyers
        sm_buyers = [
            b.broker_code
            for b in summary.top_buyers[:5]
            if self.profiler.is_smart_money(b.broker_code)
        ]

        sm_sellers = [
            s.broker_code
            for s in summary.top_sellers[:5]
            if self.profiler.is_smart_money(s.broker_code)
        ]

        # Smart money accumulating
        if smart_money_net > 0 and len(sm_buyers) >= 2:
            return PatternAlert(
                pattern=BandarPattern.SMART_MONEY_ENTRY,
                severity=PatternSeverity.HIGH,
                description=f"Smart money akumulasi: {', '.join(sm_buyers)} NET BUY",
                brokers_involved=sm_buyers,
                value=smart_money_net,
                is_bullish=True,
            )

        # Smart money distributing
        if smart_money_net < 0 and len(sm_sellers) >= 2:
            return PatternAlert(
                pattern=BandarPattern.SMART_MONEY_EXIT,
                severity=PatternSeverity.HIGH,
                description=f"Smart money distribusi: {', '.join(sm_sellers)} NET SELL",
                brokers_involved=sm_sellers,
                value=smart_money_net,
                is_bullish=False,
            )

        return None

    def detect_broker_consistency(
        self,
        cumulative_flow: CumulativeFlow,
    ) -> Optional[PatternAlert]:
        """Detect consistent broker activity over multiple days."""
        if not cumulative_flow.consistent_buyers:
            return None

        # Find brokers appearing 70%+ of days
        threshold = max(2, int(cumulative_flow.period_days * 0.7))

        very_consistent = [
            code for code, days in cumulative_flow.consistent_buyers.items() if days >= threshold
        ]

        if not very_consistent:
            return None

        # Check profiles
        sm_consistent = [c for c in very_consistent if self.profiler.is_smart_money(c)]
        bandar_consistent = [c for c in very_consistent if self.profiler.is_bandar(c)]

        if sm_consistent:
            return PatternAlert(
                pattern=BandarPattern.BROKER_CONSISTENCY,
                severity=PatternSeverity.HIGH,
                description=f"Smart money konsisten beli {threshold}+ hari: {', '.join(sm_consistent)}",
                brokers_involved=sm_consistent,
                is_bullish=True,
            )
        elif bandar_consistent:
            return PatternAlert(
                pattern=BandarPattern.BROKER_CONSISTENCY,
                severity=PatternSeverity.MEDIUM,
                description=f"Bandar konsisten akumulasi {threshold}+ hari: {', '.join(bandar_consistent)}",
                brokers_involved=bandar_consistent,
                is_bullish=True,
            )
        elif very_consistent:
            return PatternAlert(
                pattern=BandarPattern.BROKER_CONSISTENCY,
                severity=PatternSeverity.LOW,
                description=f"Broker konsisten beli: {', '.join(very_consistent[:3])}",
                brokers_involved=very_consistent[:3],
                is_bullish=True,
            )

        return None

    def detect_volume_spike(
        self,
        cumulative_flow: CumulativeFlow,
    ) -> Optional[PatternAlert]:
        """Detect sudden volume increase in recent days."""
        if len(cumulative_flow.volume_trend) < 3:
            return None

        volumes = cumulative_flow.volume_trend
        recent_avg = sum(volumes[-2:]) / 2
        earlier_avg = sum(volumes[:-2]) / max(1, len(volumes) - 2)

        if earlier_avg == 0:
            return None

        spike_ratio = recent_avg / earlier_avg

        if spike_ratio >= 2.0:
            return PatternAlert(
                pattern=BandarPattern.VOLUME_SPIKE,
                severity=PatternSeverity.HIGH,
                description=f"Volume spike {spike_ratio:.1f}x dari rata-rata - potensi markup soon",
                value=spike_ratio,
                is_bullish=True,
            )
        elif spike_ratio >= 1.5:
            return PatternAlert(
                pattern=BandarPattern.VOLUME_SPIKE,
                severity=PatternSeverity.MEDIUM,
                description=f"Volume meningkat {spike_ratio:.1f}x",
                value=spike_ratio,
                is_bullish=True,
            )

        return None

    def detect_markup_signal(
        self,
        cumulative_flow: CumulativeFlow,
    ) -> Optional[PatternAlert]:
        """
        Detect markup ready signal - all conditions align.

        Conditions:
        - Accumulation streak >= 5 days
        - Smart money net positive
        - Retail net negative (contrarian)
        - Volume increasing
        """
        conditions_met = 0
        conditions_desc = []

        # Condition 1: Accumulation streak
        if cumulative_flow.current_streak >= 5:
            conditions_met += 1
            conditions_desc.append(f"{cumulative_flow.current_streak} hari akumulasi")

        # Condition 2: Smart money positive
        if cumulative_flow.total_smart_money_net > 0:
            conditions_met += 1
            conditions_desc.append("smart money NET BUY")

        # Condition 3: Retail negative (contrarian bullish)
        if cumulative_flow.total_retail_net < 0:
            conditions_met += 1
            conditions_desc.append("retail NET SELL")

        # Condition 4: Volume trend up
        if len(cumulative_flow.volume_trend) >= 3:
            recent = cumulative_flow.volume_trend[-1]
            earlier = sum(cumulative_flow.volume_trend[:-1]) / max(
                1, len(cumulative_flow.volume_trend) - 1
            )
            if recent > earlier * 1.2:
                conditions_met += 1
                conditions_desc.append("volume meningkat")

        if conditions_met >= 3:
            severity = PatternSeverity.HIGH if conditions_met >= 4 else PatternSeverity.MEDIUM
            return PatternAlert(
                pattern=BandarPattern.MARKUP_SIGNAL,
                severity=severity,
                description=f"MARKUP SIGNAL ({conditions_met}/4): {', '.join(conditions_desc)}",
                value=conditions_met,
                is_bullish=True,
            )

        return None

    def detect_distribution_warning(
        self,
        cumulative_flow: CumulativeFlow,
    ) -> Optional[PatternAlert]:
        """Detect early signs of distribution."""
        # Check if smart money starting to sell after accumulation
        if cumulative_flow.current_streak >= 0:
            return None  # Still accumulating

        # Distribution streak starting
        if cumulative_flow.current_streak <= -2:
            sm_net = cumulative_flow.total_smart_money_net

            if sm_net < 0:
                return PatternAlert(
                    pattern=BandarPattern.DISTRIBUTION_SETUP,
                    severity=PatternSeverity.HIGH,
                    description=f"DISTRIBUTION WARNING: {abs(cumulative_flow.current_streak)} hari distribusi, smart money keluar",
                    is_bullish=False,
                )

        return None

    def detect_rotasi(
        self,
        summaries: List[BrokerSummary],
    ) -> Optional[PatternAlert]:
        """
        Detect rotation - foreign out, local in (or vice versa).
        """
        if len(summaries) < 3:
            return None

        # Compare first half vs second half
        mid = len(summaries) // 2
        first_half = summaries[:mid]
        second_half = summaries[mid:]

        # Calculate foreign net for each half
        first_foreign = sum(s.foreign_net_buy for s in first_half)
        second_foreign = sum(s.foreign_net_buy for s in second_half)

        # Significant rotation
        if first_foreign > 0 and second_foreign < 0:
            return PatternAlert(
                pattern=BandarPattern.ROTASI,
                severity=PatternSeverity.MEDIUM,
                description="Rotasi: Foreign keluar setelah akumulasi awal",
                is_bullish=False,
            )
        elif first_foreign < 0 and second_foreign > 0:
            return PatternAlert(
                pattern=BandarPattern.ROTASI,
                severity=PatternSeverity.MEDIUM,
                description="Rotasi: Foreign masuk setelah distribusi awal",
                is_bullish=True,
            )

        return None

    def get_pattern_summary(
        self,
        alerts: List[PatternAlert],
    ) -> dict:
        """Get summary of detected patterns."""
        bullish_count = sum(1 for a in alerts if a.is_bullish)
        bearish_count = len(alerts) - bullish_count

        high_severity = [a for a in alerts if a.severity == PatternSeverity.HIGH]

        return {
            "total_patterns": len(alerts),
            "bullish_patterns": bullish_count,
            "bearish_patterns": bearish_count,
            "high_severity_count": len(high_severity),
            "patterns": [a.pattern.value for a in alerts],
            "net_sentiment": bullish_count - bearish_count,
        }
