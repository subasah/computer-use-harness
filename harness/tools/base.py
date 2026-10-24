"""
Base abstractions and schemas for tools in the harness.
"""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    """Outcome of a tool invocation."""
    content: str
    image_bytes: Optional[bytes] = None
    is_error: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_anthropic_content(self, tool_use_id: str) -> List[Dict[str, Any]]:
        """Format as Anthropic tool_result block."""
        blocks: List[Dict[str, Any]] = []
        if self.image_bytes:
            b64_img = base64.b64encode(self.image_bytes).decode("utf-8")
            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": b64_img,
                },
            })
        if self.content:
            blocks.append({"type": "text", "text": self.content})
        elif not self.image_bytes:
            blocks.append({"type": "text", "text": "Success"})

        return [{
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "is_error": self.is_error,
            "content": blocks,
        }]

    def to_openai_message(self, tool_call_id: str) -> Dict[str, Any]:
        """Format as OpenAI tool message."""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": self.content or ("Success" if not self.is_error else "Error"),
        }


class BaseTool(ABC):
    """Abstract base class for all harness tools."""

    name: str
    description: str
    parameters_schema: Dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool asynchronously with supplied parameters."""
        pass

    def to_anthropic_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters_schema,
        }

    def to_openai_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }
