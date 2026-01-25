"""簡化版診斷腳本 - 2025-06-02 後無交易問題"""

import yfinance as yf
from datetime import datetime

print("=" * 60)
print("診斷 2025-06-02 後無交易問題")
print("=" * 60)

# 下載數據
ticker = yf.Ticker('2330.TW')
df = ticker.history(start=datetime(2024, 6, 1), end=datetime(2026, 1, 26))

print(f"\n下載 {len(df)} 筆數據")
print(f"最後交易日: {df.index[-1].date()}")

# 計算 MA200
df['MA200'] = df['Close'].rolling(window=200).mean()

# 計算 RSI
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# 只看 2025-06-02 之後
after = df[df.index >= '2025-06-02']

print(f"\n2025-06-02 之後共 {len(after)} 個交易日")
print(f"最新日期: {after.index[-1].date()}")

# 分析站上年線
print("\n" + "=" * 60)
print("【站上年線分析】")
print("=" * 60)

prev_close = None
prev_ma200 = None
crosses = []

for idx in after.index:
    close = after.loc[idx, 'Close']
    ma200 = after.loc[idx, 'MA200']
    
    if prev_close is not None and prev_ma200 is not None:
        if prev_close <= prev_ma200 and close > ma200:
            crosses.append((idx, prev_close, close, ma200))
    
    prev_close = close
    prev_ma200 = ma200

if crosses:
    print(f"✅ 發現 {len(crosses)} 次站上年線:")
    for date, prev_c, curr_c, ma in crosses:
        print(f"  {date.date()} | 前收: {prev_c:.0f} → 今收: {curr_c:.0f} | MA200: {ma:.0f}")
else:
    print("❌ 沒有「站上年線」的機會")
    
    below = after[after['Close'] <= after['MA200']]
    above = after[after['Close'] > after['MA200']]
    print(f"  在年線下方: {len(below)} 天")
    print(f"  在年線上方: {len(above)} 天")

# 分析 RSI 抄底
print("\n" + "=" * 60)
print("【RSI 抄底分析】")
print("=" * 60)

below_30 = after[after['RSI'] < 30]
print(f"RSI < 30 的天數: {len(below_30)}")

if len(below_30) > 0:
    print("日期列表:")
    for idx in below_30.head(5).index:
        print(f"  {idx.date()} | RSI: {after.loc[idx, 'RSI']:.1f}")
else:
    print("❌ RSI 從未低於 30")

# 最近數據
print("\n" + "=" * 60)
print("【最近 5 個交易日】")
print("=" * 60)
for idx in after.tail(5).index:
    row = after.loc[idx]
    status = "↑ 在年線上" if row['Close'] > row['MA200'] else "↓ 在年線下"
    print(f"{idx.date()} | 收盤: {row['Close']:.0f} | MA200: {row['MA200']:.0f} | RSI: {row['RSI']:.1f} | {status}")

print("\n" + "=" * 60)
print("結論")
print("=" * 60)
