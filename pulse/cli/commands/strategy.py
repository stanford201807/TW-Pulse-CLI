"""策略相關 CLI 命令處理。"""

import os
from pulse.cli.commands.registry import CommandRegistry
from pulse.core.strategies import registry as strategy_registry
from pulse.utils.logger import get_logger

log = get_logger(__name__)


async def handle_strategy_command(app, args: str) -> str:
    """處理 /strategy 命令。

    支援的用法：
    - /strategy           # 顯示策略選單
    - /strategy <name>    # 顯示策略詳情
    - /strategy <name> <ticker>  # 查看策略在特定股票的狀態
    - /strategy <name> <ticker> backtest  # 執行回測

    Args:
        app: PulseApp 實例
        args: 命令參數
        
    Returns:
        格式化的結果字符串
    """
    if not args or args.strip() == "":
        # 顯示策略選單
        return await show_strategy_menu(app)

    parts = args.strip().split()

    if len(parts) == 1:
        # /strategy <name> - 顯示策略詳情
        strategy_name = parts[0]
        return await show_strategy_details(app, strategy_name)
    elif len(parts) == 2:
        # /strategy <name> <ticker> - 查看策略狀態
        strategy_name, ticker = parts
        return await show_strategy_status(app, strategy_name, ticker)
    elif len(parts) == 3 and parts[2].lower() == "backtest":
        # /strategy <name> <ticker> backtest - 執行回測
        strategy_name, ticker = parts[0], parts[1]
        return await run_strategy_backtest(app, strategy_name, ticker)
    else:
        return "⚠️ 用法：`/strategy [strategy_name] [ticker] [backtest]`"



async def show_strategy_menu(app) -> str:
    """顯示策略選單。
    
    Returns:
        格式化的策略選單字符串
    """
    strategies = strategy_registry.list_strategies()

    if not strategies:
        return "⚠️ 目前沒有可用的策略"

    lines = ["\n## 交易策略選單\n"]

    for idx, strategy_info in enumerate(strategies, 1):
        lines.append(
            f"**{idx}. {strategy_info['name']}**\n"
            f"   {strategy_info['description']}\n"
            f"   指令：`/strategy {strategy_info['key']}`\n"
        )

    lines.append(
        "\n---\n*輸入策略名稱或編號查看詳情*\n\n"
        "範例：`/strategy farmerplanting` 或 `/strategy 1`"
    )
    
    return "".join(lines)




async def show_strategy_details(app, strategy_name: str) -> str:
    """顯示策略詳細資訊。

    Args:
        app: PulseApp 實例
        strategy_name: 策略名稱或編號
        
    Returns:
        格式化的策略詳情字符串
    """
    # 嘗試將策略名稱轉換為索引
    strategies = strategy_registry.list_strategies()

    try:
        idx = int(strategy_name) - 1
        if 0 <= idx < len(strategies):
            strategy_key = strategies[idx]["key"]
        else:
            return f"❌ 無效的策略編號：{strategy_name}"
    except ValueError:
        strategy_key = strategy_name.lower()

    strategy_class = strategy_registry.get(strategy_key)

    if not strategy_class:
        return (
            f"❌ 找不到策略：{strategy_name}\n\n"
            "*使用 `/strategy` 查看可用策略*"
        )

    # 創建策略實例以取得配置結構
    strategy = strategy_class()
    config_schema = strategy.get_config_schema()

    lines = [f"\n## {strategy.name}\n"]
    lines.append(f"**描述**：{strategy.description}\n")
    
    lines.append("\n### 配置參數\n\n")
    for param_name, param_info in config_schema.items():
        lines.append(
            f"- **{param_name}**: {param_info['description']} "
            f"*(預設: {param_info['default']})*\n"
        )

    lines.append(
        f"\n---\n*查看特定股票狀態*：`/strategy {strategy_key} 2330`\n\n"
        f"*執行回測*：`/strategy {strategy_key} 2330 backtest`"
    )
    
    return "".join(lines)




async def show_strategy_status(app, strategy_name: str, ticker: str) -> str:
    """顯示策略在特定股票的狀態。

    Args:
        app: PulseApp 實例
        strategy_name: 策略名稱
        ticker: 股票代碼
        
    Returns:
        格式化的策略狀態字符串
    """
    strategy_class = strategy_registry.get(strategy_name.lower())

    if not strategy_class:
        return f"❌ 找不到策略：{strategy_name}"

    # 創建策略實例
    strategy = strategy_class()

    # 初始化策略（使用預設配置）
    initial_cash = 1_000_000  # 預設 100 萬
    config = {}  # 使用預設配置

    try:
        await strategy.initialize(ticker, initial_cash, config)

        # 顯示策略狀態
        status = strategy.get_status()
        
        return (
            f"{status}\n\n"
            f"*執行回測*：`/strategy {strategy_name} {ticker} backtest`"
        )

    except Exception as e:
        log.error(f"Error initializing strategy: {e}")
        return f"❌ 初始化策略時發生錯誤：{e}"




async def run_strategy_backtest(app, strategy_name: str, ticker: str) -> str:
    """執行策略回測。

    Args:
        app: PulseApp 實例
        strategy_name: 策略名稱
        ticker: 股票代碼
        
    Returns:
        格式化的回測結果字符串
    """
    strategy_class = strategy_registry.get(strategy_name.lower())

    if not strategy_class:
        return f"❌ 找不到策略：{strategy_name}"

    lines = [
        "⏳ **正在執行回測...**\n\n",
        f"- **策略**：{strategy_name}\n",
        f"- **股票**：{ticker}\n\n"
    ]

    try:
        from pulse.core.backtest import BacktestEngine

        # 創建策略實例
        strategy = strategy_class()

        # 使用預設配置初始化（可從 app.config 讀取）
        initial_cash = 1_000_000  # 100 萬
        
        # 創建回測引擎
        engine = BacktestEngine(
            strategy=strategy,
            ticker=ticker,
            initial_cash=initial_cash,
        )

        # 執行回測
        log.info(f"Starting backtest engine for {ticker}...")
        report = await engine.run()
        log.info("Backtest completed successfully.")

        # 自動保存報表（傳遞 position_manager 以支援動態資金詳細表格）
        log.info("Saving report to markdown...")
        position_manager = engine.strategy.state if hasattr(engine, 'strategy') else None
        # 取得 position_manager（需要從 engine 內部存取）
        # 使用一個簡單的方式：從 engine 重新執行時獲得 position_manager
        # 或者修改 engine.run() 返回 (report, position_manager)
        # 這裡我們直接修改 engine 來暫存 position_manager
        pm = getattr(engine, '_last_position_manager', None)
        report_path = report.save_to_markdown(position_manager=pm)
        log.info(f"Report saved to absolute path: {os.path.abspath(report_path)}")

        # 顯示報告（預設顯示所有交易明細）
        lines.append(report.format())
        
        # 增加存檔提醒
        save_msg = f"\n\n✅ **報表已儲存至**：`report/{os.path.basename(report_path)}`"
        lines.append(save_msg)
        log.info(f"Returning result with save message: {save_msg}")

        return "".join(lines)

    except Exception as e:
        log.error(f"Backtest error: {e}", exc_info=True)
        return f"❌ 回測執行錯誤：{e}"




def register_strategy_commands(registry: CommandRegistry) -> None:
    """註冊策略相關命令。

    Args:
        registry: 命令註冊表
    """
    registry.register(
        name="strategy",
        handler=handle_strategy_command,
        description="交易策略系統",
        usage="/strategy [strategy_name] [ticker] [backtest]",
        aliases=["strategies", "策略"],
    )
