"""
Configuration management for Nexus Computer Use Harness.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SandboxType(str, Enum):
    DOCKER = "docker"
    LOCAL = "local"


class LLMProviderType(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    MOCK = "mock"


class Resolution(BaseModel):
    width: int = Field(default=1024, description="Display resolution width in pixels")
    height: int = Field(default=768, description="Display resolution height in pixels")


class SandboxConfig(BaseModel):
    sandbox_type: SandboxType = Field(default=SandboxType.LOCAL, description="Execution sandbox backend")
    workspace_dir: str = Field(default="./workspace", description="Local workspace directory")
    docker_image: str = Field(
        default="nexus-computer-use-sandbox:latest",
        description="Docker image to use for containerized sandbox",
    )
    docker_container_name: str = Field(
        default="nexus_sandbox_runtime",
        description="Name of the running sandbox container",
    )
    display: str = Field(default=":99", description="X11 display identifier")
    resolution: Resolution = Field(default_factory=Resolution)
    vnc_port: int = Field(default=5900, description="VNC streaming port")
    novnc_port: int = Field(default=6080, description="noVNC web interface port")
    memory_limit: str = Field(default="4g", description="Container memory limit")
    cpu_quota: float = Field(default=2.0, description="Container CPU quota (cores)")
    network_restricted: bool = Field(default=True, description="Enforce egress network isolation")


class MCPConfig(BaseModel):
    auto_discovery: bool = Field(default=True, description="Enable automatic MCP server discovery")
    storytold_enabled: bool = Field(default=True, description="Enable StoryTold software MCP server")
    filesystem_enabled: bool = Field(default=True, description="Enable standard filesystem MCP server")
    custom_servers: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Mapping of server name to server startup configurations",
    )


class GuardrailConfig(BaseModel):
    max_steps: int = Field(default=30, description="Maximum step budget per execution run")
    max_cost_usd: float = Field(default=5.00, description="Maximum budget in USD per run")
    command_timeout_seconds: int = Field(default=30, description="Shell command execution timeout")
    loop_detection_window: int = Field(default=4, description="Window size for detecting repeated actions")
    prompt_injection_defense: bool = Field(default=True, description="Enable visual and text prompt injection defense")
    blocked_commands: List[str] = Field(
        default_factory=lambda: [
            "rm -rf /",
            "mkfs",
            ":(){ :|:& };:",
            "chmod -R 777 /",
            "> /dev/sda",
            "shutdown",
            "reboot",
        ]
    )


class HarnessConfig(BaseModel):
    """Root configuration object for NexusCUH."""

    app_name: str = "NexusCUH"
    version: str = "0.1.0"
    provider: LLMProviderType = Field(default=LLMProviderType.MOCK, description="Active LLM provider")
    model_name: str = Field(default="claude-3-7-sonnet-20250219", description="Target model identifier")
    api_key: Optional[str] = Field(default=None, description="API key for LLM provider")
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    guardrails: GuardrailConfig = Field(default_factory=GuardrailConfig)
    log_dir: str = Field(default="./logs/runs", description="Directory to persist run recordings")
    record_runs: bool = Field(default=True, description="Persist screenshots and action traces")

    @classmethod
    def load_from_env(cls) -> "HarnessConfig":
        """Load configuration from environment variables with sensible fallbacks."""
        provider_str = os.getenv("NEXUS_DEFAULT_PROVIDER", "mock").lower()
        provider = LLMProviderType(provider_str) if provider_str in [p.value for p in LLMProviderType] else LLMProviderType.MOCK

        sandbox_str = os.getenv("NEXUS_SANDBOX_TYPE", "local").lower()
        sandbox_type = SandboxType(sandbox_str) if sandbox_str in [s.value for s in SandboxType] else SandboxType.LOCAL

        api_key = None
        if provider == LLMProviderType.ANTHROPIC:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        elif provider == LLMProviderType.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
        elif provider == LLMProviderType.GEMINI:
            api_key = os.getenv("GEMINI_API_KEY")

        return cls(
            provider=provider,
            model_name=os.getenv("NEXUS_DEFAULT_MODEL", "claude-3-7-sonnet-20250219"),
            api_key=api_key,
            sandbox=SandboxConfig(
                sandbox_type=sandbox_type,
                workspace_dir=os.getenv("NEXUS_WORKSPACE_DIR", "./workspace"),
                docker_image=os.getenv("NEXUS_DOCKER_IMAGE", "nexus-computer-use-sandbox:latest"),
                docker_container_name=os.getenv("NEXUS_DOCKER_CONTAINER_NAME", "nexus_sandbox_runtime"),
                display=os.getenv("NEXUS_DOCKER_DISPLAY", ":99"),
                vnc_port=int(os.getenv("NEXUS_DOCKER_VNC_PORT", "5900")),
                novnc_port=int(os.getenv("NEXUS_DOCKER_NOVNC_PORT", "6080")),
                memory_limit=os.getenv("NEXUS_SANDBOX_MEMORY_LIMIT", "4g"),
                cpu_quota=float(os.getenv("NEXUS_SANDBOX_CPU_QUOTA", "2.0")),
            ),
            mcp=MCPConfig(
                auto_discovery=os.getenv("NEXUS_MCP_AUTO_DISCOVERY", "true").lower() == "true",
                storytold_enabled=os.getenv("NEXUS_MCP_STORYTOLD_ENABLED", "true").lower() == "true",
                filesystem_enabled=os.getenv("NEXUS_MCP_FILESYSTEM_ENABLED", "true").lower() == "true",
            ),
            guardrails=GuardrailConfig(
                max_steps=int(os.getenv("NEXUS_MAX_STEPS", "30")),
                max_cost_usd=float(os.getenv("NEXUS_MAX_COST_USD", "5.00")),
                loop_detection_window=int(os.getenv("NEXUS_LOOP_DETECTION_WINDOW", "4")),
            ),
            log_dir=os.getenv("NEXUS_RUN_LOGS_DIR", "./logs/runs"),
            record_runs=os.getenv("NEXUS_RECORD_RUNS", "true").lower() == "true",
        )
