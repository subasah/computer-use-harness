"""
Nexus Computer Use Harness CLI Tool.
Command-line interface for running tasks, evaluating benchmarks, and managing MCP servers.
"""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harness.agent.orchestrator import AgentOrchestrator
from harness.agent.providers import AnthropicProvider, MockProvider, OpenAIProvider
from harness.config import HarnessConfig, SandboxType
from harness.eval.benchmark import BenchmarkRunner
from harness.eval.leaderboard import LeaderboardReporter
from harness.mcp.server_manager import MCPServerManager

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="nexus")
def main() -> None:
    """Nexus Computer Use Harness (NexusCUH) - Enterprise Computer Use Agent Platform."""
    pass


@main.command()
@click.option("--task", "-t", required=True, help="Task instruction string for the agent to execute.")
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["mock", "anthropic", "openai"]),
    default="mock",
    help="LLM provider backend.",
)
@click.option(
    "--sandbox",
    "-s",
    type=click.Choice(["local", "docker"]),
    default="local",
    help="Sandbox execution environment.",
)
@click.option("--workspace", "-w", default="./workspace", help="Sandbox workspace directory.")
def run(task: str, provider: str, sandbox: str, workspace: str) -> None:
    """Execute a task using the Computer Use Agent."""
    console.print(Panel(f"[bold cyan]NexusCUH Task Execution[/bold cyan]\n[white]{task}[/white]", border_style="cyan"))

    config = HarnessConfig.load_from_env()
    config.sandbox.sandbox_type = SandboxType(sandbox)
    config.sandbox.workspace_dir = workspace

    if provider == "anthropic":
        llm = AnthropicProvider(api_key=config.api_key, model=config.model_name)
    elif provider == "openai":
        llm = OpenAIProvider(api_key=config.api_key)
    else:
        llm = MockProvider()

    async def _run() -> None:
        orchestrator = AgentOrchestrator(config=config, provider=llm)
        try:
            with console.status("[bold green]Initializing sandbox and MCP servers..."):
                await orchestrator.initialize()

            with console.status("[bold yellow]Executing agent ReAct loop..."):
                result = await orchestrator.run_task(task)

            console.print("\n[bold green]Execution Complete![/bold green]")
            table = Table(title="Run Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            table.add_row("Success", str(result["success"]))
            table.add_row("Steps", str(result["steps_count"]))
            table.add_row("Duration", f"{result['duration_seconds']}s")
            table.add_row("Estimated Cost", f"${result['budget']['estimated_cost_usd']}")
            table.add_row("Termination Reason", str(result["termination_reason"]))

            console.print(table)

            if result["verification"]["results"]:
                verif_table = Table(title="Ground-Truth Verification Assertions")
                verif_table.add_column("Assertion", style="white")
                verif_table.add_column("Status", style="bold")
                verif_table.add_column("Diagnostic", style="dim")

                for res in result["verification"]["results"]:
                    status = "[green]PASS[/green]" if res["passed"] else "[red]FAIL[/red]"
                    verif_table.add_row(res["name"], status, res["diagnostic"])

                console.print(verif_table)

        finally:
            await orchestrator.shutdown()

    asyncio.run(_run())


@main.command()
@click.option("--output", "-o", default="benchmark_results.md", help="Output path for report (Markdown or JSON).")
def eval(output: str) -> None:
    """Run full evaluation benchmark suite and generate report."""
    console.print(Panel("[bold yellow]Starting NexusCUH Benchmark Suite Evaluation...[/bold yellow]", border_style="yellow"))

    config = HarnessConfig.load_from_env()
    config.sandbox.sandbox_type = SandboxType.LOCAL

    async def _eval() -> None:
        orchestrator = AgentOrchestrator(config=config, provider=MockProvider())
        try:
            await orchestrator.initialize()
            runner = BenchmarkRunner(orchestrator)

            with console.status("[bold green]Evaluating benchmark tasks..."):
                summary = await runner.run_suite()

            LeaderboardReporter.save_report(summary, output)

            console.print("\n[bold green]Benchmark evaluation completed![/bold green]")
            console.print(f"Results saved to: [cyan]{output}[/cyan]\n")

            md_view = LeaderboardReporter.generate_markdown(summary)
            console.print(Panel(md_view, title="Benchmark Summary", border_style="green"))

        finally:
            await orchestrator.shutdown()

    asyncio.run(_eval())


@main.command()
def mcp() -> None:
    """Inspect and list active MCP tools across connected servers."""
    config = HarnessConfig.load_from_env()
    mgr = MCPServerManager(config.mcp)

    async def _list_mcp() -> None:
        with console.status("[bold blue]Starting MCP servers and querying tools..."):
            await mgr.start_all()

        tools = mgr.get_agent_tools()
        table = Table(title=f"Discovered MCP Tools ({len(tools)} total)")
        table.add_column("Server", style="cyan")
        table.add_column("Tool Name", style="bold green")
        table.add_column("Description", style="white")

        for t in tools:
            server, original = t.name.split("__", 1) if "__" in t.name else ("custom", t.name)
            table.add_row(server, original, t.description)

        console.print(table)
        await mgr.stop_all()

    asyncio.run(_list_mcp())


if __name__ == "__main__":
    main()
