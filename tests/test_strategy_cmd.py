"""測試 strategy 命令的註冊鍵值"""

from pulse.core.strategies import registry

print("=== 策略註冊表內容 ===\n")
strategies = registry.list_strategies()

for idx, strategy_info in enumerate(strategies, 1):
    print(f"{idx}. 策略鍵值 (key): {strategy_info['key']}")
    print(f"   策略名稱 (name): {strategy_info['name']}")
    print(f"   描述: {strategy_info['description']}\n")

print("\n=== 測試不同鍵值查詢 ===\n")

test_keys = ["farmer", "farmerplanting", "1"]
for key in test_keys:
    result = registry.get(key)
    print(f"registry.get('{key}'): {result}")
