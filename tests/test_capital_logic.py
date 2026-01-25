"""簡單測試：直接檢查資金管理器邏輯"""
from pulse.core.capital.capital_manager import DynamicCapitalManager

# 模擬場景
print("=" * 70)
print("測試：2025-06-02 賣出後，2025-06-05 買進")
print("=" * 70)

# 初始化（模擬2025-06-02賣出後的狀態）
manager = DynamicCapitalManager(initial_capital=1_000_000, num_positions=10)

# 模擬之前的盈利（賣出後總資金應為 1,437,386）
profit = 437_386
manager.update_capital(profit)

print(f"\n賣出後狀態:")
print(f"  當前總資金: {manager.get_current_capital():,.0f}")
print(f"  每份金額: {manager.get_position_size():,.0f}")

# 計算2025-06-05的買進股數
price = 988.51
shares = manager.calculate_shares(price)
cost = shares * price

print(f"\n2025-06-05 買進計算:")
print(f"  股價: {price:,.2f}")
print(f"  計算股數: {shares:,}")
print(f"  實際花費: {cost:,.0f}")
print(f"  預期花費: {manager.get_position_size():,.0f}")
print(f"  差異: {cost - manager.get_position_size():+,.0f}")
