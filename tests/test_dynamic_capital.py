"""測試動態資金管理回測功能（5年期）。"""

import asyncio
from datetime import datetime, timedelta

from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy


async def test_long_term_backtest():
    """測試5年期動態資金管理回測功能。"""
    print("=" * 60)
    print("動態資金管理回測測試（5年期）")
    print("=" * 60)
    
    # 建立策略（啟用動態資金管理）
    strategy = FarmerPlantingStrategy()
    
    # 建立回測引擎
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330.TW",
        start_date=datetime(2021, 1, 26),
        end_date=datetime(2026, 1, 25),
        initial_cash=2_000_000,  # 初始資金 200 萬
    )
    
    print(f"\n股票代碼: 2330.TW (台積電)")
    print(f"回測期間: 2021-01-26 ~ 2026-01-25 (5年)")
    print(f"初始資金: NT$ 2,000,000")
    print(f"動態資金管理: 啟用\n")
    
    # 執行回測
    report = await engine.run()
    
    # 顯示結果摘要
    print("\n" + "=" * 60)
    print("回測完成！")
    print("=" * 60)
    
    print(f"\n總報酬率: {report.total_return:.2f}%")
    print(f"年化報酬率: {report.annualized_return:.2f}%")
    print(f"總交易次數: {report.total_trades}")
    print(f"最終資金: NT$ {report.final_equity:,.0f}")
    print(f"總損益: NT$ {report.total_pnl:+,.0f}")
    
    print("\n✅ 標準回測報表已生成")
    report_path = report.save_to_markdown()
    print(f"📄 路徑: {report_path}")
    
    # 檢查詳細報表是否生成
    import os
    detailed_reports = [f for f in os.listdir("report") if "detailed" in f and "2330.TW" in f]
    if detailed_reports:
        latest_detailed = sorted(detailed_reports)[-1]
        print("\n✅ 動態資金詳細報表已生成")
        print(f"📄 路徑: report/{latest_detailed}")
        
        # 讀取並顯示報表前20行
        print("\n" + "-" * 60)
        print("詳細報表預覽（前 20 行）:")
        print("-" * 60)
        with open(f"report/{latest_detailed}", "r", encoding="utf-8") as f:
            lines = f.readlines()[:20]
            print("".join(lines))
        
        # 顯示報表統計
        with open(f"report/{latest_detailed}", "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            print(f"\n報表總行數: {len(all_lines)}")
    else:
        print("\n⚠️  詳細報表未生成（可能未啟用動態資金管理）")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_long_term_backtest())
