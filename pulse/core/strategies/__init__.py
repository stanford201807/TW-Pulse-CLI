"""策略模組初始化。

自動導入並註冊所有可用的策略。
"""

from pulse.core.strategies.base import BaseStrategy, SignalAction, StrategySignal, StrategyState
from pulse.core.strategies.registry import registry

# 導入策略實作並自動註冊
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy

registry.register(FarmerPlantingStrategy)

__all__ = [
    "BaseStrategy",
    "StrategySignal",
    "StrategyState",
    "SignalAction",
    "registry",
]
