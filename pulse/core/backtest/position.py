"""持倉管理模組。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:
    """單筆交易記錄。

    Attributes:
        date: 交易日期
        action: 動作（買進/賣出）
        quantity: 數量（份數）
        price: 價格
        shares: 股數
        amount: 金額
        reason: 交易原因
    """

    date: datetime
    action: str
    quantity: int
    price: float
    shares: int
    amount: float
    reason: str

    def to_dict(self) -> dict:
        """轉換為字典。"""
        return {
            "日期": self.date.strftime("%Y-%m-%d"),
            "動作": self.action,
            "價格": f"NT$ {self.price:,.0f}",
            "份數": self.quantity,
            "股數": self.shares,
            "金額": f"NT$ {self.amount:,.0f}",
            "原因": self.reason,
        }


class PositionManager:
    """持倉管理器。

    追蹤持倉狀態、計算盈虧、記錄交易明細。
    直接以股數為單位進行交易，支持零股。
    """

    def __init__(self, initial_cash: float):
        """初始化持倉管理器。

        Args:
            initial_cash: 初始資金
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash

        self.positions = 0  # 持倉股數
        self.total_shares = 0  # 總股數（與 positions 相同，保留以相容）
        self.avg_cost = 0.0  # 平均成本

        self.trades: list[Trade] = []  # 交易記錄
        self.equity_curve: list[dict] = []  # 權益曲線

    def execute_trade(
        self, date: datetime, action: str, quantity: int, price: float, reason: str
    ) -> bool:
        """執行交易。

        Args:
            date: 交易日期
            action: 動作（買進/賣出）
            quantity: 股數
            price: 價格
            reason: 原因

        Returns:
            是否成功執行
        """
        # quantity 直接代表股數
        shares = quantity
        amount = price * shares

        if action == "買進":
            # 檢查現金是否足夠
            if amount > self.cash:
                return False

            # 更新平均成本
            total_cost = self.avg_cost * self.total_shares + amount
            self.total_shares += shares
            self.avg_cost = total_cost / self.total_shares if self.total_shares > 0 else 0

            self.cash -= amount
            self.positions += shares

        elif action == "賣出":
            # 檢查持股是否足夠
            if shares > self.positions:
                return False

            self.total_shares -= shares
            if self.total_shares < 0:
                self.total_shares = 0
            if self.total_shares == 0:
                self.avg_cost = 0

            self.cash += amount
            self.positions -= shares

        # 記錄交易
        trade = Trade(
            date=date,
            action=action,
            quantity=shares,
            price=price,
            shares=shares,
            amount=amount,
            reason=reason,
        )
        self.trades.append(trade)

        return True

    def update_equity(self, date: datetime, current_price: float) -> None:
        """更新權益曲線。

        Args:
            date: 日期
            current_price: 當前價格
        """
        position_value = self.total_shares * current_price
        total_equity = self.cash + position_value

        self.equity_curve.append(
            {
                "date": date,
                "cash": self.cash,
                "position_value": position_value,
                "total_equity": total_equity,
                "price": current_price,
            }
        )

    def get_total_equity(self, current_price: float) -> float:
        """取得總權益。

        Args:
            current_price: 當前價格

        Returns:
            總權益（現金 + 持倉市值）
        """
        position_value = self.total_shares * current_price
        return self.cash + position_value

    def get_return(self, current_price: float) -> float:
        """取得總報酬率。

        Args:
            current_price: 當前價格

        Returns:
            報酬率（百分比）
        """
        final_equity = self.get_total_equity(current_price)
        return ((final_equity - self.initial_cash) / self.initial_cash) * 100
