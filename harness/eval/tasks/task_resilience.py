"""
Benchmark Task: Self-Healing and Error Recovery under Fault Injection.
"""

from __future__ import annotations

from typing import List

from harness.sandbox.base import BaseSandbox
from harness.verification.assertions import (
    BaseAssertion,
    FileContentRegexAssertion,
    FileExistsAssertion,
)


class ResilienceTask:
    name = "task_04_error_resilience"
    category = "fault_tolerance"
    instruction = (
        "There is a locked file at 'protected/config.env' with read-only permissions (chmod 444). "
        "Diagnose the permission failure when attempting to update it, safely recover by modifying "
        "its permissions, append 'RECOVERY_COMPLETED=TRUE', and re-lock the file permissions."
    )

    def setup(self, sandbox: BaseSandbox) -> None:
        sandbox.write_file("protected/config.env", "MODE=PRODUCTION\n")
        sandbox.exec_command("chmod 444 protected/config.env")

    def get_assertions(self) -> List[BaseAssertion]:
        return [
            FileExistsAssertion("protected/config.env"),
            FileContentRegexAssertion(
                "protected/config.env",
                r"RECOVERY_COMPLETED=TRUE",
                description="Contains recovery completed flag",
            ),
        ]
