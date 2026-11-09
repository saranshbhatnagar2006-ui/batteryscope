
from pathlib import Path

from rich.console import Console
from rich.table import Table

from modules.processes import analyze_processes

console = Console()

BATTERY_PATH = Path("/sys/class/power_supply/BAT1")
AC_PATH = Path("/sys/class/power_supply/ACAD")


# -----------------------------------------
# 1. BATTERY SENSOR FUNCTIONS
# -----------------------------------------

def read_sensor(filename):
    """Read a numeric battery sensor."""

    try:
        return int((BATTERY_PATH / filename).read_text().strip())
    except (FileNotFoundError, ValueError, PermissionError):
        return None


def read_text_sensor(filename):
    """Read a text-based battery sensor."""

    try:
        return (BATTERY_PATH / filename).read_text().strip()
    except (FileNotFoundError, PermissionError):
        return "Unknown"


def is_ac_connected():
    """Detect AC adapter connection."""

    try:
        value = (AC_PATH / "online").read_text().strip()
        return value == "1"
    except (FileNotFoundError, PermissionError):
        return None


# -----------------------------------------
# 2. BATTERY POWER MEASUREMENT
# -----------------------------------------

def get_system_power():

    voltage = read_sensor("voltage_now")
    current = read_sensor("current_now")

    status = read_text_sensor("status")
    ac_connected = is_ac_connected()

    if voltage is None or current is None:
        power_watts = None
    else:
        power_watts = abs(voltage * current) / 1_000_000_000_000

    return {
        "voltage": voltage / 1_000_000 if voltage is not None else None,
        "current": current / 1_000_000 if current is not None else None,
        "power_watts": power_watts,
        "status": status,
        "ac_connected": ac_connected
    }


# -----------------------------------------
# 3. BATTERY ENERGY INFORMATION
# -----------------------------------------

def get_battery_energy():

    charge_now = read_sensor("charge_now")
    charge_full = read_sensor("charge_full")
    voltage = read_sensor("voltage_now")

    if charge_now is None or voltage is None:
        energy_wh = None
    else:
        energy_wh = (
            (charge_now / 1_000_000)
            * (voltage / 1_000_000)
        )

    return {
        "charge_now_uah": charge_now,
        "charge_full_uah": charge_full,
        "energy_wh_estimate": energy_wh
    }


def calculate_battery_health():

    charge_full = read_sensor("charge_full")
    charge_design = read_sensor("charge_full_design")

    if not charge_full or not charge_design:
        return None

    return round(
        (charge_full / charge_design) * 100, 2
    )


# -----------------------------------------
# 4. ENERGY CALCULATION
# -----------------------------------------

def calculate_energy_wh(power_watts, duration_seconds):
    """Convert power in watts into energy in Wh."""

    if power_watts is None or duration_seconds <= 0:
        return None

    return power_watts * duration_seconds / 3600


# -----------------------------------------
# 5. PROCESS DATA COLLECTION
# -----------------------------------------

def collect_process_usage(interval=1):

    processes = analyze_processes(
        display=False,
        interval=interval
    )

    return processes


# -----------------------------------------
# 6. ENERGY ATTRIBUTION ENGINE
# -----------------------------------------

def calculate_attribution(
    processes,
    system_power,
    overhead_fraction=0.30,
    duration_seconds=1
):
    """
    Estimate process energy using relative CPU activity.

    This is a heuristic allocation, not direct
    per-process hardware power measurement.
    """

    if not 0 <= overhead_fraction <= 1:
        raise ValueError(
            "Overhead fraction must be between 0 and 1."
        )

    if duration_seconds <= 0:
        raise ValueError(
            "Duration must be greater than zero."
        )

    # Only attribute measured battery discharge.
    if system_power is None or system_power <= 0:
        return {
            "available": False,
            "reason": "No measurable battery discharge.",
            "system_power_watts": system_power,
            "system_overhead_watts": None,
            "process_power_watts": None,
            "processes": []
        }

    valid_processes = [
        process for process in processes
        if process.get("cpu", 0) > 0
    ]

    total_cpu = sum(
        process["cpu"] for process in valid_processes
    )

    if total_cpu <= 0:
        return {
            "available": False,
            "reason": "No measurable process CPU activity.",
            "system_power_watts": system_power,
            "system_overhead_watts": None,
            "process_power_watts": None,
            "processes": []
        }

    # Reserve part of system power for OS and hardware overhead.
    overhead_watts = system_power * overhead_fraction

    process_power = system_power * (1 - overhead_fraction)

    attributed_processes = []

    for process in valid_processes:

        cpu_share = process["cpu"] / total_cpu

        estimated_watts = process_power * cpu_share

        estimated_wh = calculate_energy_wh(
            estimated_watts,
            duration_seconds
        )

        attributed_processes.append({
            "pid": process["pid"],
            "name": process["name"],
            "cpu_percent": process["cpu"],
            "cpu_share_percent": cpu_share * 100,
            "estimated_watts": estimated_watts,
            "estimated_wh": estimated_wh
        })

    attributed_processes.sort(
        key=lambda item: item["estimated_watts"],
        reverse=True
    )

    return {
        "available": True,
        "reason": "CPU-weighted estimate",
        "system_power_watts": system_power,
        "system_overhead_watts": overhead_watts,
        "process_power_watts": process_power,
        "processes": attributed_processes
    }


