"""
Nexus Computer Use Harness (NexusCUH)
=====================================
A production-grade, extensible harness for building, running, evaluating,
and sandboxing Computer-Use AI Agents with Model Context Protocol (MCP) integration.
"""

__version__ = "0.1.0"
__author__ = "Suba Sah"

from harness.agent.orchestrator import AgentOrchestrator
from harness.config import HarnessConfig

__all__ = ["HarnessConfig", "AgentOrchestrator", "__version__"]
