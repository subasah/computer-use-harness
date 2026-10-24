"""
Benchmark Task: Shell & File Parsing of Financial Receipts.
"""

from __future__ import annotations

from typing import List

from harness.sandbox.base import BaseSandbox
from harness.verification.assertions import BaseAssertion, FileExistsAssertion, FileJsonAssertion


class ReceiptProcessingTask:
    name = "task_01_receipt_processing"
    category = "shell_and_filesystem"
    instruction = (
        "Process all invoice receipt text files inside the 'inbox/' directory. "
        "Extract the invoice IDs and amounts, calculate the grand total and invoice count, "
        "and write the final summary into 'reports/accounting_summary.json' with keys "
        "'invoice_count' and 'grand_total'."
    )

    def setup(self, sandbox: BaseSandbox) -> None:
        """Seed the sandbox with test invoice files."""
        sandbox.write_file(
            "inbox/inv_001.txt",
            "INVOICE #INV-1001\nVendor: Harbour Cafe\nDate: 2026-09-02\nAmount: $45.50\nStatus: Pending",
        )
        sandbox.write_file(
            "inbox/inv_002.txt",
            "INVOICE #INV-1002\nVendor: City Taxi Transit\nDate: 2026-09-05\nAmount: $67.00\nStatus: Pending",
        )
        sandbox.write_file(
            "inbox/inv_003.txt",
            "INVOICE #INV-1003\nVendor: Parkside Hotel\nDate: 2026-09-11\nAmount: $300.00\nStatus: Pending",
        )

    def get_assertions(self) -> List[BaseAssertion]:
        return [
            FileExistsAssertion("reports/accounting_summary.json"),
            FileJsonAssertion(
                "reports/accounting_summary.json",
                {"invoice_count": 3, "grand_total": 412.50},
            ),
        ]
