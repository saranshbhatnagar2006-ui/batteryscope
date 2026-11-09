
import time
import psutil

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live

from modules.history import save_snapshot

console = Console()

BATTERY_PATH = Path("/sys/class/power_supply/BAT1")


def read_battery(filename):

    try:
        value = (BATTERY_PATH / filename).read_text().strip()
        return int(value)
    except (OSError, ValueError):
        return None


def get_battery_data():

    battery = psutil.sensors_battery()

    if battery:
        percentage = battery.percent
    else:
        percentage = read_battery("capacity")

    voltage_raw = read_battery("voltage_now")
    current_raw = read_battery("current_now")

    voltage = (
        voltage_raw / 1_000_000
        if voltage_raw is not None else None
    )

    current = (
        current_raw / 1_000_000
        if current_raw is not None else None
    )

    power = None

    if voltage is not None and current is not None:
        power = abs(voltage * current)

    return percentage, voltage, current, power


def get_top_processes():

    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "memory_percent"]
    ):

        try:
            cpu = process.cpu_percent(None)

            processes.append({
                "pid": process.pid,
                "name": process.info["name"] or "Unknown",
                "cpu": cpu,
                "ram": process.info["memory_percent"] or 0
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return sorted(
        processes,
        key=lambda p: p["cpu"],
        reverse=True
    )[:5]


def create_dashboard(cpu, ram, battery, voltage,
                     current, power, processes):

    table = Table(
        title="BATTERYSCOPE - LIVE SYSTEM MONITOR",
        expand=True
    )

    table.add_column("Metric", style="cyan")
    table.add_column("Current Reading", style="green")

    table.add_row("CPU Usage", f"{cpu:.1f}%")
    table.add_row("RAM Usage", f"{ram:.1f}%")
    table.add_row(
        "Battery Level",
        f"{battery}%" if battery is not None else "Unavailable"
    )
    table.add_row(
        "Voltage",
        f"{voltage:.3f} V" if voltage is not None else "Unavailable"
    )
    table.add_row(
        "Current",
        f"{current:.3f} A" if current is not None else "Unavailable"
    )
    table.add_row(
        "Battery Power",
        f"{power:.3f} W" if power is not None else "Unavailable"
    )

    process_table = Table(title="TOP 5 CPU CONSUMING PROCESSES")

    process_table.add_column("PID")
    process_table.add_column("Process")
    process_table.add_column("CPU %")
    process_table.add_column("RAM %")

    for process in processes:

        process_table.add_row(
            str(process["pid"]),
            process["name"][:22],
            f'{process["cpu"]:.1f}%',
            f'{process["ram"]:.2f}%'
        )

    from rich.console import Group

    return Group(table, process_table)


def monitor_system():

    console.print(
        "\n[bold green]BATTERYSCOPE LIVE MONITOR STARTED[/bold green]"
    )

    psutil.cpu_percent(interval=None)

    last_history = time.monotonic() -60

    try:

        with Live(console=console, refresh_per_second=1) as live:

            while True:

                time.sleep(1)

                cpu = psutil.cpu_percent(interval=None)

                ram = psutil.virtual_memory().percent

                battery, voltage, current, power = get_battery_data()

                processes = get_top_processes()

                dashboard = create_dashboard(
                    cpu,
                    ram,
                    battery,
                    voltage,
                    current,
                    power,
                    processes
                )

                live.update(dashboard)

                # Save historical data every 60 seconds
                now = time.monotonic()

                if now - last_history >= 60:

                    top = processes[0] if processes else {}

                    save_snapshot({
                        "cpu_percent": cpu,
                        "ram_percent": ram,
                        "battery_percent": battery,
                        "voltage": voltage,
                        "current": current,
                        "power_watts": power,
                        "top_process": top.get("name", "Unknown"),
                        "top_process_cpu": top.get("cpu", 0),
                        "top_process_ram": top.get("ram", 0)
                    })

                    last_history = now

    except KeyboardInterrupt:

        console.print(
            "\n[bold yellow]BatteryScope monitoring stopped.[/bold yellow]"
        )


if __name__ == "__main__":
    monitor_system()
