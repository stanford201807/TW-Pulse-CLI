"""AI client using LiteLLM for multi-provider LLM support."""

from collections.abc import AsyncIterator
from typing import Any

import litellm
from litellm import acompletion

from pulse.ai.prompts import CHAT_SYSTEM_PROMPT
from pulse.core.config import settings
from pulse.utils.logger import get_logger

# Suppress LiteLLM verbose logging
litellm.suppress_debug_info = True

log = get_logger(__name__)


class AIClient:
    """AI client for stock analysis using LiteLLM (supports multiple providers)."""

    def __init__(
        self,
        model: str | None = None,
    ):
        """
        Initialize AI client.

        Args:
            model: Model to use in LiteLLM format (e.g., "anthropic/claude-sonnet-4-20250514")
                   API keys are read from environment variables:
                   - ANTHROPIC_API_KEY for Anthropic
                   - OPENAI_API_KEY for OpenAI
                   - GEMINI_API_KEY for Google
                   - GROQ_API_KEY for Groq
        """
        self.model = model or settings.ai.default_model
        self.temperature = settings.ai.temperature
        self.max_tokens = settings.ai.max_tokens
        self.timeout = settings.ai.timeout

        self._conversation_history: list[dict[str, str]] = []

    def set_model(self, model: str) -> None:
        """
        Set the AI model to use.

        Args:
            model: Model ID
        """
        if model in settings.ai.available_models:
            self.model = model
            log.info(f"Model switched to: {settings.get_model_display_name(model)}")
        else:
            log.warning(f"Unknown model: {model}")

    def get_current_model(self) -> dict[str, str]:
        """Get current model info."""
        return {
            "id": self.model,
            "name": settings.get_model_display_name(self.model),
        }

    def list_models(self) -> list[dict[str, str]]:
        """List all available models."""
        return settings.list_models()

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history = []

    async def chat(
        self,
        message: str,
        system_prompt: str | None = None,
        use_history: bool = True,
    ) -> str:
        """
        Send a chat message and get a response.

        Args:
            message: User message
            system_prompt: Optional system prompt
            use_history: Whether to include conversation history

        Returns:
            AI response text
        """
        messages = []

        # Add system prompt
        prompt = system_prompt or CHAT_SYSTEM_PROMPT
        messages.append({"role": "system", "content": prompt})

        # Add history if enabled
        if use_history:
            messages.extend(self._conversation_history)

        # Prepend identity reminder to user message for first message or greetings
        user_msg = message
        greetings = ["嗨", "你好", "哈囉", "hello", "hi", "hey"]
        is_greeting = message.lower().strip() in greetings

        if not self._conversation_history or is_greeting:
            user_msg = (
                f"[指示: 以 PULSE 台灣股市助理的身份回答。不是程式設計助理。]\n\nUser: {message}"
            )

        # Add current message
        messages.append({"role": "user", "content": user_msg})

        try:
            response = await acompletion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )

            assistant_message = response.choices[0].message.content or ""

            # Update history
            if use_history:
                self._conversation_history.append({"role": "user", "content": message})
                self._conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )

            return assistant_message

        except Exception as e:
            log.error(f"AI request failed: {e}")
            raise

    async def chat_stream(
        self,
        message: str,
        system_prompt: str | None = None,
        use_history: bool = True,
    ) -> AsyncIterator[str]:
        """
        Send a chat message and stream the response.

        Args:
            message: User message
            system_prompt: Optional system prompt
            use_history: Whether to include conversation history

        Yields:
            Response text chunks
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if use_history:
            messages.extend(self._conversation_history)

        messages.append({"role": "user", "content": message})

        try:
            response = await acompletion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                stream=True,
            )

            full_response = ""

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Update history after streaming complete
            if use_history:
                self._conversation_history.append({"role": "user", "content": message})
                self._conversation_history.append({"role": "assistant", "content": full_response})

        except Exception as e:
            log.error(f"AI stream request failed: {e}")
            raise

    async def analyze_stock(
        self,
        ticker: str,
        data: dict[str, Any],
        analysis_type: str = "comprehensive",
    ) -> str:
        """
        Analyze a stock using AI.

        Args:
            ticker: Stock ticker
            data: Stock data dictionary
            analysis_type: Type of analysis (comprehensive, technical, fundamental, broker)

        Returns:
            AI analysis response
        """
        from pulse.ai.prompts import StockAnalysisPrompts

        prompts = StockAnalysisPrompts()

        if analysis_type == "technical":
            system_prompt = prompts.get_technical_prompt()
        elif analysis_type == "fundamental":
            system_prompt = prompts.get_fundamental_prompt()
        elif analysis_type == "broker":
            system_prompt = prompts.get_broker_flow_prompt()
        else:
            system_prompt = prompts.get_comprehensive_prompt()

        # Format data as message
        user_message = prompts.format_analysis_request(ticker, data)

        return await self.chat(
            message=user_message,
            system_prompt=system_prompt,
            use_history=False,
        )

    async def get_recommendation(
        self,
        ticker: str,
        analysis_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get AI recommendation for a stock.

        Args:
            ticker: Stock ticker
            analysis_result: Analysis data

        Returns:
            Recommendation dictionary
        """
        from pulse.ai.prompts import StockAnalysisPrompts

        prompts = StockAnalysisPrompts()
        system_prompt = prompts.get_recommendation_prompt()

        import json

        user_message = f"""
根據以下數據為股票 {ticker} 提供建議:

{json.dumps(analysis_result, indent=2, default=str)}

以 JSON 格式回應，結構如下:
{{
    "signal": "Strong Buy/Buy/Neutral/Sell/Strong Sell",
    "confidence": 0-100,
    "target_price": number,
    "stop_loss": number,
    "risk_level": "Low/Medium/High",
    "holding_period": "Short/Medium/Long",
    "key_reasons": ["reason1", "reason2", ...],
    "risks": ["risk1", "risk2", ...]
}}
"""

        response = await self.chat(
            message=user_message,
            system_prompt=system_prompt,
            use_history=False,
        )

        # Try to parse JSON from response
        try:
            # Find JSON in response
            import re

            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            log.warning(f"Failed to parse recommendation JSON: {e}")

        return {"raw_response": response}
