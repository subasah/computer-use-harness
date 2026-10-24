"""
Multi-Provider LLM Abstraction Layer (Anthropic, OpenAI, Gemini, and Mock).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolCallRequest:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    text: Optional[str] = None
    tool_calls: List[ToolCallRequest] = field(default_factory=list)
    prompt_tokens: int = 150
    completion_tokens: int = 40
    finish_reason: str = "tool_calls"


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> LLMResponse:
        pass


class MockProvider(BaseLLMProvider):
    """
    Deterministic scripted mock provider for unit tests, offline demos,
    and CI/CD pipelines without external API dependencies.
    """

    def __init__(self, script: Optional[List[LLMResponse]] = None):
        self.script: List[LLMResponse] = script or []
        self.step_idx = 0
        self.dynamic_handler: Optional[Callable[[List[Dict[str, Any]]], LLMResponse]] = None

    def set_script(self, script: List[LLMResponse]) -> None:
        self.script = script
        self.step_idx = 0

    def set_dynamic_handler(self, handler: Callable[[List[Dict[str, Any]]], LLMResponse]) -> None:
        self.dynamic_handler = handler

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> LLMResponse:
        if self.dynamic_handler:
            return self.dynamic_handler(messages)

        if self.step_idx < len(self.script):
            resp = self.script[self.step_idx]
            self.step_idx += 1
            return resp

        # Default fallback response if script exhausted
        return LLMResponse(
            text="I have completed all required operations.",
            tool_calls=[],
            finish_reason="stop",
        )


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Computer Use Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-7-sonnet-20250219"):
        self.api_key = api_key
        self.model = model

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> LLMResponse:
        try:
            import anthropic  # type: ignore

            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=messages,
                tools=tools,
            )

            tool_calls: List[ToolCallRequest] = []
            text_blocks: List[str] = []

            for block in response.content:
                if block.type == "text":
                    text_blocks.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(
                        ToolCallRequest(
                            id=block.id,
                            name=block.name,
                            arguments=block.input if isinstance(block.input, dict) else {},
                        )
                    )

            prompt_tokens = response.usage.input_tokens if hasattr(response, "usage") else 100
            completion_tokens = response.usage.output_tokens if hasattr(response, "usage") else 50

            return LLMResponse(
                text="\n".join(text_blocks) if text_blocks else None,
                tool_calls=tool_calls,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason="tool_calls" if tool_calls else "stop",
            )
        except ImportError:
            raise RuntimeError("anthropic package is not installed. Run `pip install anthropic`.") from None


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Vision & Function Calling Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> LLMResponse:
        try:
            from openai import AsyncOpenAI  # type: ignore

            client = AsyncOpenAI(api_key=self.api_key)
            formatted_messages = [{"role": "system", "content": system_prompt}, *messages]

            # Convert tools to OpenAI format if needed
            openai_tools = []
            for t in tools:
                if "type" in t and t["type"] == "function":
                    openai_tools.append(t)
                else:
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": t.get("name"),
                            "description": t.get("description", ""),
                            "parameters": t.get("input_schema", {}),
                        },
                    })

            response = await client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                tools=openai_tools if openai_tools else None,
            )

            choice = response.choices[0]
            msg = choice.message

            tool_calls: List[ToolCallRequest] = []
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    tool_calls.append(ToolCallRequest(id=tc.id, name=tc.function.name, arguments=args))

            prompt_tokens = response.usage.prompt_tokens if response.usage else 100
            completion_tokens = response.usage.completion_tokens if response.usage else 50

            return LLMResponse(
                text=msg.content,
                tool_calls=tool_calls,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason="tool_calls" if tool_calls else "stop",
            )
        except ImportError:
            raise RuntimeError("openai package is not installed. Run `pip install openai`.") from None
