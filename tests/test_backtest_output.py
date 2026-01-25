"""測試回測輸出"""
import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pulse.cli.commands.strategy import run_strategy_backtest
from pulse.utils.logger import get_logger
from rich.console import Console

log = get_logger(__name__)


class MockApp:
    """模擬 App 實例"""
    def __init__(self):
        self.console = Console()


async def main():
    """主函數"""
    print("=" * 80)
    print("測試回測輸出")
    print("=" * 80)
    
    app = MockApp()
    
    print("\n執行命令: /strategy farmerplanting 2330 backtest")
    print("-" * 80)
    
    try:
        await run_strategy_backtest(app, "farmerplanting", "2330")
    except Exception as e:
        log.error(f"回測執行錯誤: {e}", exc_info=True)
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
