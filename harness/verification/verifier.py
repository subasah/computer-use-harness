"""
Verification runner and report generator.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from harness.sandbox.base import BaseSandbox
from harness.verification.assertions import BaseAssertion


@dataclass
class AssertionResult:
    name: str
    passed: bool
    diagnostic: str


@dataclass
class VerificationReport:
    passed: bool
    total_assertions: int
    passed_count: int
    failed_count: int
    results: List[AssertionResult] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "total_assertions": self.total_assertions,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "results": [
                {"name": r.name, "passed": r.passed, "diagnostic": r.diagnostic}
                for r in self.results
            ],
            "timestamp": self.timestamp,
        }


class MultiModalVerifier:
    """
    Executes a suite of ground-truth assertions against the sandbox and MCP servers
    to definitively establish whether a computer use task succeeded.
    """

    def __init__(self, assertions: Optional[List[BaseAssertion]] = None):
        self.assertions: List[BaseAssertion] = assertions or []

    def add_assertion(self, assertion: BaseAssertion) -> "MultiModalVerifier":
        self.assertions.append(assertion)
        return self

    async def verify(self, sandbox: BaseSandbox, mcp_manager: Optional[Any] = None) -> VerificationReport:
        results: List[AssertionResult] = []
        passed_count = 0
        failed_count = 0

        for assertion in self.assertions:
            has_passed, diagnostic = await assertion.evaluate(sandbox, mcp_manager)
            results.append(AssertionResult(name=assertion.name, passed=has_passed, diagnostic=diagnostic))
            if has_passed:
                passed_count += 1
            else:
                failed_count += 1

        overall_passed = (failed_count == 0) and (self.assertions != [])

        return VerificationReport(
            passed=overall_passed,
            total_assertions=len(self.assertions),
            passed_count=passed_count,
            failed_count=failed_count,
            results=results,
        )
