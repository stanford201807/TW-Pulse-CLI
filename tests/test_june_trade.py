"""測試2025年6月的交易"""
import asyncio
from datetime import datetime
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy
from pulse.utils.logger import get_logger

# 設定日誌級別為INFO以查看詳細資訊
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    """執行回測"""
    strategy = FarmerPlantingStrategy()
    
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330",
        start_date=datetime(2025, 6, 1),
        end_date=datetime(2025, 6, 15),
        initial_cash=1_437_386,  # 2025-06-02賣出後的資金
    )
    
    print("\n執行回測...")
    report = await engine.run()
    
    print(f"\n總交易: {report.total_trades}次")
    print(f"最終資金: NT$ {report.final_capital:,.0f}")
    
    if strategy.capital_manager:
        print(f"\n資金管理器:")
        print(f"  當前總資金: {strategy.capital_manager.get_current_capital():,.0f}")
        print(f"  每份金額: {strategy.capital_manager.get_position_size():,.0f}")

if __name__ == "__main__":
    asyncio.run(main())
