"""回測引擎核心模組。"""

from datetime import datetime, timedelta

from pulse.core.analysis.technical import TechnicalAnalyzer
from pulse.core.backtest.position import PositionManager
from pulse.core.backtest.report import BacktestReport, calculate_metrics
from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.strategies.base import BaseStrategy, SignalAction
from pulse.reports import TradeReportGenerator
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class BacktestEngine:
    """回測引擎。

    使用歷史數據模擬策略執行，計算績效指標。
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        ticker: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        initial_cash: float = 1_000_000,
    ):
        """初始化回測引擎。

        Args:
            strategy: 交易策略實例
            ticker: 股票代碼
            start_date: 開始日期（None = 5年前）
            end_date: 結束日期（None = 今天）
            initial_cash: 初始資金（預設 100 萬）
        """
        self.strategy = strategy
        self.ticker = ticker
        self.initial_cash = initial_cash

        # 設定日期範圍（預設 5 年）
        self.end_date = end_date or datetime.now()
        self.start_date = start_date or (self.end_date - timedelta(days=365 * 5))

        self.fetcher = YFinanceFetcher()
        self.analyzer = TechnicalAnalyzer()

    async def run(self) -> BacktestReport:
        """執行回測。

        Returns:
            回測報告
        """
        log.info(
            f"Starting backtest for {self.ticker} "
            f"from {self.start_date.date()} to {self.end_date.date()}"
        )

        # 1. 載入歷史數據
        log.info("Loading historical data...")
        df = await self.fetcher.fetch_history(
            self.ticker, start=self.start_date, end=self.end_date
        )

        if df is None or df.empty:
            raise ValueError(f"無法載入 {self.ticker} 的歷史數據")

        log.info(f"Loaded {len(df)} bars")

        # 2. 計算技術指標
        log.info("Calculating technical indicators...")
        indicators_df = await self.analyzer.calculate_indicators(df)

        if indicators_df is None or indicators_df.empty:
            raise ValueError("技術指標計算失敗")

        # 3. 初始化策略
        await self.strategy.initialize(
            self.ticker, self.initial_cash, self.strategy.config
        )

        # 4. 初始化持倉管理器
        position_manager = PositionManager(self.initial_cash)

        # 5. 逐日回測
        log.info("Running backtest simulation...")
        signals_generated = 0

        for i in range(len(indicators_df)):
            row = indicators_df.iloc[i]
            date = row.name

            # 準備 K 線數據
            bar = {
                "date": date,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row.get("volume", 0),
            }

            # 準備技術指標
            indicators = {
                "rsi_14": row.get("RSI_14"),
                "ma_200": row.get("MA_200"),
                "ma_50": row.get("MA_50"),
                "ma_20": row.get("MA_20"),
            }
            
            # 同步資金管理器狀態（在生成訊號前）
            if self.strategy.capital_manager:
                current_equity = position_manager.get_total_equity(row["close"])
                realized_pnl = current_equity - self.initial_cash
                self.strategy.capital_manager.state.current_capital = self.initial_cash + realized_pnl
                log.debug(f"Synced capital: equity={current_equity:,.0f}, realized_pnl={realized_pnl:+,.0f}")

            # 生成交易訊號
            signal = await self.strategy.on_bar(bar, indicators)

            # 執行交易
            if signal and signal.action != SignalAction.HOLD:
                action_str = signal.action.value
                success = position_manager.execute_trade(
                    date=date,
                    action=action_str,
                    quantity=signal.quantity,
                    price=signal.price,
                    reason=signal.reason,
                )

                if success:
                    signals_generated += 1
                    log.debug(f"{date.date()} | {action_str} {signal.quantity}股 @ {signal.price:,.0f}")

                    # 更新策略狀態（quantity 直接是股數變化）
                    quantity_change = signal.quantity if signal.action == SignalAction.BUY else -signal.quantity
                    self.strategy.state.update_position(
                        quantity_change,
                        signal.price,
                        1,  # shares_per_position 不再使用，傳入 1
                    )
                    
                    # 更新動態資金管理器（賣出時記錄已實現損益）
                    if self.strategy.capital_manager and signal.action == SignalAction.SELL:
                        # 計算已實現損益（賣出金額 - 成本）
                        sell_amount = signal.quantity * signal.price
                        cost = signal.quantity * position_manager.avg_cost if position_manager.avg_cost > 0 else 0
                        realized_pnl = sell_amount - cost
                        
                        # 更新總資金
                        self.strategy.capital_manager.update_capital(realized_pnl)
                        log.debug(f"Updated capital: realized_pnl={realized_pnl:+,.0f}, new_capital={self.strategy.capital_manager.get_current_capital():,.0f}")

            # 更新權益曲線
            position_manager.update_equity(date, row["close"])


        log.info(f"Backtest completed. Signals generated: {signals_generated}")

        # 6. 計算績效指標
        log.info("Calculating performance metrics...")
        
        # 檢查是否有動態資金管理
        capital_state = None
        if hasattr(self.strategy, 'capital_manager') and self.strategy.capital_manager:
            capital_state = self.strategy.capital_manager.get_state()
            log.info("Dynamic capital management detected, will include detailed trade table")
        
        report = calculate_metrics(
            ticker=self.ticker,
            strategy_name=self.strategy.name,
            position_manager=position_manager,
            start_date=self.start_date,
            end_date=self.end_date,
            capital_state=capital_state,
        )
        
        # 暫存 position_manager 供外部使用（例如 CLI 生成詳細報表）
        self._last_position_manager = position_manager

        return report
