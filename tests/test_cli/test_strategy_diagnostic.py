"""診斷測試：確認 /strategy 命令運作情況

此腳本模擬 pulse app 的行為，並測試策略命令處理器
"""
import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from pulse.core.strategies import registry


class MockApp:
    """模擬 PulseApp"""
    
    def __init__(self):
        self.console = Console()


async def test_strategy_command():
    """測試策略命令處理"""
    print("=" * 70)
    print("診斷測試：/strategy 命令輸出測試")
    print("=" * 70)
    print()
    
    # 創建模擬 app
    app = MockApp()
    
    # 導入策略命令處理器
    from pulse.cli.commands.strategy import handle_strategy_command
    
    print("執行 /strategy 命令（無參數）...")
    print("-" * 70)
    
    try:
        # 執行命令
        await handle_strategy_command(app, "")
        
        print("-" * 70)
        print("\n✅ 命令執行成功")
        
    except Exception as e:
        print(f"\n❌ 命令執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("執行 /strategy farmerplanting 命令...")
    print("=" * 70)
    print()
    
    try:
        await handle_strategy_command(app, "farmerplanting")
        print("\n✅ 命令執行成功")
        
    except Exception as e:
        print(f"\n❌ 命令執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_strategy_command())
    sys.exit(0 if result else 1)
