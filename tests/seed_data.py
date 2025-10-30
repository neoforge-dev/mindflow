"""
Test data seeding script.

Populates the MindFlow system with realistic test data including edge cases.
"""

import sys
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from tests.client import MindFlowClient
from tests.factories import TestDataSets

console = Console()


def seed_realistic_tasks(client: MindFlowClient) -> list[str]:
    """Seed realistic mixed tasks."""
    console.print("\n[bold blue]Seeding realistic mixed tasks...[/bold blue]")

    tasks = TestDataSets.realistic_mixed_tasks(count=20)
    task_ids = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating tasks...", total=len(tasks))

        for task_data in tasks:
            try:
                response = client.create_task(task_data)
                task_ids.append(response.data["id"])
                progress.update(task, advance=1)
            except Exception as e:
                console.print(f"[red]✗ Failed to create task: {e}[/red]")

    console.print(f"[green]✓ Created {len(task_ids)} realistic tasks[/green]")
    return task_ids


def seed_edge_cases(client: MindFlowClient) -> list[str]:
    """Seed edge case tasks."""
    console.print("\n[bold blue]Seeding edge case tasks...[/bold blue]")

    tasks = TestDataSets.edge_cases()
    task_ids = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating edge cases...", total=len(tasks))

        for task_data in tasks:
            try:
                response = client.create_task(task_data)
                task_ids.append(response.data["id"])
                progress.update(task, advance=1)
            except Exception as e:
                console.print(f"[yellow]⚠ Edge case failed (expected): {e}[/yellow]")

    console.print(f"[green]✓ Created {len(task_ids)} edge case tasks[/green]")
    return task_ids


def seed_scoring_test_set(client: MindFlowClient) -> list[str]:
    """Seed tasks for scoring algorithm testing."""
    console.print("\n[bold blue]Seeding scoring test tasks...[/bold blue]")

    tasks = TestDataSets.scoring_test_set()
    task_ids = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating scoring tests...", total=len(tasks))

        for task_data in tasks:
            try:
                response = client.create_task(task_data)
                task_ids.append(response.data["id"])
                progress.update(task, advance=1)
            except Exception as e:
                console.print(f"[red]✗ Failed: {e}[/red]")

    console.print(f"[green]✓ Created {len(task_ids)} scoring test tasks[/green]")
    return task_ids


def verify_best_task(client: MindFlowClient) -> None:
    """Verify best task endpoint and show results."""
    console.print("\n[bold blue]Testing best task selection...[/bold blue]")

    try:
        response = client.get_best_task()

        if isinstance(response.data, dict) and "id" in response.data:
            table = Table(title="Best Task Selected")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="magenta")

            table.add_row("ID", response.data.get("id", "N/A"))
            table.add_row("Title", response.data.get("title", "N/A"))
            table.add_row("Priority", str(response.data.get("priority", "N/A")))
            table.add_row("Score", str(response.data.get("score", "N/A")))
            table.add_row("Reasoning", response.data.get("reasoning", "N/A"))

            console.print(table)
            console.print("[green]✓ Best task endpoint working correctly[/green]")
        else:
            console.print("[yellow]⚠ No active tasks found[/yellow]")

    except Exception as e:
        console.print(f"[red]✗ Error testing best task: {e}[/red]")


def query_and_display_stats(client: MindFlowClient) -> None:
    """Query tasks and display statistics."""
    console.print("\n[bold blue]Querying task statistics...[/bold blue]")

    try:
        # Query by status
        statuses = ["pending", "in_progress", "completed", "snoozed"]
        status_counts = {}

        for status in statuses:
            try:
                response = client.query_tasks(status=status)
                if isinstance(response.data, list):
                    status_counts[status] = len(response.data)
            except Exception:
                status_counts[status] = 0

        # Display stats table
        table = Table(title="Task Statistics by Status")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="magenta")

        for status, count in status_counts.items():
            table.add_row(status.replace("_", " ").title(), str(count))

        console.print(table)

        # Query by priority
        priority_counts = {}
        for priority in range(1, 6):
            try:
                response = client.query_tasks(priority=priority)
                if isinstance(response.data, list):
                    priority_counts[priority] = len(response.data)
            except Exception:
                priority_counts[priority] = 0

        table2 = Table(title="Task Statistics by Priority")
        table2.add_column("Priority", style="cyan")
        table2.add_column("Count", style="magenta")

        for priority, count in priority_counts.items():
            table2.add_row(str(priority), str(count))

        console.print(table2)

    except Exception as e:
        console.print(f"[red]✗ Error querying statistics: {e}[/red]")


def main() -> None:
    """Main seeding function."""
    console.print("[bold cyan]MindFlow Test Data Seeder[/bold cyan]")
    console.print("=" * 60)

    # Create client
    client = MindFlowClient()

    # Health check
    console.print("\n[bold]Checking API health...[/bold]")
    if not client.health_check():
        console.print("[red]✗ API is not accessible. Check deployment URL.[/red]")
        sys.exit(1)
    console.print("[green]✓ API is healthy[/green]")

    # Seed different data sets
    all_task_ids = []

    # Option 1: Realistic mixed tasks
    all_task_ids.extend(seed_realistic_tasks(client))

    # Option 2: Edge cases
    all_task_ids.extend(seed_edge_cases(client))

    # Option 3: Scoring test set
    all_task_ids.extend(seed_scoring_test_set(client))

    # Summary
    console.print(f"\n[bold green]✓ Successfully seeded {len(all_task_ids)} tasks[/bold green]")

    # Verify and display stats
    verify_best_task(client)
    query_and_display_stats(client)

    console.print("\n[bold cyan]Seeding complete![/bold cyan]")
    console.print("You can now:")
    console.print("  1. Run tests: [cyan]pytest tests/[/cyan]")
    console.print("  2. Test with Custom GPT: [cyan]'What should I do next?'[/cyan]")
    console.print("  3. View data in Google Sheet")


if __name__ == "__main__":
    main()