# -----------------------------------------
# 7. GENERATE ENERGY REPORT
# -----------------------------------------

def generate_energy_report(
    interval=1,
    overhead_fraction=0.30
):

    # Collect process activity over the sampling interval.
    processes = collect_process_usage(interval)

    # Read battery telemetry after process sampling.
    battery = get_system_power()

    # Check whether battery discharge can be attributed.
    discharging = (
        battery["status"].lower() == "discharging"
        and battery["ac_connected"] is False
    )

    if discharging:
        attribution = calculate_attribution(
            processes,
            battery["power_watts"],
            overhead_fraction,
            interval
        )
    else:
        attribution = {
            "available": False,
            "reason": (
                "Battery is not confirmed to be discharging."
            ),
            "system_power_watts": battery["power_watts"],
            "system_overhead_watts": None,
            "process_power_watts": None,
            "processes": []
        }

    return {
        "battery": battery,
        "stored_energy": get_battery_energy(),
        "battery_health_percent": calculate_battery_health(),
        "system_energy_wh": (
            calculate_energy_wh(
                battery["power_watts"], interval
            )
            if discharging else None
        ),
        "attribution": attribution
    }


# -----------------------------------------
# 8. DISPLAY ENERGY REPORT
# -----------------------------------------

def display_energy_report(report):

    battery = report["battery"]
    attribution = report["attribution"]

    console.print(
        "\n[bold cyan]BATTERYSCOPE - ENERGY ATTRIBUTION REPORT[/bold cyan]\n"
    )

    console.print(f"Battery Status: {battery['status']}")
    console.print(f"AC Connected: {battery['ac_connected']}")
    console.print(f"Voltage: {battery['voltage']} V")
    console.print(f"Current: {battery['current']} A")
    console.print(f"Battery Power: {battery['power_watts']} W")

    console.print(
        f"Battery Health: {report['battery_health_percent']}%"
    )

    console.print(
        f"Stored Energy Estimate: "
        f"{report['stored_energy']['energy_wh_estimate']} Wh"
    )

    console.print(
        f"Measured Battery Energy (sample): "
        f"{report['system_energy_wh']} Wh"
    )

    if not attribution["available"]:

        console.print(
            f"\n[yellow]Process attribution unavailable: "
            f"{attribution['reason']}[/yellow]"
        )

        return

    console.print(
        f"\nSystem Overhead Estimate: "
        f"{attribution['system_overhead_watts']:.3f} W"
    )

    console.print(
        f"Allocated Process Power: "
        f"{attribution['process_power_watts']:.3f} W"
    )

    table = Table(
        title="PROCESS ENERGY ATTRIBUTION (ESTIMATED)"
    )

    table.add_column("PID", style="cyan")
    table.add_column("Process", style="green")
    table.add_column("CPU %", style="yellow")
    table.add_column("CPU Share", style="magenta")
    table.add_column("Estimated W", style="blue")
    table.add_column("Estimated Wh", style="white")

    for process in attribution["processes"][:10]:

        table.add_row(
            str(process["pid"]),
            process["name"][:22],
            f"{process['cpu_percent']:.1f}%",
            f"{process['cpu_share_percent']:.2f}%",
            f"{process['estimated_watts']:.4f}",
            f"{process['estimated_wh']:.8f}"
        )

    console.print(table)


# -----------------------------------------
# 9. MAIN EXECUTION
# -----------------------------------------

if __name__ == "__main__":

    report = generate_energy_report(
        interval=2,
        overhead_fraction=0.30
    )

    display_energy_report(report)
