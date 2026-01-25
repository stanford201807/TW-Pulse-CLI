"""診斷 2025-06-02 之後無交易的原因

分析防禦機制觸發後，為何沒有後續交易
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

print("=" * 70)
print("診斷 2025-06-02 防禦機制觸發後無交易問題")
print("=" * 70)

# 下載 2025-06 至今的數據
print("\n下載 2025-06-01 至今的 2330.TW 數據...")
df = yf.download('2330.TW', start=datetime(2025, 6, 1), end=datetime(2026, 1, 26), progress=False)

if df.empty:
    print("❌ 無法下載數據")
    exit(1)

df.columns = df.columns.str.lower()
print(f"✓ 下載 {len(df)} 筆數據")
print(f"日期範圍: {df.index.min().date()} ~ {df.index.max().date()}")

# 計算 MA200（需要更長歷史數據）
print("\n下載完整歷史數據以計算 MA200...")
df_full = yf.download('2330.TW', start=datetime(2024, 1, 1), end=datetime(2026, 1, 26), progress=False)
df_full.columns = df_full.columns.str.lower()
df_full['ma200'] = df_full['close'].rolling(window=200).mean()

# 只看 2025-06 之後的數據
df_recent = df_full[df_full.index >= '2025-06-01'].copy()

print(f"\n2025-06-01 之後的數據: {len(df_recent)} 筆")

# 計算 RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df_recent['rsi'] = calculate_rsi(df_full['close'])[df_recent.index]

# 分析
print("\n" + "=" * 70)
print("數據分析")
print("=" * 70)

print(f"\n【2025-06-02 當日狀況】")
if '2025-06-02' in df_recent.index:
    day = df_recent.loc['2025-06-02']
    print(f"收盤價: {day['close']:.2f}")
    print(f"MA200: {day['ma200']:.2f}")
    print(f"防禦價 (MA200×0.96): {day['ma200'] * 0.96:.2f}")
    print(f"RSI: {day['rsi']:.2f}")

print(f"\n【2025-06-02 之後的走勢】")
after_defense = df_recent[df_recent.index > '2025-06-02']

print(f"收盤價範圍: {after_defense['close'].min():.2f} ~ {after_defense['close'].max():.2f}")
print(f"MA200 範圍: {after_defense['ma200'].min():.2f} ~ {after_defense['ma200'].max():.2f}")

# 檢查「站上年線」條件
print("\n【站上年線分析】")
crosses = []
prev_close = None
prev_ma200 = None

for idx in after_defense.index:
    row = after_defense.loc[idx]
    close = row['close']
    ma200 = row['ma200']
    
    if prev_close is not None and prev_ma200 is not None:
        # 檢查是否從年線下方站上年線
        if prev_close <= prev_ma200 and close > ma200:
            crosses.append({
                'date': idx,
                'prev_close': prev_close,
                'close': close,
                'ma200': ma200
            })
    
    prev_close = close
    prev_ma200 = ma200

if crosses:
    print(f"✅ 發現 {len(crosses)} 次站上年線機會：")
    for c in crosses:
        print(f"  {c['date'].date()} | 前日收盤: {c['prev_close']:.2f} → 今日收盤: {c['close']:.2f} | MA200: {c['ma200']:.2f}")
else:
    print("❌ 在此期間，沒有發生「從年線下方站上年線」的情況")
    
    # 分析原因
    below_ma200 = after_defense[after_defense['close'] <= after_defense['ma200']]
    above_ma200 = after_defense[after_defense['close'] > after_defense['ma200']]
    
    print(f"\n  ➡️ 收盤價在年線下方的天數: {len(below_ma200)} 天")
    print(f"  ➡️ 收盤價在年線上方的天數: {len(above_ma200)} 天")
    
    if len(below_ma200) == len(after_defense):
        print("\n  ⚠️ 結論：價格一直在年線下方，沒有站上年線的機會")
    elif len(above_ma200) == len(after_defense):
        print("\n  ⚠️ 結論：價格一直在年線上方，但沒有「從下方穿越」")

# 檢查 RSI 抄底條件
print("\n【RSI 抄底分析】")
rsi_below_30 = after_defense[after_defense['rsi'] < 30]
print(f"RSI < 30 的天數: {len(rsi_below_30)} 天")

if len(rsi_below_30) > 0:
    print("RSI < 30 的日期：")
    for idx in rsi_below_30.head(10).index:
        row = rsi_below_30.loc[idx]
        print(f"  {idx.date()} | RSI: {row['rsi']:.2f} | 收盤: {row['close']:.2f}")
else:
    print("❌ RSI 從未低於 30，無法觸發抄底機制")

# 最近幾天的數據
print("\n【最近 10 個交易日】")
recent_10 = df_recent.tail(10)
for idx in recent_10.index:
    row = recent_10.loc[idx]
    status = "在年線上" if row['close'] > row['ma200'] else "在年線下"
    print(f"  {idx.date()} | 收盤: {row['close']:.0f} | MA200: {row['ma200']:.0f} | RSI: {row['rsi']:.1f} | {status}")

print("\n" + "=" * 70)
print("診斷結論")
print("=" * 70)
