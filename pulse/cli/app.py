"""Pulse CLI - Main TUI Application."""


from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Markdown, OptionList, Static
from textual.widgets.option_list import Option

from pulse.ai.client import AIClient
from pulse.cli.commands.registry import CommandRegistry
from pulse.core.smart_agent import SmartAgent
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class CommandPalette(OptionList):
    """Command dropdown that appears when typing /."""

    DEFAULT_CSS = """
    CommandPalette {
        layer: overlay;
        dock: bottom;
        height: auto;
        max-height: 12;
        margin: 0 2 4 2;
        background: #161b22;
        border: solid #30363d;
        display: none;
    }
    
    CommandPalette:focus {
        border: solid #58a6ff;
    }
    
    CommandPalette > .option-list--option {
        padding: 0 1;
    }
    
    CommandPalette > .option-list--option-highlighted {
        background: #21262d;
        color: #58a6ff;
    }
    """

    class Selected(Message):
        """Command was selected."""
        def __init__(self, command: str) -> None:
            super().__init__()
            self.command = command


class ModelsModal(ModalScreen):
    """Modal for selecting AI models with arrow key navigation."""

    DEFAULT_CSS = """
    ModelsModal {
        align: center middle;
    }
    
    ModelsModal > Vertical {
        width: 60;
        height: auto;
        max-height: 20;
        background: #161b22;
        border: solid #30363d;
        padding: 1 2;
    }
    
    ModelsModal .modal-title {
        text-align: center;
        color: #58a6ff;
        text-style: bold;
        margin-bottom: 1;
    }
    
    ModelsModal OptionList {
        height: auto;
        max-height: 12;
        background: #0d1117;
        border: none;
    }
    
    ModelsModal OptionList > .option-list--option {
        padding: 0 1;
    }
    
    ModelsModal OptionList > .option-list--option-highlighted {
        background: #21262d;
        color: #58a6ff;
    }
    
    ModelsModal .modal-hint {
        text-align: center;
        color: #484f58;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, models: list, current: str):
        super().__init__()
        self.models = models
        self.current = current

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Select Model", classes="modal-title")
            option_list = OptionList(id="model-list")
            for model in self.models:
                marker = "> " if model["id"] == self.current else "  "
                label = f"{marker}{model['name']}"
                option_list.add_option(Option(label, id=model["id"]))
            yield option_list
            yield Static("Enter: Select | Esc: Cancel", classes="modal-hint")

    def on_mount(self) -> None:
        self.query_one("#model-list", OptionList).focus()

    @on(OptionList.OptionSelected, "#model-list")
    def on_model_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:
            self.dismiss(event.option.id)

    def action_cancel(self) -> None:
        self.dismiss(None)


class PulseApp(App):
    """Pulse CLI - AI Stock Analysis."""

    TITLE = "Pulse"

    CSS = """
    Screen {
        background: #0d1117;
        layers: base overlay;
    }
    
    #chat {
        layer: base;
        height: 1fr;
        padding: 1 2;
        scrollbar-size: 1 1;
        scrollbar-color: #30363d;
        overflow-y: auto;
        overflow-x: hidden;
    }
    
    .user-msg {
        color: #58a6ff;
        margin: 1 0 0 0;
        padding: 0 0 0 2;
        border-left: thick #58a6ff;
    }
    
    .ai-msg {
        color: #c9d1d9;
        margin: 0 0 1 0;
    }
    
    .ai-msg Markdown {
        margin: 0;
        padding: 0;
    }
    
    .ai-msg MarkdownH1,
    .ai-msg MarkdownH2,
    .ai-msg MarkdownH3 {
        color: #58a6ff;
        margin: 1 0 0 0;
        padding: 0;
        border: none;
        background: transparent;
    }
    
    .ai-msg MarkdownBulletList,
    .ai-msg MarkdownOrderedList {
        margin: 0;
        padding: 0 0 0 2;
    }
    
    .thinking {
        color: #484f58;
        text-style: italic;
        padding: 0 0 0 2;
        border-left: thick #484f58;
    }
    
    .welcome {
        color: #484f58;
    }
    
    .chart-msg {
        color: #8b949e;
        margin: 0 0 1 0;
        padding: 0;
    }
    
    #input-area {
        dock: bottom;
        height: auto;
        padding: 0 2 1 2;
    }
    
    #input {
        height: 3;
        background: #161b22;
        border: solid #30363d;
        padding: 0 1;
    }
    
    #input:focus {
        border: solid #58a6ff;
    }
    
    #status {
        height: 1;
        background: #161b22;
        color: #484f58;
        padding: 0 1;
        text-align: right;
    }
    
    Footer {
        background: #161b22;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("escape", "close_palette", "Close", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.ai_client = AIClient()
        self.command_registry = CommandRegistry(self)
        self.smart_agent = SmartAgent()
        self._palette_visible = False

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="chat")
        yield CommandPalette(id="palette")
        with Vertical(id="input-area"):
            yield Input(placeholder="> Message Pulse...", id="input")
            yield Static(f"pulse | {self.ai_client.model}", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#input", Input).focus()
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(Static("Pulse - Type /help for commands", classes="welcome"))
        self._populate_palette()

    def _populate_palette(self, filter_text: str = "") -> None:
        """Populate command palette with commands."""
        palette = self.query_one("#palette", CommandPalette)
        palette.clear_options()

        for cmd in self.command_registry.list_commands():
            cmd_text = f"/{cmd.name}"
            if filter_text and not cmd_text.startswith(filter_text):
                continue

            aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            label = f"/{cmd.name}{aliases} - {cmd.description}"
            palette.add_option(Option(label, id=cmd.name))

    def _show_palette(self) -> None:
        """Show command palette."""
        if not self._palette_visible:
            palette = self.query_one("#palette", CommandPalette)
            palette.styles.display = "block"
            self._palette_visible = True

    def _hide_palette(self) -> None:
        """Hide command palette."""
        if self._palette_visible:
            palette = self.query_one("#palette", CommandPalette)
            palette.styles.display = "none"
            self._palette_visible = False

    def action_close_palette(self) -> None:
        """Close command palette."""
        self._hide_palette()
        self.query_one("#input", Input).focus()

    @on(Input.Changed, "#input")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes to show/hide palette."""
        value = event.value

        if value.startswith("/"):
            self._populate_palette(value)
            self._show_palette()
        else:
            self._hide_palette()

    @on(OptionList.OptionSelected, "#palette")
    def on_palette_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle command selection from palette."""
        if event.option.id:
            cmd = self.command_registry.get(event.option.id)
            if cmd:
                input_widget = self.query_one("#input", Input)
                # Set input to command, user can add args
                input_widget.value = f"/{cmd.name} "
                input_widget.focus()
                self._hide_palette()

    def _add_user(self, text: str) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(Static(text, classes="user-msg"))
        # Use call_later to ensure scroll happens after mount
        self.call_later(self._scroll_chat_end)

    def _add_response(self, text: str) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(Markdown(text, classes="ai-msg"))
        self._update_status()
        # Use call_later to ensure scroll happens after mount
        self.call_later(self._scroll_chat_end)

    def _add_chart(self, chart_text: str) -> None:
        """Add chart to chat as plain Static widget."""
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(Static(chart_text, classes="chart-msg"))
        self.call_later(self._scroll_chat_end)

    def _update_status(self) -> None:
        """Update status bar with current model."""
        self.query_one("#status", Static).update(f"pulse | {self.ai_client.model}")

    def show_models_modal(self) -> None:
        """Show modal for model selection."""
        models = self.ai_client.list_models()
        current = self.ai_client.model

        def on_select(model_id: str | None) -> None:
            if model_id:
                self.ai_client.set_model(model_id)
                model_info = self.ai_client.get_current_model()
                self._add_response(f"Switched to: {model_info['name']}")
                self._update_status()
            self.query_one("#input", Input).focus()

        self.push_screen(ModelsModal(models, current), on_select)

    def _add_thinking(self) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(Static("thinking...", classes="thinking", id="thinking"))
        self.call_later(self._scroll_chat_end)

    def _remove_thinking(self) -> None:
        try:
            thinking = self.query_one("#thinking")
            thinking.remove()
        except Exception:
            pass

    def _refocus_input(self) -> None:
        """Refocus input widget."""
        try:
            self.query_one("#input", Input).focus()
        except Exception:
            pass

    def _scroll_chat_end(self) -> None:
        """Scroll chat to end."""
        try:
            chat = self.query_one("#chat", VerticalScroll)
            chat.scroll_end(animate=False)
        except Exception:
            pass

    @on(Input.Submitted, "#input")
    def on_submit(self, event: Input.Submitted) -> None:
        msg = event.value.strip()
        if not msg:
            return

        # Clear input immediately for responsiveness
        event.input.value = ""
        self._hide_palette()

        # Show user message and thinking immediately (before any processing)
        self._add_user(msg)
        self._add_thinking()

        if msg.startswith("/"):
            # Run command in background
            self._run_command(msg)
        else:
            # Run chat in background
            self._handle_chat(msg)

    @work(exclusive=True)
    async def _run_command(self, cmd: str) -> None:
        """Run command in background."""
        try:
            result = await self.command_registry.execute(cmd)
            self._remove_thinking()
            if result:
                self._add_response(result)
        except Exception as e:
            self._remove_thinking()
            self._add_response(f"Error: {e}")
        finally:
            self._refocus_input()

    @work(exclusive=True)
    async def _handle_chat(self, msg: str) -> None:
        """
        Handle chat using SmartAgent - true agentic flow.
        
        Flow:
        1. SmartAgent parses intent & extracts tickers
        2. SmartAgent fetches REAL data from yfinance
        3. SmartAgent builds context with real data
        4. AI analyzes with full context
        5. Response shown to user (chart saved as PNG file)
        """
        try:
            # Use SmartAgent for agentic flow
            result = await self.smart_agent.run(msg)
            self._remove_thinking()
            self._add_response(result.message)

        except Exception as e:
            self._remove_thinking()
            log.error(f"Chat error: {e}")
            self._add_response(f"Error: {e}")
        finally:
            # Always refocus input after response
            self._refocus_input()

    def action_clear(self) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        chat.remove_children()
        self.ai_client.clear_history()
        chat.mount(Static("Pulse - Type /help for commands", classes="welcome"))

    def action_quit(self) -> None:
        self.exit()


def main():
    app = PulseApp()
    app.run()


if __name__ == "__main__":
    main()
