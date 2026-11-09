
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

BATTERY_PATH = Path("/sys/class/power_supply/BAT1")


def read_value(filename):
    """Read a battery value from Linux sysfs."""

    file_path = BATTERY_PATH / filename

    try:
        return file_path.read_text().strip()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def convert_micro(value):
    """Convert micro-units into standard units."""

    if value is None:
        return None

    return int(value) / 1_000_000


def battery_analysis():

    manufacturer = read_value("manufacturer")
    model = read_value("model_name")
    status = read_value("status")

    capacity = read_value("capacity")
    voltage = read_value("voltage_now")
    current = read_value("current_now")

    charge_full = read_value("charge_full")
    charge_design = read_value("charge_full_design")

    cycle_count = read_value("cycle_count")

    # Calculate battery health
    health = None

    if charge_full and charge_design:
        design = int(charge_design)

        if design > 0:
            health = int(charge_full) / design * 100

    # Convert voltage and current
    voltage_v = convert_micro(voltage)
    current_a = convert_micro(current)

    # Calculate battery power
    power_w = None

    if voltage_v is not None and current_a is not None:
        power_w = voltage_v * abs(current_a)

    # Display information
    table = Table(title="BATTERYSCOPE - BATTERY INTELLIGENCE")

    table.add_column("Parameter", style="cyan")
    table.add_column("Reading", style="green")

    table.add_row("Manufacturer", manufacturer or "Unavailable")
    table.add_row("Model", model or "Unavailable")
    table.add_row("Status", status or "Unavailable")
    table.add_row("Battery Level", f"{capacity}%" if capacity else "Unavailable")
    table.add_row("Voltage", f"{voltage_v:.3f} V" if voltage_v is not None else "Unavailable")
    table.add_row("Current", f"{current_a:.3f} A" if current_a is not None else "Unavailable")
    table.add_row("Power Draw", f"{power_w:.3f} W" if power_w is not None else "Unavailable")
    table.add_row("Battery Health", f"{health:.2f}%" if health is not None else "Unavailable")
    table.add_row("Cycle Count", cycle_count or "Unavailable")

    console.print(table)


if __name__ == "__main__":
    battery_analysis()
