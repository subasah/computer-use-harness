"""
Benchmark Task: Desktop GUI Interaction and Form Submission.
"""

from __future__ import annotations

from typing import List

from harness.sandbox.base import BaseSandbox
from harness.verification.assertions import (
    BaseAssertion,
    FileContentRegexAssertion,
    FileExistsAssertion,
)


class GUIFormTask:
    name = "task_03_gui_form_interaction"
    category = "desktop_gui"
    instruction = (
        "Interact with the desktop environment. Take a screenshot to inspect the workspace window, "
        "click into the active panel at coordinates (200, 150), type 'SUBMITTED_STATUS=CONFIRMED', "
        "and record the submission confirmation into 'gui_submission.log'."
    )

    def setup(self, sandbox: BaseSandbox) -> None:
        sandbox.write_file("gui_submission.log", "INITIALIZING\n")

    def get_assertions(self) -> List[BaseAssertion]:
        return [
            FileExistsAssertion("gui_submission.log"),
            FileContentRegexAssertion(
                "gui_submission.log",
                r"SUBMITTED_STATUS=CONFIRMED",
                description="Contains submitted status confirmation",
            ),
        ]
