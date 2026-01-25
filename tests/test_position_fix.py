"""測試修正後的資金份數計算"""
import asyncio
from datetime import datetime
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy
from pulse.reports.trade_report import TradeReportGenerator

async def main():
    """執行回測並生成詳細報表"""
    print("=" * 70)
    print("測試修正後的資金份數計算")
    print("=" * 70)
    
    strategy = FarmerPlantingStrategy()
    
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330",
        start_date=datetime(2021, 1, 26),
        end_date=datetime(2026, 1, 25),
        initial_cash=1_000_000,
    )
    
    print("\n執行回測中...")
    report = await engine.run()
    
    # 使用 BacktestReport 的 save_to_markdown 方法生成詳細報表
    # 傳入 position_manager 以啟用動態資金詳細表格
    filename = report.save_to_markdown(
        directory="report",
        position_manager=engine._last_position_manager
    )
    
    print(f"\n✅ 報表已儲存: {filename}")
    print("\n" + "=" * 70)
    print("驗證關鍵交易（2021-2022）:")
    print("=" * 70)
    
    # 讀取並顯示報表的關鍵部分
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # 找到交易明細表格並輸出前 20 行
    table_start = 0
    for i, line in enumerate(lines):
        if '| 日期' in line and '| 動作 |' in line:
            table_start = i
            break
    
    if table_start > 0:
        for line in lines[table_start:table_start + 22]:
            print(line.rstrip())

if __name__ == "__main__":
    asyncio.run(main())
