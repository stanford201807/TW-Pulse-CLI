"""策略註冊與管理系統。"""

from typing import Type

from pulse.core.strategies.base import BaseStrategy
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class StrategyRegistry:
    """策略註冊表。

    管理所有可用的交易策略，提供註冊、查詢和列表功能。
    """

    def __init__(self):
        self._strategies: dict[str, Type[BaseStrategy]] = {}

    def register(self, strategy_class: Type[BaseStrategy]) -> None:
        """註冊策略。

        Args:
            strategy_class: 策略類別（必須繼承 BaseStrategy）
        """
        # 使用類別名稱的小寫作為鍵值
        key = strategy_class.__name__.lower().replace("strategy", "")
        self._strategies[key] = strategy_class
        log.info(f"Registered strategy: {key}")

    def get(self, name: str) -> Type[BaseStrategy] | None:
        """取得策略類別。

        Args:
            name: 策略名稱

        Returns:
            策略類別，如果不存在則返回 None
        """
        return self._strategies.get(name.lower())

    def list_strategies(self) -> list[dict[str, str]]:
        """列出所有已註冊的策略。

        Returns:
            策略列表，每個策略包含 name 和 description
        """
        strategies = []
        for key, strategy_class in self._strategies.items():
            # 創建臨時實例以取得名稱和描述
            temp_instance = strategy_class()
            strategies.append(
                {
                    "key": key,
                    "name": temp_instance.name,
                    "description": temp_instance.description,
                }
            )
        return strategies


# 全域策略註冊表
registry = StrategyRegistry()
