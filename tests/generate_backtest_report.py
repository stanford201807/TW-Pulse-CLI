"""執行回測並輸出報表到 report 資料夾"""

import asyncio
from datetime import datetime
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy

async def run_and_save_report():
    """執行回測並保存報表"""
    
    print("=" * 70)
    print("執行 /strategy farmerplanting 2330 backtest")
    print("=" * 70)
    
    # 建立策略
    strategy = FarmerPlantingStrategy()
    
    # 建立回測引擎
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330",
        start_date=datetime(2021, 1, 26),
        end_date=datetime(2026, 1, 25),
        initial_cash=1_000_000,
    )
    
    # 執行回測
    print("\n執行回測中...")
    report = await engine.run()
    
    # 格式化報告（顯示所有交易）
    formatted_report = report.format(show_trades=0)
    
    # 輸出到控制台
    print(formatted_report)
    
    # 生成報表檔案
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report/backtest_{report.ticker}_{timestamp}.md"
    
    # 建立 Markdown 報表
    md_report = f"""# 回測報告：{report.strategy_name} - {report.ticker}

**生成時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 回測參數

| 項目 | 數值 |
|------|------|
| 期間 | {report.start_date.strftime('%Y-%m-%d')} 至 {report.end_date.strftime('%Y-%m-%d')} |
| 初始資金 | NT$ {report.initial_capital:,.0f} |
| 回測天數 | {(report.end_date - report.start_date).days} 天 |

---

## 📈 績效指標

| 指標 | 數值 |
|------|------|
| 總報酬率 | {report.total_return:+.2f}% |
| 年化報酬率 | {report.annual_return:+.2f}% |
| 最大回撤 | {report.max_drawdown:.2f}% |
| 夏普比率 | {report.sharpe_ratio:.2f} |
| 勝率 | {report.win_rate:.1f}% |
| 總交易次數 | {report.total_trades} 次 |
| 獲利交易 | {report.winning_trades} 次 |
| 虧損交易 | {report.losing_trades} 次 |

---

## 💰 最終資產

| 項目 | 數值 |
|------|------|
| 最終資金 | NT$ {report.final_capital:,.0f} |
| 總損益 | NT$ {report.final_capital - report.initial_capital:+,.0f} |

---

## 📋 交易明細

共 {len(report.trades)} 筆交易

| 日期 | 動作 | 份數 | 價格 | 原因 |
|------|------|------|------|------|
"""
    
    # 加入交易明細
    for trade in report.trades:
        md_report += f"| {trade['日期']} | {trade['動作']} | {trade['份數']}份 | {trade['價格']} | {trade['原因']} |\n"
    
    md_report += """
---

*此報表由 TW-Pulse-CLI 自動生成*
"""
    
    # 寫入檔案
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"\n" + "=" * 70)
    print(f"✅ 報表已儲存: {filename}")
    print("=" * 70)
    
    return filename

if __name__ == "__main__":
    asyncio.run(run_and_save_report())
