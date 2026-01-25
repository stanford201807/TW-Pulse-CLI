"""測試回測報告格式改善

驗證修改後的報告格式是否正確顯示每個項目的斷行
"""

from datetime import datetime
from pulse.core.backtest.report import BacktestReport

# 創建測試報告
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
    trades=[
        {
            "日期": "2021-05-14",
            "動作": "買進",
            "份數": 1,
            "價格": "NT$ 509",
            "原因": "抄底機制（RSI 從 35.2 回升至 30 以上）"
        },
        {
            "日期": "2022-03-08",
            "動作": "賣出",
            "份數": 1,
            "價格": "NT$ 520",
            "原因": "防禦機制觸發（跌破 MA200 555 × 0.96）"
        },
        {
            "日期": "2022-03-10",
            "動作": "買進",
            "份數": 1,
            "價格": "NT$ 542",
            "原因": "抄底機制（RSI 從 38.6 回升至 30 以上）"
        },
    ],
    equity_curve=[]
)

# 格式化並顯示報告
formatted_report = report.format(show_trades=10)

print("=" * 80)
print("回測報告格式驗證")
print("=" * 80)
print(formatted_report)
print("=" * 80)
print("\n✅ 驗證重點：")
print("1. 【回測參數】區塊的每個項目都應該在獨立的一行")
print("2. 【績效指標】區塊的每個項目都應該在獨立的一行")
print("3. 【最終資產】區塊的每個項目都應該在獨立的一行")
print("4. 【交易明細】的每筆交易之間應該有空行分隔")
