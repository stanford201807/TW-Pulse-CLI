"""Debug動態資金管理器狀態"""
import asyncio
from datetime import datetime
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy

async def main():
    """執行回測並追蹤資金狀態"""
    print("=" * 70)
    print("Debug動態資金管理器狀態")
    print("=" * 70)
    
    strategy = FarmerPlantingStrategy()
    
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330",
        start_date=datetime(2025, 5, 1),  # 只測試最後幾個月
        end_date=datetime(2025, 7, 1),
        initial_cash=1_400_000,  # 模擬賣出後的資金
    )
    
    print("\n執行回測中...")
    report = await engine.run()
    
    print(f"\n✅ 回測完成")
    print(f"總交易次數: {report.total_trades}")
    print(f"最終資金: NT$ {report.final_capital:,.0f}")
    
    # 檢查資金管理器狀態
    if strategy.capital_manager:
        cm = strategy.capital_manager
        print("\n資金管理器狀態:")
        print(f"  初始資金: {cm.state.initial_capital:,.0f}")
        print(f"  當前總資金: {cm.state.current_capital:,.0f}")
        print(f"  已實現損益: {cm.state.realized_pnl:+,.0f}")
        print(f"  每份金額: {cm.get_position_size():,.0f}")
    
    # 顯示前5筆交易
    print("\n前5筆交易:")
    for i, trade in enumerate(report.trades[:5]):
        print(f"{i+1}. {trade['日期']} {trade['動作']} {trade['股數']}股 @ {trade['價格']}")

if __name__ == "__main__":
    asyncio.run(main())
