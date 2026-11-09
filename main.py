
import platform
import psutil
import shutil
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()


def system_information():

    table = Table(title="BATTERYSCOPE - SYSTEM INFORMATION")

    table.add_column("Component", style="cyan")
    table.add_column("Details", style="green")

    table.add_row("Operating System", platform.system())
    table.add_row("OS Version", platform.version())
    table.add_row("Architecture", platform.machine())
    table.add_row("Processor", platform.processor())
    table.add_row("CPU Cores", str(psutil.cpu_count(logical=False)))
    table.add_row("Logical CPUs", str(psutil.cpu_count()))

    memory = psutil.virtual_memory()

    table.add_row(
        "Total RAM",
        f"{memory.total / (1024**3):.2f} GB"
    )

    table.add_row(
        "Used RAM",
        f"{memory.used / (1024**3):.2f} GB"
    )

    table.add_row(
        "RAM Usage",
        f"{memory.percent}%"
    )

    disk = shutil.disk_usage("/")

    table.add_row(
        "Total Disk",
        f"{disk.total / (1024**3):.2f} GB"
    )

    table.add_row(
        "Used Disk",
        f"{disk.used / (1024**3):.2f} GB"
    )

    battery = psutil.sensors_battery()

    if battery:

        table.add_row(
            "Battery Percentage",
            f"{battery.percent}%"
        )

        table.add_row(
            "Charging",
            str(battery.power_plugged)
        )

    else:
        table.add_row("Battery", "Not detected by psutil")

    console.print(table)


if __name__ == "__main__":

    console.print(
        "\n[bold green]BATTERYSCOPE STARTED[/bold green]"
    )

    console.print(f"Time: {datetime.now()}")

    system_information()
