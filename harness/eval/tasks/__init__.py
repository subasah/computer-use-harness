"""
Benchmark tasks suite for Computer Use Agent evaluation.
"""

from harness.eval.tasks.task_gui_form import GUIFormTask
from harness.eval.tasks.task_receipts import ReceiptProcessingTask
from harness.eval.tasks.task_resilience import ResilienceTask
from harness.eval.tasks.task_wordcraft_doc import WordCraftDocumentTask

ALL_TASKS = [
    ReceiptProcessingTask(),
    WordCraftDocumentTask(),
    GUIFormTask(),
    ResilienceTask(),
]

__all__ = [
    "ReceiptProcessingTask",
    "WordCraftDocumentTask",
    "GUIFormTask",
    "ResilienceTask",
    "ALL_TASKS",
]
