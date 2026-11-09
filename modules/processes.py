
import psutil
import time

from rich.console import Console
from rich.table import Table

console = Console()


def analyze_processes(display=True, interval=1):
    """
    Collect CPU and RAM usage of running processes.

    display: Whether to display the Rich process table.
    interval: CPU measurement interval in seconds.

    Returns a list of process dictionaries.
    """

    processes = []

    if interval <= 0:
        raise ValueError("Interval must be greater than zero.")

    if display:
        console.print(
            "\n[bold cyan]Scanning running processes...[/bold cyan]"
        )

    # First CPU measurement
    active_processes = []

    for process in psutil.process_iter(
        ["pid", "name", "status"]
    ):
        try:
            process.cpu_percent(interval=None)
            active_processes.append(process)

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    # Wait for CPU measurement interval
    time.sleep(interval)

    # Second CPU measurement
    for process in active_processes:
        try:
            cpu = process.cpu_percent(interval=None)

            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = process.memory_percent()

            processes.append({
                "pid": process.pid,
                "name": process.name(),
                "cpu": max(0.0, cpu),
                "memory": memory_percent,
                "memory_mb": memory_mb,
                "status": process.status()
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    # Sort by CPU utilization
    processes.sort(
        key=lambda item: item["cpu"],
        reverse=True
    )

    # Create resource-consumer table
    table = Table(
        title="BATTERYSCOPE - TOP RESOURCE CONSUMERS"
    )

    table.add_column("PID", style="cyan")
    table.add_column("Process", style="green")
    table.add_column("CPU %", style="yellow")
    table.add_column("RAM %", style="magenta")
    table.add_column("Memory MB", style="blue")
    table.add_column("Status", style="white")

    for process in processes[:10]:
        table.add_row(
            str(process["pid"]),
            process["name"][:22],
            f'{process["cpu"]:.1f}%',
            f'{process["memory"]:.2f}%',
            f'{process["memory_mb"]:.2f}',
            process["status"]
        )

    # Display table only when requested
    if display:
        console.print(table)

    # Return collected process data
    return processes


if __name__ == "__main__":
    analyze_processes()
