"""
End-to-End Evaluation & Benchmark Runner tests.
"""

import tempfile

import pytest

from harness.agent.orchestrator import AgentOrchestrator
from harness.agent.providers import LLMResponse, MockProvider, ToolCallRequest
from harness.config import HarnessConfig, SandboxType
from harness.eval.benchmark import BenchmarkRunner
from harness.eval.leaderboard import LeaderboardReporter
from harness.eval.tasks.task_receipts import ReceiptProcessingTask
from harness.eval.tasks.task_wordcraft_doc import WordCraftDocumentTask


@pytest.mark.asyncio
async def test_benchmark_runner_with_mock_agent():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = HarnessConfig.load_from_env()
        config.sandbox.sandbox_type = SandboxType.LOCAL
        config.sandbox.workspace_dir = tmpdir

        mock_provider = MockProvider()

        # Dynamic handler that knows how to fulfill the benchmark tasks
        def dynamic_mock_agent(messages):
            last_msg = messages[-1]
            content = str(last_msg.get("content", ""))

            # Handle Receipt Processing Task
            if "invoice receipt text files" in content:
                return LLMResponse(
                    tool_calls=[
                        ToolCallRequest(
                            id="tc-1",
                            name="shell",
                            arguments={
                                "command": (
                                    "mkdir -p reports && echo '{\"invoice_count\": 3, \"grand_total\": 412.50}' "
                                    "> reports/accounting_summary.json"
                                )
                            },
                        )
                    ]
                )

            # Handle WordCraft Task
            if "StoryTold WordCraft" in content:
                return LLMResponse(
                    tool_calls=[
                        ToolCallRequest(
                            id="tc-wc-1",
                            name="wordcraft__new_document",
                            arguments={"title": "Q3 Engineering Architecture Memo"},
                        ),
                        ToolCallRequest(
                            id="tc-wc-2",
                            name="wordcraft__type_text",
                            arguments={
                                "text": "Executive Summary",
                                "paragraph_type": "heading1",
                            },
                        ),
                        ToolCallRequest(
                            id="tc-wc-3",
                            name="wordcraft__type_text",
                            arguments={
                                "text": "NexusCUH delivers hybrid shell, GUI, and MCP orchestration.",
                                "paragraph_type": "paragraph",
                            },
                        ),
                        ToolCallRequest(
                            id="tc-wc-4",
                            name="wordcraft__save_document",
                            arguments={"path": "docs/architecture_memo.txt"},
                        ),
                    ]
                )

            # Done
            return LLMResponse(text="Task completed successfully.", tool_calls=[])

        mock_provider.set_dynamic_handler(dynamic_mock_agent)

        orchestrator = AgentOrchestrator(config=config, provider=mock_provider)
        await orchestrator.initialize()

        test_tasks = [ReceiptProcessingTask(), WordCraftDocumentTask()]
        runner = BenchmarkRunner(orchestrator, tasks=test_tasks)

        summary = await runner.run_suite()

        assert summary.total_tasks == 2
        assert summary.successful_tasks == 2
        assert summary.pass_rate_percentage == 100.0

        # Generate markdown report
        md_report = LeaderboardReporter.generate_markdown(summary)
        assert "# NexusCUH Evaluation Benchmark Report" in md_report
        assert "PASSED" in md_report

        await orchestrator.shutdown()
