"""
Multi-Modal Assertions for deterministic ground-truth verification.
"""

from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from harness.sandbox.base import BaseSandbox


class BaseAssertion(ABC):
    """Abstract assertion evaluating actual environment state against ground truth."""

    name: str

    @abstractmethod
    async def evaluate(self, sandbox: BaseSandbox, mcp_manager: Optional[Any] = None) -> tuple[bool, str]:
        """
        Evaluate assertion asynchronously.
        Returns (has_passed, diagnostic_detail).
        """
        pass


class FileExistsAssertion(BaseAssertion):
    """Asserts that a file or directory exists inside the sandbox."""

    def __init__(self, path: str):
        self.path = path
        self.name = f"FileExists({path})"

    async def evaluate(self, sandbox: BaseSandbox, mcp_manager: Optional[Any] = None) -> tuple[bool, str]:
        exists = sandbox.file_exists(self.path)
        if exists:
            return True, f"File '{self.path}' exists."
        return False, f"File '{self.path}' does NOT exist."


class FileContentRegexAssertion(BaseAssertion):
    """Asserts that a file's content matches a specific regular expression."""

    def __init__(self, path: str, regex_pattern: str, description: Optional[str] = None):
        self.path = path
        self.regex = re.compile(regex_pattern, re.MULTILINE | re.DOTALL)
        self.description = description or f"matches '{regex_pattern}'"
        self.name = f"FileRegex({path}, {self.description})"

    async def evaluate(self, sandbox: BaseSandbox, mcp_manager: Optional[Any] = None) -> tuple[bool, str]:
        if not sandbox.file_exists(self.path):
            return False, f"File '{self.path}' does not exist for regex verification."

        try:
            content = sandbox.read_file(self.path)
            if self.regex.search(content):
                return True, f"File '{self.path}' matches required pattern: {self.description}"
            return False, f"File '{self.path}' content failed to match pattern: {self.description}"
        except Exception as exc:
            return False, f"Error reading file '{self.path}': {str(exc)}"


class FileJsonAssertion(BaseAssertion):
    """Asserts that a file contains valid JSON with required keys and values."""

    def __init__(self, path: str, expected_key_values: Dict[str, Any]):
        self.path = path
        self.expected = expected_key_values
        self.name = f"FileJson({path})"

    async def evaluate(self, sandbox: BaseSandbox, mcp_manager: Optional[Any] = None) -> tuple[bool, str]:
        if not sandbox.file_exists(self.path):
            return False, f"JSON file '{self.path}' does not exist."

        try:
            content = sandbox.read_file(self.path)
            data = json.loads(content)
            for k, expected_val in self.expected.items():
                if k not in data:
                    return False, f"JSON missing required key '{k}'."
                if data[k] != expected_val:
                    return False, f"JSON key '{k}' value '{data[k]}' != expected '{expected_val}'."
            return True, f"JSON file '{self.path}' verified with all required keys."
        except Exception as exc:
            return False, f"JSON parse/validation error on '{self.path}': {str(exc)}"


class FileHashAssertion(BaseAssertion):
    """Asserts that a file's SHA-256 hash matches the golden reference."""

    def __init__(self, path: str, expected_sha256: str):
        self.path = path
        self.expected_hash = expected_sha256.lower()
        self.name = f"FileHash({path})"

    async def evaluate(self, sandbox: BaseSandbox, mcp_manager: Optional[Any] = None) -> tuple[bool, str]:
        if not sandbox.file_exists(self.path):
            return False, f"File '{self.path}' does not exist for hash check."

        data = sandbox.read_file_bytes(self.path)
        actual_hash = hashlib.sha256(data).hexdigest().lower()
        if actual_hash == self.expected_hash:
            return True, f"File '{self.path}' SHA-256 verified ({actual_hash})."
        return False, f"Hash mismatch for '{self.path}': actual {actual_hash} != expected {self.expected_hash}"


class MCPStateAssertion(BaseAssertion):
    """Asserts that an MCP server state satisfies a condition."""

    def __init__(self, server_name: str, tool_name: str, tool_args: Dict[str, Any], validator_fn: Any):
        self.server_name = server_name
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.validator_fn = validator_fn
        self.name = f"MCPState({server_name}.{tool_name})"

    async def evaluate(self, sandbox: BaseSandbox, mcp_manager: Optional[Any] = None) -> tuple[bool, str]:
        if not mcp_manager or self.server_name not in mcp_manager.clients:
            return False, f"MCP server '{self.server_name}' not available for state assertion."

        client = mcp_manager.clients[self.server_name]
        try:
            res = await client.call_tool(self.tool_name, self.tool_args)
            text = res.content[0].text if res.content else ""
            passed, detail = self.validator_fn(text)
            return passed, f"MCP State check on {self.server_name}.{self.tool_name}: {detail}"
        except Exception as exc:
            return False, f"Error calling MCP tool for assertion: {str(exc)}"
