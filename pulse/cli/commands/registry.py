"""Command registry and handler."""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pulse.cli.app import PulseApp

from pulse.utils.logger import get_logger

log = get_logger(__name__)


class Command:
    """Represents a slash command."""

    def __init__(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        usage: str = "",
        aliases: list[str] | None = None,
    ):
        self.name = name
        self.handler = handler
        self.description = description
        self.usage = usage or f"/{name}"
        self.aliases = aliases or []


class CommandRegistry:
    """Registry for slash commands."""

    def __init__(self, app: "PulseApp"):
        self.app = app
        self._commands: dict[str, Command] = {}
        self._register_builtin_commands()

    def register(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        usage: str = "",
        aliases: list[str] | None = None,
    ) -> None:
        """Register a command."""
        cmd = Command(name, handler, description, usage, aliases)
        self._commands[name.lower()] = cmd

        for alias in aliases or []:
            self._commands[alias.lower()] = cmd

    def get(self, name: str) -> Command | None:
        """Get a command by name."""
        return self._commands.get(name.lower())

    def list_commands(self) -> list[Command]:
        """List all unique commands (excluding aliases)."""
        seen = set()
        commands = []

        for cmd in self._commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                commands.append(cmd)

        return sorted(commands, key=lambda c: c.name)

    async def execute(self, command_str: str) -> str | None:
        """Execute a command string."""
        parts = command_str.strip().split(maxsplit=1)
        cmd_name = parts[0].lstrip("/").lower()
        args = parts[1] if len(parts) > 1 else ""

        cmd = self.get(cmd_name)

        if not cmd:
            return f"Unknown command: /{cmd_name}. Type /help for available commands."

        try:
            result = await cmd.handler(args)
            return result
        except Exception as e:
            log.error(f"Command {cmd_name} failed: {e}")
            raise

    def _register_builtin_commands(self) -> None:
        """Register built-in commands."""

        self.register(
            "help",
            self._cmd_help,
            "Show available commands",
            "/help [command]",
            aliases=["h", "?"],
        )

        self.register(
            "models",
            self._cmd_models,
            "List or switch AI models",
            "/models [model_id]",
            aliases=["model", "m"],
        )

        self.register(
            "analyze",
            self._cmd_analyze,
            "Analyze a stock (分析股票)",
            "/analyze <TICKER>",
            aliases=["a", "stock"],
        )

        self.register(
            "sapta",
            self._cmd_sapta,
            "SAPTA PRE-MARKUP detection engine",
            "/sapta <TICKER> | /sapta scan [universe]",
            aliases=["premarkup", "markup"],
        )

        self.register(
            "sapta-retrain",
            self._cmd_sapta_retrain,
            "Retrain SAPTA ML model",
            "/sapta-retrain [--stocks=N] [--target-gain=N] [--walk-forward]",
            aliases=["saptaretrain", "retrain-sapta"],
        )

        self.register(
            "technical",
            self._cmd_technical,
            "Technical analysis (技術分析)",
            "/technical <TICKER>",
            aliases=["tech", "ta"],
        )

        self.register(
            "fundamental",
            self._cmd_fundamental,
            "Fundamental analysis (基本面分析)",
            "/fundamental <TICKER>",
            aliases=["fund", "fa"],
        )

        self.register(
            "institutional",
            self._cmd_broker,
            "Institutional investor flow (法人動向)",
            "/institutional <TICKER>",
            aliases=["inst", "flow", "broker"],
        )

        self.register(
            "screen",
            self._cmd_screen,
            "Stock screener (股票篩選)",
            "/screen <strategy> [universe]",
            aliases=["scan", "filter"],
        )

        self.register(
            "smart-money",
            self._cmd_smart_money,
            "Smart Money Screener (主力足跡選股)",
            "/smart-money [--min-score=N] [--limit=N]",
            aliases=["tvb", "主力", "smartmoney"],
        )

        self.register(
            "sector",
            self._cmd_sector,
            "Sector analysis (產業分析)",
            "/sector [sector_name]",
            aliases=["industry"],
        )

        self.register(
            "compare",
            self._cmd_compare,
            "Compare stocks (股票比較)",
            "/compare <TICKER1> <TICKER2> [...]",
            aliases=["cmp", "vs"],
        )

        self.register(
            "chart",
            self._cmd_chart,
            "Generate stock chart (K線圖)",
            "/chart <TICKER> [period]",
            aliases=["k", "kline"],
        )

        self.register(
            "forecast",
            self._cmd_forecast,
            "Price forecast (價格預測)",
            "/forecast <TICKER> [days]",
            aliases=["pred", "predict"],
        )

        self.register(
            "taiex",
            self._cmd_taiex,
            "Taiwan index overview (大盤指數)",
            "/taiex [TPEX]",
            aliases=["twii", "index"],
        )

        self.register(
            "plan",
            self._cmd_plan,
            "Generate trading plan (交易計劃)",
            "/plan <TICKER>",
            aliases=["trade"],
        )

        self.register(
            "plan",
            self._cmd_plan,
            "Generate trading plan (交易計劃)",
            "/plan <TICKER>",
            aliases=["trade"],
        )

        self.register(
            "strategy",
            self._cmd_strategy,
            "交易策略系統",
            "/strategy [strategy_name] [ticker] [backtest]",
            aliases=["strategies", "策略"],
        )

        self.register(
            "clear",
            self._cmd_clear,
            "Clear chat history",
            "/clear",
            aliases=["cls"],
        )

        self.register(
            "exit",
            self._cmd_exit,
            "Exit the application (退出程式)",
            "/exit",
            aliases=["quit", "q"],
        )

    async def _cmd_help(self, args: str) -> str:
        """Help command handler."""
        if args:
            cmd = self.get(args.strip())
            if cmd:
                aliases_str = ", ".join(f"/{a}" for a in cmd.aliases) if cmd.aliases else "無"
                return f"""/{cmd.name}

說明: {cmd.description}
用法: {cmd.usage}
別名: {aliases_str}
"""
            else:
                return f"未知的命令: /{args}"

        lines = ["可用命令\n"]

        for cmd in self.list_commands():
            aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"  /{cmd.name}{aliases} - {cmd.description}")

        lines.append("\n輸入 /help <命令> 查看詳細說明")

        return "\n".join(lines)

    async def _cmd_models(self, args: str) -> str | None:
        """Models command handler."""
        if args:
            model_id = args.strip()
            self.app.ai_client.set_model(model_id)

            model_info = self.app.ai_client.get_current_model()
            return f"已切換至模型: {model_info['name']}"

        # No args - show modal
        self.app.show_models_modal()
        return None  # Don't output anything to chat

    async def _cmd_analyze(self, args: str) -> str:
        """Analyze command handler."""
        from pulse.cli.commands.analysis import analyze_command

        return await analyze_command(self.app, args)

    async def _cmd_broker(self, args: str) -> str:
        """Broker flow command handler."""
        from pulse.cli.commands.advanced import broker_command

        return await broker_command(self.app, args)

    async def _cmd_technical(self, args: str) -> str:
        """Technical analysis command handler."""
        from pulse.cli.commands.analysis import technical_command

        return await technical_command(self.app, args)

    async def _cmd_fundamental(self, args: str) -> str:
        """Fundamental analysis command handler."""
        from pulse.cli.commands.analysis import fundamental_command

        return await fundamental_command(self.app, args)

    async def _cmd_screen(self, args: str) -> str:
        """Screen stocks command handler."""
        from pulse.cli.commands.screening import screen_command

        return await screen_command(self.app, args)

    async def _cmd_smart_money(self, args: str) -> str:
        """Smart Money Screener command handler."""
        from pulse.cli.commands.screening import smart_money_command

        return await smart_money_command(self.app, args)

    async def _cmd_sector(self, args: str) -> str:
        """Sector analysis command handler."""
        from pulse.cli.commands.advanced import sector_command

        return await sector_command(self.app, args)

    async def _cmd_compare(self, args: str) -> str:
        """Compare stocks command handler."""
        from pulse.cli.commands.screening import compare_command

        return await compare_command(self.app, args)

    async def _cmd_chart(self, args: str) -> str:
        """Chart command handler."""
        from pulse.cli.commands.charts import chart_command

        return await chart_command(self.app, args)

    async def _cmd_forecast(self, args: str) -> str:
        """Forecast command handler."""
        from pulse.cli.commands.charts import forecast_command

        return await forecast_command(self.app, args)

    async def _cmd_clear(self, args: str) -> str | None:
        """Clear chat history."""
        self.app.action_clear()
        return None

    async def _cmd_exit(self, args: str) -> str | None:
        """Exit the application."""
        self.app.exit()
        return None

    async def _cmd_taiex(self, args: str) -> str:
        """Show TAIEX or other Taiwan index status."""
        from pulse.cli.commands.charts import taiex_command

        return await taiex_command(self.app, args)

    async def _cmd_plan(self, args: str) -> str:
        """Trading plan command handler."""
        from pulse.cli.commands.advanced import plan_command

        return await plan_command(self.app, args)

    async def _cmd_sapta(self, args: str) -> str:
        """SAPTA PRE-MARKUP detection command handler."""
        from pulse.cli.commands.advanced import sapta_command

        return await sapta_command(self.app, args)

    async def _cmd_strategy(self, args: str) -> str:
        """Strategy command handler."""
        from pulse.cli.commands.strategy import handle_strategy_command

        return await handle_strategy_command(self.app, args)

    async def _cmd_sapta_retrain(self, args: str) -> str:
        """SAPTA Model Retraining command handler."""
        from pulse.cli.commands.advanced import sapta_retrain_command

        return await sapta_retrain_command(self.app, args)
