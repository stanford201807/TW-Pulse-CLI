"""Bandarmology Engine - Main orchestrator for comprehensive broker flow analysis."""

from datetime import datetime
from typing import List, Optional

from pulse.core.analysis.bandarmology.broker_profiles import (
    BrokerProfile,
    BrokerProfiler,
)
from pulse.core.analysis.bandarmology.flow_tracker import FlowTracker
from pulse.core.analysis.bandarmology.models import (
    AccumulationPhase,
    BandarPattern,
    BandarmologyResult,
    PatternAlert,
    PatternSeverity,
)
from pulse.core.analysis.bandarmology.patterns import PatternDetector
from pulse.core.models import SignalType, BrokerSummary
from pulse.utils.formatters import format_currency
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class BandarmologyEngine:
    """
    Main engine for comprehensive bandarmology analysis.

    Provides:
    - Multi-day flow tracking
    - Accumulation/distribution phase detection
    - Pattern recognition
    - Broker profiling and composition
    - Markup readiness scoring
    """

    def __init__(self):
        self.flow_tracker = FlowTracker()
        self.pattern_detector = PatternDetector()
        self.profiler = BrokerProfiler()

    async def analyze(
        self,
        ticker: str,
        days: int = 10,
        end_date: Optional[str] = None,
    ) -> Optional[BandarmologyResult]:
        """
        Perform comprehensive bandarmology analysis.

        Args:
            ticker: Stock ticker (e.g., "BBCA")
            days: Number of trading days to analyze (default 10)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            BandarmologyResult with complete analysis
        """
        ticker = ticker.upper().strip()
        log.info(f"Starting bandarmology analysis for {ticker} ({days} days)")

        # Fetch historical data
        summaries = await self.flow_tracker.fetch_historical(ticker, days, end_date)

        if not summaries:
            log.warning(f"No broker data found for {ticker}")
            return None

        # Calculate cumulative flow
        cumulative_flow = self.flow_tracker.calculate_cumulative_flow(summaries)

        # Calculate broker composition
        broker_composition = self.flow_tracker.calculate_broker_composition(summaries)

        # Detect accumulation phase
        phase = self.flow_tracker.detect_accumulation_phase(cumulative_flow)

        # Detect patterns
        pattern_alerts = self.pattern_detector.detect_all_patterns(summaries, cumulative_flow)
        patterns = list(set(a.pattern for a in pattern_alerts))

        # Calculate scores
        flow_momentum_score = self._calculate_flow_momentum_score(
            cumulative_flow, broker_composition, pattern_alerts
        )
        markup_readiness_score = self._calculate_markup_readiness_score(
            cumulative_flow, phase, pattern_alerts
        )
        confidence = self._calculate_confidence(summaries, cumulative_flow)

        # Determine signal
        signal = self._determine_signal(flow_momentum_score, markup_readiness_score, phase)

        # Calculate top 5 consistency
        top5_consistency = self.flow_tracker.calculate_top5_consistency(summaries)

        # Check distribution warning
        distribution_warning = any(
            a.pattern == BandarPattern.DISTRIBUTION_SETUP for a in pattern_alerts
        )

        # Generate insights and risks
        insights = self._generate_insights(
            cumulative_flow, broker_composition, phase, pattern_alerts
        )
        risks = self._generate_risks(cumulative_flow, broker_composition, pattern_alerts)
        recommendation = self._generate_recommendation(
            signal, phase, flow_momentum_score, markup_readiness_score
        )

        # Get most consistent brokers
        most_consistent_buyer = cumulative_flow.most_consistent_buyer
        most_consistent_buyer_days = (
            cumulative_flow.consistent_buyers.get(most_consistent_buyer, 0)
            if most_consistent_buyer
            else 0
        )
        most_consistent_seller = cumulative_flow.most_consistent_seller
        most_consistent_seller_days = (
            cumulative_flow.consistent_sellers.get(most_consistent_seller, 0)
            if most_consistent_seller
            else 0
        )

        return BandarmologyResult(
            ticker=ticker,
            analyzed_at=datetime.now(),
            period_days=len(summaries),
            start_date=summaries[0].date if summaries else None,
            end_date=summaries[-1].date if summaries else None,
            flow_momentum_score=flow_momentum_score,
            markup_readiness_score=markup_readiness_score,
            confidence=confidence,
            accumulation_phase=phase,
            signal=signal,
            cumulative_flow=cumulative_flow,
            broker_composition=broker_composition,
            patterns=patterns,
            pattern_alerts=pattern_alerts,
            foreign_net_total=cumulative_flow.total_foreign_net,
            smart_money_net_total=cumulative_flow.total_smart_money_net,
            retail_net_total=cumulative_flow.total_retail_net,
            accumulation_streak=cumulative_flow.current_streak,
            distribution_warning=distribution_warning,
            top5_consistency_score=top5_consistency,
            most_consistent_buyer=most_consistent_buyer,
            most_consistent_buyer_days=most_consistent_buyer_days,
            most_consistent_seller=most_consistent_seller,
            most_consistent_seller_days=most_consistent_seller_days,
            insights=insights,
            risks=risks,
            recommendation=recommendation,
            raw_summaries=summaries,
        )

    def _calculate_flow_momentum_score(
        self,
        cumulative_flow,
        broker_composition,
        pattern_alerts: List[PatternAlert],
    ) -> int:
        """Calculate flow momentum score (0-100)."""
        score = 50  # Start neutral

        # Foreign flow impact (±20)
        foreign_net = cumulative_flow.total_foreign_net
        if foreign_net > 50_000_000_000:  # > 50B
            score += 20
        elif foreign_net > 20_000_000_000:  # > 20B
            score += 15
        elif foreign_net > 5_000_000_000:  # > 5B
            score += 10
        elif foreign_net > 0:
            score += 5
        elif foreign_net < -50_000_000_000:
            score -= 20
        elif foreign_net < -20_000_000_000:
            score -= 15
        elif foreign_net < -5_000_000_000:
            score -= 10
        elif foreign_net < 0:
            score -= 5

        # Smart money impact (±15)
        sm_net = cumulative_flow.total_smart_money_net
        if sm_net > 20_000_000_000:
            score += 15
        elif sm_net > 5_000_000_000:
            score += 10
        elif sm_net > 0:
            score += 5
        elif sm_net < -20_000_000_000:
            score -= 15
        elif sm_net < -5_000_000_000:
            score -= 10
        elif sm_net < 0:
            score -= 5

        # Retail contrarian (±10)
        retail_net = cumulative_flow.total_retail_net
        if retail_net < 0 and sm_net > 0:
            score += 10  # Retail selling, smart buying = bullish
        elif retail_net > 0 and sm_net < 0:
            score -= 10  # Retail buying, smart selling = bearish

        # Accumulation streak (±10)
        streak = cumulative_flow.current_streak
        if streak >= 5:
            score += 10
        elif streak >= 3:
            score += 5
        elif streak <= -5:
            score -= 10
        elif streak <= -3:
            score -= 5

        # Pattern impact (±5)
        for alert in pattern_alerts:
            if alert.severity == PatternSeverity.HIGH:
                score += 5 if alert.is_bullish else -5

        return max(0, min(100, score))

    def _calculate_markup_readiness_score(
        self,
        cumulative_flow,
        phase: AccumulationPhase,
        pattern_alerts: List[PatternAlert],
    ) -> int:
        """Calculate markup readiness score (0-100)."""
        score = 0

        # Phase impact (0-40)
        phase_scores = {
            AccumulationPhase.MARKUP_READY: 40,
            AccumulationPhase.LATE_ACCUMULATION: 30,
            AccumulationPhase.MID_ACCUMULATION: 20,
            AccumulationPhase.EARLY_ACCUMULATION: 10,
            AccumulationPhase.NEUTRAL: 5,
            AccumulationPhase.EARLY_DISTRIBUTION: -10,
            AccumulationPhase.MID_DISTRIBUTION: -20,
            AccumulationPhase.LATE_DISTRIBUTION: -30,
        }
        score += phase_scores.get(phase, 0)

        # Accumulation streak (0-25)
        streak = cumulative_flow.current_streak
        if streak >= 7:
            score += 25
        elif streak >= 5:
            score += 20
        elif streak >= 3:
            score += 10
        elif streak >= 1:
            score += 5

        # Smart money + retail contrarian (0-20)
        if cumulative_flow.total_smart_money_net > 0:
            score += 10
            if cumulative_flow.total_retail_net < 0:
                score += 10  # Contrarian bonus

        # Markup signal pattern (0-15)
        has_markup_signal = any(a.pattern == BandarPattern.MARKUP_SIGNAL for a in pattern_alerts)
        if has_markup_signal:
            score += 15

        return max(0, min(100, score))

    def _calculate_confidence(
        self,
        summaries: List[BrokerSummary],
        cumulative_flow,
    ) -> int:
        """Calculate confidence level (0-100)."""
        confidence = 50

        # More days = more confidence
        if len(summaries) >= 10:
            confidence += 20
        elif len(summaries) >= 7:
            confidence += 15
        elif len(summaries) >= 5:
            confidence += 10

        # Consistent patterns = more confidence
        acc_ratio = cumulative_flow.accumulation_days / max(1, len(summaries))
        dist_ratio = cumulative_flow.distribution_days / max(1, len(summaries))

        if acc_ratio >= 0.7 or dist_ratio >= 0.7:
            confidence += 15
        elif acc_ratio >= 0.5 or dist_ratio >= 0.5:
            confidence += 10

        # Broker consistency = more confidence
        if cumulative_flow.consistent_buyers:
            max_consistency = max(cumulative_flow.consistent_buyers.values())
            if max_consistency >= len(summaries) * 0.8:
                confidence += 15
            elif max_consistency >= len(summaries) * 0.5:
                confidence += 10

        return max(0, min(100, confidence))

    def _determine_signal(
        self,
        flow_score: int,
        markup_score: int,
        phase: AccumulationPhase,
    ) -> SignalType:
        """Determine trading signal."""
        combined_score = (flow_score * 0.6) + (markup_score * 0.4)

        if combined_score >= 80:
            return SignalType.STRONG_BUY
        elif combined_score >= 65:
            return SignalType.BUY
        elif combined_score >= 40:
            return SignalType.NEUTRAL
        elif combined_score >= 25:
            return SignalType.SELL
        else:
            return SignalType.STRONG_SELL

    def _generate_insights(
        self,
        cumulative_flow,
        broker_composition,
        phase: AccumulationPhase,
        pattern_alerts: List[PatternAlert],
    ) -> List[str]:
        """Generate human-readable insights."""
        insights = []

        # Foreign flow insight
        fn = cumulative_flow.total_foreign_net
        if fn > 0:
            insights.append(f"Foreign NET BUY {format_currency(fn)}")
        else:
            insights.append(f"Foreign NET SELL {format_currency(abs(fn))}")

        # Smart money insight
        sm = cumulative_flow.total_smart_money_net
        if sm > 0:
            insights.append(f"Smart money akumulasi {format_currency(sm)}")
        elif sm < 0:
            insights.append(f"Smart money distribusi {format_currency(abs(sm))}")

        # Phase insight
        insights.append(f"Fase: {phase.value}")

        # Streak insight
        streak = cumulative_flow.current_streak
        if streak > 0:
            insights.append(f"Akumulasi streak: {streak} hari")
        elif streak < 0:
            insights.append(f"Distribusi streak: {abs(streak)} hari")

        # Most consistent buyer
        if cumulative_flow.most_consistent_buyer:
            buyer = cumulative_flow.most_consistent_buyer
            days = cumulative_flow.consistent_buyers.get(buyer, 0)
            name = self.profiler.get_name(buyer)
            insights.append(f"Broker paling konsisten beli: {buyer} ({name}) - {days} hari")

        return insights

    def _generate_risks(
        self,
        cumulative_flow,
        broker_composition,
        pattern_alerts: List[PatternAlert],
    ) -> List[str]:
        """Generate risk warnings."""
        risks = []

        # Distribution warning
        has_dist = any(a.pattern == BandarPattern.DISTRIBUTION_SETUP for a in pattern_alerts)
        if has_dist:
            risks.append("WARNING: Tanda-tanda distribusi terdeteksi")

        # Retail trap warning
        has_trap = any(
            a.pattern == BandarPattern.RETAIL_TRAP and not a.is_bullish for a in pattern_alerts
        )
        if has_trap:
            risks.append("WARNING: Retail trap - retail beli saat smart money jual")

        # High bandar concentration
        if broker_composition and broker_composition.bandar_percent > 30:
            risks.append(
                f"Dominasi bandar {broker_composition.bandar_percent:.1f}% - hati-hati gorengan"
            )

        # Negative smart money
        if cumulative_flow.total_smart_money_net < 0:
            risks.append("Smart money sedang keluar")

        return risks

    def _generate_recommendation(
        self,
        signal: SignalType,
        phase: AccumulationPhase,
        flow_score: int,
        markup_score: int,
    ) -> str:
        """Generate recommendation text."""
        if signal == SignalType.STRONG_BUY:
            if phase == AccumulationPhase.MARKUP_READY:
                return "STRONG BUY - Siap markup! Entry segera."
            else:
                return "STRONG BUY - Akumulasi kuat, tunggu konfirmasi breakout."
        elif signal == SignalType.BUY:
            return "BUY - Akumulasi positif, entry bertahap."
        elif signal == SignalType.NEUTRAL:
            return "HOLD - Belum ada sinyal kuat, monitor terus."
        elif signal == SignalType.SELL:
            return "REDUCE - Tanda distribusi awal, kurangi posisi."
        else:
            return "SELL - Distribusi aktif, hindari atau exit."

    async def scan_markup_ready(
        self,
        tickers: List[str],
        min_score: int = 70,
        days: int = 10,
    ) -> List[BandarmologyResult]:
        """
        Scan multiple stocks for markup-ready candidates.

        Args:
            tickers: List of stock tickers to scan
            min_score: Minimum markup readiness score
            days: Days to analyze per stock

        Returns:
            List of BandarmologyResult for stocks meeting criteria
        """
        results = []

        for ticker in tickers:
            try:
                result = await self.analyze(ticker, days)

                if result and result.markup_readiness_score >= min_score:
                    results.append(result)
                    log.info(
                        f"{ticker}: Markup Score {result.markup_readiness_score}, "
                        f"Phase: {result.accumulation_phase.value}"
                    )

            except Exception as e:
                log.warning(f"Error analyzing {ticker}: {e}")
                continue

        # Sort by markup readiness score descending
        results.sort(key=lambda x: x.markup_readiness_score, reverse=True)

        return results

    def format_report(
        self,
        result: BandarmologyResult,
        detailed: bool = False,
    ) -> str:
        """Format comprehensive bandarmology report."""
        lines = []

        # Header
        lines.append("=" * 65)
        lines.append(f"BANDARMOLOGY REPORT: {result.ticker}")
        if result.start_date and result.end_date:
            start = result.start_date.strftime("%Y-%m-%d")
            end = result.end_date.strftime("%Y-%m-%d")
            lines.append(f"Period: {result.period_days} days ({start} to {end})")
        lines.append("=" * 65)
        lines.append("")

        # Scores
        signal_emoji = result.get_signal_emoji()
        phase_emoji = result.get_phase_emoji()

        lines.append(
            f"FLOW MOMENTUM: {result.flow_momentum_score}/100 [{result.signal.value}] {signal_emoji}"
        )
        lines.append(f"MARKUP READINESS: {result.markup_readiness_score}/100")
        lines.append(f"PHASE: {result.accumulation_phase.value} {phase_emoji}")
        lines.append(f"CONFIDENCE: {result.confidence}%")
        lines.append("")

        # Flow Summary
        lines.append("-" * 65)
        lines.append("FLOW SUMMARY")
        lines.append("-" * 65)

        fn = result.foreign_net_total
        fn_sign = "+" if fn >= 0 else ""
        lines.append(f"  Foreign Net     : {fn_sign}{format_currency(fn)}")

        sm = result.smart_money_net_total
        sm_sign = "+" if sm >= 0 else ""
        lines.append(f"  Smart Money Net : {sm_sign}{format_currency(sm)}")

        rt = result.retail_net_total
        rt_sign = "+" if rt >= 0 else ""
        lines.append(f"  Retail Net      : {rt_sign}{format_currency(rt)}")

        if result.accumulation_streak != 0:
            streak_type = "Akumulasi" if result.accumulation_streak > 0 else "Distribusi"
            lines.append(f"  {streak_type} Streak: {abs(result.accumulation_streak)} hari")
        lines.append("")

        # Broker Composition
        if result.broker_composition:
            bc = result.broker_composition
            lines.append("-" * 65)
            lines.append("BROKER COMPOSITION")
            lines.append("-" * 65)

            def format_bar(pct: float, width: int = 20) -> str:
                filled = int(pct / 100 * width)
                return "█" * filled + "░" * (width - filled)

            lines.append(
                f"  Smart Money : {bc.smart_money_percent:5.1f}% {format_bar(bc.smart_money_percent)}"
            )
            lines.append(
                f"  Bandar      : {bc.bandar_percent:5.1f}% {format_bar(bc.bandar_percent)}"
            )
            lines.append(
                f"  Retail      : {bc.retail_percent:5.1f}% {format_bar(bc.retail_percent)}"
            )
            lines.append(
                f"  Local Inst  : {bc.local_inst_percent:5.1f}% {format_bar(bc.local_inst_percent)}"
            )
            lines.append("")

        # Top Broker Consistency
        if result.most_consistent_buyer:
            lines.append("-" * 65)
            lines.append("TOP BROKER CONSISTENCY")
            lines.append("-" * 65)

            buyer_name = self.profiler.get_name(result.most_consistent_buyer)
            buyer_profile = self.profiler.get_profile(result.most_consistent_buyer).value
            lines.append(
                f"  Top Buyer : {result.most_consistent_buyer} ({buyer_name}) - "
                f"{result.most_consistent_buyer_days}/{result.period_days} hari [{buyer_profile}]"
            )

            if result.most_consistent_seller:
                seller_name = self.profiler.get_name(result.most_consistent_seller)
                lines.append(
                    f"  Top Seller: {result.most_consistent_seller} ({seller_name}) - "
                    f"{result.most_consistent_seller_days}/{result.period_days} hari"
                )

            lines.append(f"  Top 5 Consistency: {result.top5_consistency_score:.1f}%")
            lines.append("")

        # Pattern Alerts
        if result.pattern_alerts:
            lines.append("-" * 65)
            lines.append("PATTERN ALERTS")
            lines.append("-" * 65)

            for alert in result.pattern_alerts:
                icon = "+" if alert.is_bullish else "!"
                sev = "HIGH" if alert.severity == PatternSeverity.HIGH else ""
                lines.append(f"  [{icon}] {sev} {alert.description}")
            lines.append("")

        # Daily Timeline (if detailed)
        if detailed and result.cumulative_flow and result.cumulative_flow.daily_flows:
            lines.append("-" * 65)
            lines.append("DAILY TIMELINE")
            lines.append("-" * 65)

            for df in result.cumulative_flow.daily_flows:
                date_str = df.date.strftime("%b %d")
                acc_icon = "▓" if df.is_accumulation else "░" if df.is_distribution else "▒"
                fn_short = f"{df.foreign_net_value / 1e9:+.1f}B"
                top_buyer = df.top_buyer_code or "-"
                lines.append(
                    f"  {date_str} {acc_icon} {df.accdist:12} Foreign: {fn_short:>8}  Top: {top_buyer}"
                )
            lines.append("")

        # Insights
        if result.insights:
            lines.append("-" * 65)
            lines.append("INSIGHTS")
            lines.append("-" * 65)
            for insight in result.insights:
                lines.append(f"  - {insight}")
            lines.append("")

        # Risks
        if result.risks:
            lines.append("-" * 65)
            lines.append("RISKS")
            lines.append("-" * 65)
            for risk in result.risks:
                lines.append(f"  ! {risk}")
            lines.append("")

        # Recommendation
        lines.append("-" * 65)
        lines.append("RECOMMENDATION")
        lines.append("-" * 65)
        lines.append(f"  {result.recommendation}")
        lines.append("")

        return "\n".join(lines)

    def format_scan_results(
        self,
        results: List[BandarmologyResult],
        title: str = "Bandarmology Scan Results",
    ) -> str:
        """Format scan results as table."""
        if not results:
            return "No stocks found matching criteria."

        lines = []
        lines.append(f"{'=' * 65}")
        lines.append(title)
        lines.append(f"{'=' * 65}")
        lines.append("")
        lines.append(f"{'Ticker':<8} {'Markup':>8} {'Flow':>8} {'Phase':<20} {'Signal':<12}")
        lines.append("-" * 65)

        for r in results:
            phase_short = r.accumulation_phase.value[:18]
            lines.append(
                f"{r.ticker:<8} {r.markup_readiness_score:>7}% {r.flow_momentum_score:>7}% "
                f"{phase_short:<20} {r.signal.value:<12}"
            )

        lines.append("")
        lines.append(f"Total: {len(results)} stocks")

        return "\n".join(lines)
