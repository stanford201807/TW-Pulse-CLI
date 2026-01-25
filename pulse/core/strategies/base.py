"""策略模組基礎類別與資料模型。

此模組定義了所有交易策略必須實作的基礎介面，
以及策略執行過程中使用的資料結構。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class SignalAction(str, Enum):
    """交易訊號動作"""

    BUY = "買進"
    SELL = "賣出"
    HOLD = "持有"


@dataclass
class StrategySignal:
    """策略產生的交易訊號。

    Attributes:
        timestamp: 訊號產生時間
        action: 交易動作（買進/賣出/持有）
        quantity: 交易數量（份數）
        price: 建議價格
        reason: 訊號原因說明
    """

    timestamp: datetime
    action: SignalAction
    quantity: int
    price: float
    reason: str

    def __str__(self) -> str:
        return (
            f"{self.timestamp.strftime('%Y-%m-%d')} | "
            f"{self.action.value} {self.quantity}份 @ NT$ {self.price:,.0f} | "
            f"{self.reason}"
        )


@dataclass
class StrategyState:
    """策略執行狀態。

    記錄策略運行過程中的關鍵狀態資訊。

    Attributes:
        positions: 當前持倉份數
        base_price: 基準價（用於計算加減碼）
        peak_price: 波段最高點（用於移動停利）
        total_shares: 總持股數
        avg_cost: 平均成本
        cash: 可用現金
        total_capital: 當前總資金（動態資金管理用）
        realized_pnl: 已實現損益（動態資金管理用）
    """

    positions: int = 0
    base_price: float = 0.0
    peak_price: float = 0.0
    total_shares: int = 0
    avg_cost: float = 0.0
    cash: float = 0.0
    total_capital: float = 0.0  # 新增：動態資金管理
    realized_pnl: float = 0.0   # 新增：已實現損益


    def update_position(
        self, quantity: int, price: float, shares_per_position: int
    ) -> None:
        """更新持倉狀態。

        Args:
            quantity: 變動份數（正數為買入，負數為賣出）
            price: 成交價格
            shares_per_position: 每份股數
        """
        shares = quantity * shares_per_position

        if quantity > 0:  # 買進
            total_cost = self.avg_cost * self.total_shares + price * shares
            self.total_shares += shares
            self.avg_cost = total_cost / self.total_shares if self.total_shares > 0 else 0
            self.cash -= price * shares
        elif quantity < 0:  # 賣出
            self.total_shares += shares  # shares 是負數
            if self.total_shares == 0:
                self.avg_cost = 0
            self.cash += price * abs(shares)

        self.positions += quantity
        self.base_price = price  # 更新基準價


class BaseStrategy(ABC):
    """交易策略基礎類別。

    所有交易策略都必須繼承此類別並實作其抽象方法。

    Attributes:
        name: 策略名稱
        description: 策略描述
        state: 策略執行狀態
        config: 策略配置參數
    """

    def __init__(self, name: str, description: str):
        """初始化策略。

        Args:
            name: 策略名稱
            description: 策略描述
        """
        self.name = name
        self.description = description
        self.state: StrategyState | None = None
        self.config: dict[str, Any] = {}

    @abstractmethod
    async def initialize(
        self, ticker: str, initial_cash: float, config: dict[str, Any]
    ) -> None:
        """初始化策略狀態。

        Args:
            ticker: 股票代碼
            initial_cash: 初始資金
            config: 策略配置參數
        """
        pass

    @abstractmethod
    async def on_bar(
        self, bar: dict[str, Any], indicators: dict[str, Any]
    ) -> StrategySignal | None:
        """處理每根K線數據。

        Args:
            bar: K線數據 (包含 date, open, high, low, close, volume)
            indicators: 技術指標數據 (如 RSI, MA200 等)

        Returns:
            交易訊號，如果無訊號則返回 None
        """
        pass

    @abstractmethod
    def get_config_schema(self) -> dict[str, Any]:
        """取得策略配置結構定義。

        Returns:
            配置結構的字典，包含參數名稱、類型、預設值等
        """
        pass

    def get_status(self) -> str:
        """取得策略當前狀態的文字描述。

        Returns:
            格式化的狀態字串
        """
        if not self.state:
            return "策略尚未初始化"

        return f"""
【策略狀態】
持倉: {self.state.positions} 份 ({self.state.total_shares:,} 股)
基準價: NT$ {self.state.base_price:,.0f}
平均成本: NT$ {self.state.avg_cost:,.0f}
波段最高: NT$ {self.state.peak_price:,.0f}
可用資金: NT$ {self.state.cash:,.0f}
"""
