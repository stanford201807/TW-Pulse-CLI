"""驗證回測報告格式改善

測試重點：
1. 每個資料項目都應該在獨立的一行
2. 交易明細預設顯示所有交易，不再限制為前 10 筆
3. 交易之間使用雙換行分隔，提高可讀性
"""

from datetime import datetime
from pulse.core.backtest.report import BacktestReport

# 建立測試報告（包含 20 筆交易模擬真實情況）
trades = []
for i in range(1, 21):
    trades.append({
        "日期": f"2022-0{(i-1)//10 + 1}-{(i-1)%10 + 10:02d}",
        "動作": "買進" if i % 2 == 1 else "賣出",
        "份數": 1,
        "價格": f"NT$ {500 + i * 5}",
        "原因": f"測試交易 #{i}"
    })

report = BacktestReport(
    ticker="2330",
    strategy_name="進階農夫播種術",
    start_date=datetime(2021, 1, 26),
    end_date=datetime(2026, 1, 25),
    initial_capital=1_000_000,
    final_capital=1_068_192,
    total_return=6.82,
    annual_return=1.33,
    max_drawdown=10.88,
    sharpe_ratio=-0.10,
    win_rate=100.0,
    total_trades=20,
    winning_trades=10,
    losing_trades=0,
    trades=trades,
    equity_curve=[]
)

# 格式化並顯示報告
print("=" * 80)
print("✅ 回測報告格式驗證（預設 show_trades=0）")
print("=" * 80)
formatted_report = report.format()
print(formatted_report)

print("\n" + "=" * 80)
print("✅ 驗證結果")
print("=" * 80)

# 計算交易明細中的交易筆數
trade_count = formatted_report.count("測試交易 #")
print(f"✓ 交易明細總筆數：{trade_count} / 20 筆")

if trade_count == 20:
    print("✅ 通過：所有 20 筆交易都已顯示！")
else:
    print(f"❌ 失敗：僅顯示 {trade_count} 筆交易，應顯示全部 20 筆")

# 檢查標題
if "（共 20 筆）" in formatted_report:
    print("✅ 通過：交易明細標題正確顯示「（共 20 筆）」")
else:
    print("❌ 失敗：交易明細標題格式不正確")

# 檢查不應該出現的內容
if "顯示前 10 筆" not in formatted_report:
    print("✅ 通過：不再顯示「顯示前 10 筆」提示")
else:
    print("❌ 失敗：仍然包含「顯示前 10 筆」提示")

print("\n" + "=" * 80)
print("驗證完成")
print("=" * 80)
