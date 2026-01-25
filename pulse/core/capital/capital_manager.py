"""動態資金管理模組。

實現依據盈虧動態調整資金配置的邏輯。
"""

from dataclasses import dataclass, field
from typing import Optional

from pulse.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class CapitalState:
    """資金狀態資料類別。

    Attributes:
        initial_capital: 初始資金
        current_capital: 當前總資金（含已實現損益）
        num_positions: 總份數（預設 10）
        realized_pnl: 已實現損益
        peak_price: 波段最高價（用於計算回落）
        last_trade_price: 上次交易價格
    """

    initial_capital: float
    current_capital: float
    num_positions: int = 10
    realized_pnl: float = 0.0
    peak_price: float = 0.0
    last_trade_price: float = 0.0

    def __post_init__(self):
        """初始化後驗證。"""
        if self.initial_capital <= 0:
            raise ValueError("初始資金必須大於 0")
        if self.num_positions <= 0:
            raise ValueError("總份數必須大於 0")


class DynamicCapitalManager:
    """動態資金管理器。

    根據盈虧自動調整每份可用資金，實現動態資金管理。

    Example:
        >>> manager = DynamicCapitalManager(initial_capital=1_000_000, num_positions=10)
        >>> # 盈利後，總資金增加
        >>> manager.update_capital(profit=50_000)
        >>> manager.get_current_capital()  # 1,050,000
        >>> manager.get_position_size()    # 105,000 (1,050,000 / 10)
    """

    def __init__(self, initial_capital: float, num_positions: int = 10):
        """初始化資金管理器。

        Args:
            initial_capital: 初始資金
            num_positions: 總份數（預設 10）

        Raises:
            ValueError: 參數無效時
        """
        self.state = CapitalState(
            initial_capital=initial_capital,
            current_capital=initial_capital,
            num_positions=num_positions,
        )
        log.info(
            f"Initialized DynamicCapitalManager: "
            f"initial={initial_capital:,.0f}, positions={num_positions}"
        )

    def update_capital(self, profit_or_loss: float) -> None:
        """更新總資金（記錄已實現損益）。

        Args:
            profit_or_loss: 損益金額（正數為盈利，負數為虧損）
        """
        self.state.realized_pnl += profit_or_loss
        self.state.current_capital = self.state.initial_capital + self.state.realized_pnl

        log.debug(
            f"Capital updated: PnL={profit_or_loss:+,.0f}, "
            f"Total={self.state.current_capital:,.0f}"
        )

    def get_current_capital(self) -> float:
        """取得當前總資金。

        Returns:
            當前總資金
        """
        return self.state.current_capital

    def get_position_size(self) -> float:
        """計算每份可用資金。

        Returns:
            每份金額 = 當前總資金 ÷ 總份數
        """
        return self.state.current_capital / self.state.num_positions

    def calculate_shares(self, price: float) -> int:
        """計算可買進股數（依據動態份額）。

        Args:
            price: 當前股價

        Returns:
            可買進股數（向下取整）

        Raises:
            ValueError: 股價無效時
        """
        if price <= 0:
            raise ValueError("股價必須大於 0")

        position_size = self.get_position_size()
        shares = int(position_size / price)

        log.debug(f"Calculated shares: {shares} @ {price:,.2f} (size={position_size:,.0f})")
        return shares

    def update_peak_price(self, current_price: float) -> None:
        """更新波段最高價。

        Args:
            current_price: 當前價格
        """
        if current_price > self.state.peak_price:
            self.state.peak_price = current_price
            log.debug(f"Peak price updated: {current_price:,.2f}")

    def calculate_drawdown_percent(self, current_price: float) -> float:
        """計算從波段最高點的回落百分比。

        Args:
            current_price: 當前價格

        Returns:
            回落百分比（0-100）
        """
        if self.state.peak_price <= 0:
            return 0.0

        drawdown = (self.state.peak_price - current_price) / self.state.peak_price * 100
        return max(0.0, drawdown)

    def record_trade(self, price: float, is_buy: bool) -> None:
        """記錄交易價格。

        Args:
            price: 成交價格
            is_buy: 是否為買進
        """
        self.state.last_trade_price = price
        action = "買進" if is_buy else "賣出"
        log.debug(f"Trade recorded: {action} @ {price:,.2f}")

    def get_state(self) -> CapitalState:
        """取得資金狀態。

        Returns:
            CapitalState 實例
        """
        return self.state

    def get_status_summary(self) -> str:
        """取得資金狀態摘要（格式化文字）。

        Returns:
            格式化的狀態字串
        """
        pnl_sign = "+" if self.state.realized_pnl >= 0 else ""
        return f"""
【動態資金狀態】
初始資金：NT$ {self.state.initial_capital:,.0f}
當前總資金：NT$ {self.state.current_capital:,.0f}
已實現損益：{pnl_sign}NT$ {self.state.realized_pnl:,.0f}
每份金額：NT$ {self.get_position_size():,.0f}
總份數：{self.state.num_positions}
波段最高價：NT$ {self.state.peak_price:,.2f}
"""
