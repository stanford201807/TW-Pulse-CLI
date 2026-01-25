"""測試策略命令功能

此測試腳本用於驗證策略模組系統的核心功能：
1. 策略註冊機制
2. 策略列表顯示
3. 策略詳情查詢
4. 策略鍵值解析
"""
import asyncio
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pulse.core.strategies import registry


async def test_strategy_registration():
    """測試 1: 驗證策略註冊"""
    print("=" * 70)
    print("測試 1: 策略註冊機制")
    print("=" * 70)
    
    strategies = registry.list_strategies()
    
    if not strategies:
        print("❌ 失敗：沒有找到任何已註冊的策略")
        return False
    
    print(f"✅ 成功：找到 {len(strategies)} 個已註冊的策略")
    
    for idx, strategy_info in enumerate(strategies, 1):
        print(f"  {idx}. 鍵值: {strategy_info['key']}")
        print(f"     名稱: {strategy_info['name']}")
        print(f"     描述: {strategy_info['description']}\n")
    
    return True


async def test_strategy_menu():
    """測試 2: 模擬策略選單顯示"""
    print("=" * 70)
    print("測試 2: 策略選單顯示（模擬 /strategy 命令）")
    print("=" * 70)
    
    strategies = registry.list_strategies()
    
    if not strategies:
        print("❌ 失敗：無法顯示策略選單（沒有可用策略）")
        return False
    
    print("\n=== 交易策略選單 ===\n")
    
    for idx, strategy_info in enumerate(strategies, 1):
        print(f"{idx}. {strategy_info['name']}")
        print(f"   {strategy_info['description']}")
        print(f"   指令：/strategy {strategy_info['key']}\n")
    
    print("\n輸入策略名稱或編號查看詳情")
    print(f"範例：/strategy {strategies[0]['key']} 或 /strategy 1")
    
    print("\n✅ 成功：策略選單顯示正常")
    return True


async def test_strategy_key_resolution():
    """測試 3: 測試策略鍵值解析"""
    print("\n" + "=" * 70)
    print("測試 3: 策略鍵值解析")
    print("=" * 70)
    
    strategies = registry.list_strategies()
    
    if not strategies:
        print("❌ 失敗：沒有可用策略進行測試")
        return False
    
    # 測試第一個策略的鍵值
    test_key = strategies[0]['key']
    strategy_class = registry.get(test_key)
    
    if not strategy_class:
        print(f"❌ 失敗：無法通過鍵值 '{test_key}' 取得策略類別")
        return False
    
    print(f"✅ 成功：成功解析鍵值 '{test_key}'")
    print(f"   策略類別: {strategy_class.__name__}")
    
    # 測試實例化
    try:
        strategy_instance = strategy_class()
        print(f"   實例名稱: {strategy_instance.name}")
        print(f"   實例描述: {strategy_instance.description}")
        print("✅ 成功：策略實例化正常")
        return True
    except Exception as e:
        print(f"❌ 失敗：無法實例化策略 - {e}")
        return False


async def test_strategy_details():
    """測試 4: 顯示策略詳細資訊"""
    print("\n" + "=" * 70)
    print("測試 4: 策略詳細資訊（模擬 /strategy farmer 命令）")
    print("=" * 70)
    
    strategies = registry.list_strategies()
    
    if not strategies:
        print("❌ 失敗：沒有可用策略")
        return False
    
    # 取得第一個策略進行測試
    strategy_key = strategies[0]['key']
    strategy_class = registry.get(strategy_key)
    
    if not strategy_class:
        print(f"❌ 失敗：找不到策略 '{strategy_key}'")
        return False
    
    try:
        # 創建策略實例
        strategy = strategy_class()
        config_schema = strategy.get_config_schema()
        
        print(f"\n=== {strategy.name} ===\n")
        print(f"描述：{strategy.description}\n")
        
        print("配置參數：")
        for param_name, param_info in config_schema.items():
            print(f"  • {param_name}: {param_info['description']} (預設: {param_info['default']})")
        
        print(f"\n查看特定股票狀態：/strategy {strategy_key} 2330")
        print(f"執行回測：/strategy {strategy_key} 2330 backtest")
        
        print("\n✅ 成功：策略詳情顯示正常")
        return True
        
    except Exception as e:
        print(f"❌ 失敗：無法取得策略詳情 - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_farmer_strategy_specific():
    """測試 5: 農夫播種術策略特定測試"""
    print("\n" + "=" * 70)
    print("測試 5: 農夫播種術策略專項測試")
    print("=" * 70)
    
    # 嘗試取得農夫播種術策略
    farmer_key = "farmerplanting"
    strategy_class = registry.get(farmer_key)
    
    if not strategy_class:
        print(f"⚠️  警告：找不到鍵值 '{farmer_key}' 的策略")
        
        # 列出所有可用的鍵值
        strategies = registry.list_strategies()
        print(f"   可用的策略鍵值：{[s['key'] for s in strategies]}")
        return False
    
    print(f"✅ 成功：找到農夫播種術策略")
    
    strategy = strategy_class()
    print(f"   策略名稱: {strategy.name}")
    print(f"   核心規則:")
    
    config = strategy.get_config_schema()
    print(f"   - 最大持倉: {config['max_positions']['default']} 份")
    print(f"   - 加碼門檻: {config['add_threshold']['default']} (漲幅 3%)")
    print(f"   - 減碼門檻: {config['reduce_threshold']['default']} (跌幅 3%)")
    print(f"   - 移動停利: {config['trailing_stop']['default']} (回落 20%)")
    
    return True


async def main():
    """執行所有測試"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "策略命令系統測試程式" + " " * 28 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    tests = [
        test_strategy_registration,
        test_strategy_menu,
        test_strategy_key_resolution,
        test_strategy_details,
        test_farmer_strategy_specific,
    ]
    
    results = []
    
    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 測試執行錯誤: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # 測試結果總結
    print("\n" + "=" * 70)
    print("測試結果總結")
    print("=" * 70)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"通過: {passed}/{total}")
    
    if passed == total:
        print("✅ 所有測試通過！")
        return 0
    else:
        print(f"⚠️  有 {total - passed} 個測試失敗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
