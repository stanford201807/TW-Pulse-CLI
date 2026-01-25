"""進階農夫播種術交易策略。

基於基準價的加減碼策略，適合趨勢股票的長期持有。

策略規則：
1. 基準價：上次成交價（買進或賣出）
2. 加碼：收盤價 ≥ 基準價 × 1.03，隔日開盤買進 1 份
3. 減碼：收盤價 ≤ 基準價 × 0.97，隔日開盤賣出 1 份
4. 資金控管：最多持有 10 份
5. 移動停利：從波段最高點回落 20%，全數獲利了結
6. 防禦機制：跌破 MA200 × 0.96，全數清倉
7. 抄底機制：RSI < 30 後回升至 30 以上，買進第 1 份
"""

from typing import Any

from pulse.core.capital import DynamicCapitalManager
from pulse.core.strategies.base import BaseStrategy, SignalAction, StrategySignal, StrategyState
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class FarmerPlantingStrategy(BaseStrategy):
    """進階農夫播種術策略實作。"""

    def __init__(self):
        super().__init__(
            name="進階農夫播種術",
            description="基準價加減碼策略，適合趨勢股票的長期持有",
        )
        self.ticker = ""
        self.rsi_was_oversold = False  # 追蹤 RSI 是否曾低於 30
        self.prev_close = 0.0  # 前一日收盤價（用於判斷站上年線）
        self.capital_manager: DynamicCapitalManager | None = None  # 動態資金管理器
        self.position_count = 0  # 追蹤已買進次數（份數）

    async def initialize(
        self, ticker: str, initial_cash: float, config: dict[str, Any]
    ) -> None:
        """初始化策略。

        Args:
            ticker: 股票代碼
            initial_cash: 初始資金
            config: 配置參數
        """
        self.ticker = ticker
        self.config = {
            "max_shares": config.get("max_shares", 10_000),  # 最大持股 10000 股
            "shares_per_trade": config.get("shares_per_trade", 1_000),  # 每次交易 1000 股
            "add_threshold": config.get("add_threshold", 1.03),
            "reduce_threshold": config.get("reduce_threshold", 0.97),
            "trailing_stop": config.get("trailing_stop", 0.20),
            "ma200_stop": config.get("ma200_stop", 0.96),
            "rsi_oversold": config.get("rsi_oversold", 30),
            "use_dynamic_capital": config.get("use_dynamic_capital", True),  # 啟用動態資金管理
            "num_positions": config.get("num_positions", 10),  # 總份數
        }

        self.state = StrategyState(cash=initial_cash, total_capital=initial_cash)
        self.rsi_was_oversold = False
        self.position_count = 0  # 重置份數計數
        
        # 初始化動態資金管理器
        if self.config["use_dynamic_capital"]:
            self.capital_manager = DynamicCapitalManager(
                initial_capital=initial_cash,
                num_positions=self.config["num_positions"]
            )
            log.info("Dynamic capital management enabled")
        else:
            self.capital_manager = None
            log.info("Using static position sizing")

        log.info(f"Initialized FarmerPlantingStrategy for {ticker}")
        log.info(f"Config: {self.config}")

    def _calculate_buy_quantity(self, price: float) -> int:
        """計算買進股數（依據動態或固定份額）。

        Args:
            price: 當前價格

        Returns:
            買進股數
        """
        if self.capital_manager:
            # 使用動態份額計算
            current_capital = self.capital_manager.get_current_capital()
            position_size = self.capital_manager.get_position_size()
            
            # 特殊處理：如果即將買進最後一份（滿倉），使用所有剩餘現金
            if self.position_count == self.config["num_positions"] - 1:
                # 從 state.cash 計算能買多少股（買滿）
                available_cash = self.state.cash
                shares = int(available_cash / price)
                log.info(f"Final position (10/10): using ALL cash={available_cash:,.0f}, price={price:,.2f}, shares={shares}")
                return shares
            
            # 一般情況：使用動態份額
            shares = self.capital_manager.calculate_shares(price)
            log.info(f"Dynamic capital: total={current_capital:,.0f}, per_position={position_size:,.0f}, price={price:,.2f}, shares={shares}")
            return shares
        else:
            # 使用固定股數
            return self.config["shares_per_trade"]

    async def on_bar(
        self, bar: dict[str, Any], indicators: dict[str, Any]
    ) -> StrategySignal | None:
        """處理每根K線。

        Args:
            bar: K線數據 {date, open, high, low, close, volume}
            indicators: 技術指標 {rsi_14, ma_200, ...}

        Returns:
            交易訊號或 None
        """
        if not self.state:
            log.warning("Strategy not initialized")
            return None

        close_price = bar["close"]
        open_price = bar["open"]
        date = bar["date"]
        rsi = indicators.get("rsi_14")
        ma200 = indicators.get("ma_200")

        # 更新波段最高點
        if close_price > self.state.peak_price:
            self.state.peak_price = close_price

        # 儲存當前的 prev_close 供站上年線判斷使用，然後更新為今日收盤
        prev_close_for_ma_check = self.prev_close
        self.prev_close = close_price  # 立即更新，確保下次調用有正確的前一日收盤

        # === 檢查賣出條件 ===

        # 1. 移動停利：從波段最高點回落 20%
        if self.state.positions > 0 and self.state.peak_price > 0:
            stop_price = self.state.peak_price * (1 - self.config["trailing_stop"])
            if close_price <= stop_price:
                self.position_count = 0  # 全數清倉，重置份數
                return StrategySignal(
                    timestamp=date,
                    action=SignalAction.SELL,
                    quantity=self.state.positions,  # 全數出場（股數）
                    price=open_price,  # 隔日開盤價
                    reason=f"移動停利觸發（從 {self.state.peak_price:,.0f} 回落 20%）",
                )

        # 2. 防禦機制：跌破 MA200 × 0.96
        if self.state.positions > 0 and ma200:
            defense_level = ma200 * self.config["ma200_stop"]
            if close_price <= defense_level:
                self.position_count = 0  # 全數清倉，重置份數
                return StrategySignal(
                    timestamp=date,
                    action=SignalAction.SELL,
                    quantity=self.state.positions,  # 全數出場（股數）
                    price=open_price,
                    reason=f"防禦機制觸發（跌破 MA200 {ma200:,.0f} × 0.96）",
                )

        # 3. 減碼規則：收盤價 ≤ 基準價 × 0.97
        if self.state.positions > 0 and self.state.base_price > 0:
            reduce_level = self.state.base_price * self.config["reduce_threshold"]
            if close_price <= reduce_level:
                # 使用動態計算賣出 1 份（與買進 1 份保持一致）
                sell_shares = self._calculate_buy_quantity(open_price)
                self.position_count -= 1  # 減碼減少 1 份
                return StrategySignal(
                    timestamp=date,
                    action=SignalAction.SELL,
                    quantity=sell_shares,  # 減碼 1 份
                    price=open_price,
                    reason=f"減碼（收盤 {close_price:,.0f} ≤ 基準價 {self.state.base_price:,.0f} × 0.97）",
                )

        # === 檢查買入條件 ===

        # 0. 站上年線啟動：價格從年線下方站上年線（主要進場訊號）
        if self.state.positions == 0 and ma200 and prev_close_for_ma_check > 0:
            # 前一日收盤 <= MA200 且今日收盤 > MA200
            if prev_close_for_ma_check <= ma200 and close_price > ma200:
                buy_shares = self._calculate_buy_quantity(open_price)
                self.position_count = 1  # 買進第 1 份
                return StrategySignal(
                    timestamp=date,
                    action=SignalAction.BUY,
                    quantity=buy_shares,
                    price=open_price,
                    reason=f"站上年線，多頭啟動（MA200: {ma200:,.0f}）",
                )

        # 1. 抄底機制：RSI < 30 後回升至 30 以上（空頭反彈用）
        if rsi is not None:
            if rsi < self.config["rsi_oversold"]:
                self.rsi_was_oversold = True
            elif self.rsi_was_oversold and rsi >= self.config["rsi_oversold"]:
                # RSI 回升，且目前無持倉
                if self.state.positions == 0:
                    self.rsi_was_oversold = False  # 重置標記
                    buy_shares = self._calculate_buy_quantity(open_price)
                    self.position_count = 1  # 買進第 1 份
                    return StrategySignal(
                        timestamp=date,
                        action=SignalAction.BUY,
                        quantity=buy_shares,
                        price=open_price,
                        reason=f"RSI抄底（RSI 從 {rsi:.1f} 回升至 30 以上）",
                    )

        # 2. 加碼規則：收盤價 ≥ 基準價 × 1.03
        if self.state.positions > 0 and self.state.base_price > 0:
            # 檢查是否已達最大份數
            if self.position_count < self.config["num_positions"]:
                add_level = self.state.base_price * self.config["add_threshold"]
                if close_price >= add_level:
                    buy_shares = self._calculate_buy_quantity(open_price)
                    self.position_count += 1  # 加碼增加 1 份
                    return StrategySignal(
                        timestamp=date,
                        action=SignalAction.BUY,
                        quantity=buy_shares,
                        price=open_price,
                        reason=f"加碼（收盤 {close_price:,.0f} ≥ 基準價 {self.state.base_price:,.0f} × 1.03）",
                    )

        # 無訊號
        return None

    def get_config_schema(self) -> dict[str, Any]:
        """取得配置結構。"""
        return {
            "max_positions": {
                "type": "int",
                "default": 10,
                "description": "最大持倉份數",
            },
            "shares_per_position": {
                "type": "int",
                "default": 1000,
                "description": "每份股數（1 張 = 1000 股）",
            },
            "add_threshold": {
                "type": "float",
                "default": 1.03,
                "description": "加碼門檻（基準價的倍數）",
            },
            "reduce_threshold": {
                "type": "float",
                "default": 0.97,
                "description": "減碼門檻（基準價的倍數）",
            },
            "trailing_stop": {
                "type": "float",
                "default": 0.20,
                "description": "移動停利回撤比例（20%）",
            },
            "ma200_stop": {
                "type": "float",
                "default": 0.96,
                "description": "MA200 防禦倍數（0.96 = 跌破 4%）",
            },
            "rsi_oversold": {
                "type": "int",
                "default": 30,
                "description": "RSI 超賣門檻",
            },
        }

    def get_status(self) -> str:
        """取得策略狀態。"""
        if not self.state:
            return "策略尚未初始化"

        status = f"""
=== 進階農夫播種術：{self.ticker} ===

【當前狀態】
基準價：NT$ {self.state.base_price:,.0f}
持倉：{self.state.positions} 份（{self.state.total_shares:,} 股）
平均成本：NT$ {self.state.avg_cost:,.0f}
波段最高：NT$ {self.state.peak_price:,.0f}
可用資金：NT$ {self.state.cash:,.0f}

【規則說明】
"""

        if self.state.base_price > 0:
            add_level = self.state.base_price * self.config["add_threshold"]
            reduce_level = self.state.base_price * self.config["reduce_threshold"]
            status += f"✓ 加碼：收盤價 ≥ NT$ {add_level:,.0f} ({self.state.base_price:,.0f} × 1.03)\n"
            status += f"✓ 減碼：收盤價 ≤ NT$ {reduce_level:,.0f} ({self.state.base_price:,.0f} × 0.97)\n"

        if self.state.peak_price > 0:
            stop_price = self.state.peak_price * (1 - self.config["trailing_stop"])
            status += f"✓ 停利：回落至 NT$ {stop_price:,.0f} ({self.state.peak_price:,.0f} × 0.80)\n"

        status += f"""
【資金控管】
最大份數：{self.config['max_positions']} 份
單份大小：{self.config['shares_per_position']:,} 股
已用份數：{self.state.positions}/{self.config['max_positions']}
"""

        return status
