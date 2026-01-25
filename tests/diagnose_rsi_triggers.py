"""簡化版診斷腳本 - 分析 RSI 觸發點

重點：檢查 2022-10-27 之後是否有 RSI < 30 再回升的情況
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

# 下載數據
print("下載 2022-10 至 2025-05 的 2330.TW 數據...")
df = yf.download('2330.TW', start=datetime(2022, 10, 1), end=datetime(2025, 5, 1), progress=False)
df.columns = df.columns.str.lower()

print(f"\n總共 {len(df)} 筆數據")
print(f"日期範圍: {df.index.min().date()} ~ {df.index.max().date()}")

# 手動計算 RSI (使用 14 天)
def calculate_rsi(prices, period=14):
    """計算 RSI 指標"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calculate_rsi(df['close'])

print(f"\nRSI 統計:")
print(f"  最小值: {df['rsi'].min():.2f}")
print(f"  最大值: {df['rsi'].max():.2f}")
print(f"  平均值: {df['rsi'].mean():.2f}")

# 找出 RSI < 30 的日期
oversold_df = df[df['rsi'] < 30].copy()
print(f"\nRSI < 30 的天數: {len(oversold_df)} 天")

if len(oversold_df) > 0:
    print(f"\n首次出現: {oversold_df.index.min().date()}")
    print(f"最後出現: {oversold_df.index.max().date()}")
    print(f"\n詳細列表(前10筆):")
    for idx in oversold_df.head(10).index:
        row = df.loc[idx]
        print(f"  {idx.date()} | RSI: {row['rsi']:.2f} | 收盤: {row['close']:.2f}")

# 分析觸發點: RSI 從 < 30 回升至 >= 30
print(f"\n" + "=" * 60)
print("抄底觸發點分析 (RSI 從 <30 回升至 >=30)")
print("=" * 60)

rs_was_oversold = False
triggers = []

for idx in df.index:
    rsi = df.loc[idx, 'rsi']
    
    if pd.isna(rsi):
        continue
        
    if rsi < 30:
        rsi_was_oversold = True
    elif rsi_was_oversold and rsi >= 30:
        triggers.append({
            'date': idx,
            'rsi': rsi,
            'close': df.loc[idx, 'close'],
            'open': df.loc[idx, 'open']
        })
        rsi_was_oversold = False

print(f"\n觸發點總數: {len(triggers)} 次\n")

if triggers:
    for i, t in enumerate(triggers, 1):
        print(f"{i}. {t['date'].date()} | RSI: {t['rsi']:.2f} | 收盤: NT${t['close']:.0f} | 開盤: NT${t['open']:.0f}")
        
    print(f"\n✓ 第一個觸發點: {triggers[0]['date'].date()}")
    print(f"  回測結果顯示的第一筆買進: 2025-04-10")
    
    if triggers[0]['date'].date().year < 2025:
        print(f"\n❌ 數據不一致！")
        print(f"   診斷腳本發現 {triggers[0]['date'].date()} 就應該觸發買進")
        print(f"   但回測結果直到 2025-04-10 才買進")
else:
    print("❌ 整個期間沒有任何觸發點")
    print("   這解釋了為何長期沒有買進訊號")
