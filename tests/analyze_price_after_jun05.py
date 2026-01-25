"""分析 2025-06-05 買進後為何沒有加碼/減碼"""

import yfinance as yf
from datetime import datetime

# 下載數據
ticker = yf.Ticker('2330.TW')
df = ticker.history(start=datetime(2025, 6, 1), end=datetime(2026, 1, 26))

print("=" * 70)
print("分析 2025-06-05 買進後的價格走勢")
print("=" * 70)

# 2025-06-05 買進開盤價
base_price = 989
add_level = base_price * 1.03  # 1018.67
reduce_level = base_price * 0.97  # 959.33

print(f"\n基準價: {base_price}")
print(f"加碼條件: 收盤 >= {add_level:.0f} (基準價×1.03)")
print(f"減碼條件: 收盤 <= {reduce_level:.0f} (基準價×0.97)")

print(f"\n2025-06-05 之後的價格 (找出觸發點):")
print("-" * 70)

after_jun05 = df[df.index >= '2025-06-05']

for idx in after_jun05.head(30).index:
    close = after_jun05.loc[idx, 'Close']
    
    add_trigger = close >= add_level
    reduce_trigger = close <= reduce_level
    
    if add_trigger or reduce_trigger:
        marker = "⬆️ 加碼!" if add_trigger else "⬇️ 減碼!"
        print(f"{idx.date()} | 收盤: {close:.0f} | {marker}")
    else:
        print(f"{idx.date()} | 收盤: {close:.0f}")

print("\n" + "=" * 70)
print("結論")
print("=" * 70)

# 檢查是否有任何日期滿足加碼條件
add_days = after_jun05[after_jun05['Close'] >= add_level]
reduce_days = after_jun05[after_jun05['Close'] <= reduce_level]

print(f"\n收盤價 >= {add_level:.0f} 的天數: {len(add_days)}")
if len(add_days) > 0:
    print(f"首次達到: {add_days.index[0].date()} (收盤 {add_days.iloc[0]['Close']:.0f})")
    
print(f"\n收盤價 <= {reduce_level:.0f} 的天數: {len(reduce_days)}")
if len(reduce_days) > 0:
    print(f"首次達到: {reduce_days.index[0].date()} (收盤 {reduce_days.iloc[0]['Close']:.0f})")
