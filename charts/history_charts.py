
import csv
from pathlib import Path
import matplotlib.pyplot as plt

CSV_FILE = Path("reports/system_history.csv")


def load_history():

    if not CSV_FILE.exists():
        print("Historical data not found!")
        return []

    with open(CSV_FILE, "r") as file:
        reader = csv.DictReader(file)
        return list(reader)


def generate_charts():

    data = load_history()

    if not data:
        print("No historical readings available.")
        return

    timestamps = [row["timestamp"] for row in data]

    metrics = [
        ("cpu_percent", "CPU Usage (%)"),
        ("ram_percent", "RAM Usage (%)"),
        ("battery_percent", "Battery Level (%)"),
        ("power_watts", "Battery Power (W)")
    ]

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))

    fig.suptitle(
        "BATTERYSCOPE - SYSTEM ANALYTICS",
        fontsize=16,
        fontweight="bold"
    )

    for ax, (column, title) in zip(axes.flat, metrics):

        values = []

        for row in data:
            try:
                value = row[column]

                if value == "" or value is None:
                    values.append(float("nan"))
                else:
                    values.append(float(value))

            except (ValueError, KeyError):
                values.append(float("nan"))

        ax.plot(
            timestamps,
            values,
            marker="o",
            linewidth=2
        )

        ax.set_title(title)
        ax.set_xlabel("Time")
        ax.set_ylabel(title)
        ax.grid(True, alpha=0.3)

        ax.tick_params(axis="x", rotation=35)

    plt.tight_layout()

    output = Path("charts/system_analytics.png")

    plt.savefig(output, dpi=150)

    print(f"\nCharts saved successfully: {output}")

    plt.savefig(output, dpi=150)


if __name__ == "__main__":
    generate_charts()

