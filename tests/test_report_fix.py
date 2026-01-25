"""快速測試修正後的報表生成邏輯。"""

import asyncio
from datetime import datetime

from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy


async def test_report_fix():
    """測試修正後的報表生成。"""
    print("=" * 60)
    print("測試修正後的資金份數計算")
    print("=" * 60)
    
    strategy = FarmerPlantingStrategy()
    
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330.TW",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2026, 1, 25),
        initial_cash=2_000_000,
    )
    
    print(f"\n執行回測...")
    report = await engine.run()
    
    print(f"\n總交易次數: {report.total_trades}")
    
    import os
    detailed_reports = [f for f in os.listdir("report") if "detailed" in f and "2330.TW" in f]
    if detailed_reports:
        latest = sorted(detailed_reports)[-1]
        print(f"\n✅ 詳細報表: report/{latest}")
        
        # 顯示報表前15行
        print("\n報表預覽:")
        print("-" * 60)
        with open(f"report/{latest}", "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < 15:
                    print(line.rstrip())
                elif "|" in line and i < 25:  # 多顯示幾筆交易記錄
                    print(line.rstrip())
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_report_fix())
