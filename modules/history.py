
import csv
from pathlib import Path
from datetime import datetime

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

HISTORY_FILE = REPORT_DIR / "system_history.csv"


def save_snapshot(data):

    file_exists = HISTORY_FILE.exists()

    fields = [
        "timestamp",
        "cpu_percent",
        "ram_percent",
        "battery_percent",
        "voltage",
        "current",
        "power_watts",
        "top_process",
        "top_process_cpu",
        "top_process_ram"
    ]

    with open(HISTORY_FILE, "a", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        if not file_exists or HISTORY_FILE.stat().st_size == 0:
            writer.writeheader()

        row = {
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
            **data
        }

        writer.writerow(row)
