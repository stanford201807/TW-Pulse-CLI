"""診斷 2022-2025 期間策略為何無交易訊號

分析重點：
1. RSI 數據分布
2. 是否有 RSI < 30 的情況
3. 價格走勢分析
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import sys
sys.path.insert(0, 'D:\\GitHub\\TW-Pulse-CLI')

from pulse.core.analysis.technical import TechnicalAnalyzer

# 下載數據
print("=" * 80)
print("下載 2022-10 至 2025-05 期間的 2330.TW 數據")
print("=" * 80)

df = yf.download('2330.TW', start=datetime(2022, 10, 1), end=datetime(2025, 5, 1), progress=False)

if df.empty:
    print("❌ 無法下載數據")
    exit(1)

df.columns = df.columns.str.lower()
print(f"\n✓ 下載成功：{len(df)} 筆數據")
print(f"日期範圍：{df.index.min()} 至 {df.index.max()}")

# 計算技術指標
print("\n" + "=" * 80)
print("計算技術指標（RSI、MA200）")
print("=" * 80)

import asyncio

analyzer = TechnicalAnalyzer()
indicators_df = asyncio.run(analyzer.calculate_indicators(df))

if indicators_df is None or indicators_df.empty:
    print("❌ 技術指標計算失敗")
    exit(1)

print(f"✓ 指標計算完成")

# 分析 RSI
print("\n" + "=" * 80)
print("RSI 分析")
print("=" * 80)

rsi_data = indicators_df['RSI_14'].dropna()
print(f"RSI 最低值：{rsi_data.min():.2f}")
print(f"RSI 最高值：{rsi_data.max():.2f}")
print(f"RSI 平均值：{rsi_data.mean():.2f}")

# 檢查 RSI < 30 的情況
oversold = indicators_df[indicators_df['RSI_14'] < 30]
print(f"\n✓ RSI < 30 的天數：{len(oversold)} 天")

if len(oversold) > 0:
    print(f"\nRSI < 30 的日期範圍：")
    print(f"首次：{oversold.index.min()}")
    print(f"末次：{oversold.index.max()}")
    print(f"\n詳細列表（前 10 筆）：")
    for idx, row in oversold.head(10).iterrows():
        print(f"  {idx.date()} | RSI: {row['RSI_14']:.2f} | Close: {row['close']:.2f}")

# 檢查 RSI 從 < 30 回升至 >= 30 的時點
print("\n" + "=" * 80)
print("RSI 從 <30 回升至 >=30 的觸發點分析")
print("=" * 80)

rsi_was_oversold = False
triggers = []

for i in range(len(indicators_df)):
    row = indicators_df.iloc[i]
    rsi = row['RSI_14']
    
    if pd.isna(rsi):
        continue
    
    if rsi < 30:
        rsi_was_oversold = True
    elif rsi_was_oversold and rsi >= 30:
        triggers.append({
            'date': row.name,
            'rsi': rsi,
            'close': row['close'],
            'open': row['open']
        })
        rsi_was_oversold = False

print(f"\n✓ 抄底觸發點總數：{len(triggers)} 次")

if triggers:
    print(f"\n抄底觸發點列表：")
    for t in triggers[:20]:  # 顯示前 20 個
        print(f"  {t['date'].date()} | RSI: {t['rsi']:.2f} | Close: {t['close']:.2f} | Open: {t['open']:.2f}")

# 價格統計
print("\n" + "=" * 80)
print("價格走勢分析")
print("=" * 80)

print(f"最高價：NT$ {indicators_df['close'].max():.2f}")
print(f"最低價：NT$ {indicators_df['close'].min():.2f}")
print(f"期初價：NT$ {indicators_df.iloc[0]['close']:.2f}")
print(f"期末價：NT$ {indicators_df.iloc[-1]['close']:.2f}")
print(f"漲跌幅：{(indicators_df.iloc[-1]['close'] / indicators_df.iloc[0]['close'] - 1) * 100:.2f}%")

print("\n" + "=" * 80)
print("結論")
print("=" * 80)

if len(triggers) == 0:
    print("❌ 整個期間沒有任何抄底觸發點（RSI 從 <30 回升至 >=30）")
    print("   這解釋了為何 2022-10-27 之後沒有買進訊號")
elif len(triggers) > 0:
    print(f"✓ 發現 {len(triggers)} 個抄底觸發點")
    print("  但回測結果顯示直到 2025-04-10 才有買進")
    print("  可能原因：")
    print("  1. 早期觸發點的 RSI 數據計算問題")
    print("  2. RSI 指標延遲（需要足夠的歷史數據）")
    print("  3. 回測引擎的數據處理順序問題")
