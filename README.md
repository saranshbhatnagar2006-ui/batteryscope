## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd BatteryScope
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

### 3. Activate the Virtual Environment

**Linux / Fedora / Ubuntu:**

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Running BatteryScope

Run commands from the main `BatteryScope` project directory.

### 1. System Information Dashboard

```bash
python main.py
```

### 2. Live System Monitoring

```bash
python -m modules.monitor
```

Displays live system information, including:

- CPU usage
- RAM usage
- Battery percentage
- Battery voltage and current
- Estimated battery power
- Top resource-consuming processes

Press `Ctrl + C` to stop live monitoring.

### 3. Energy Attribution Report

```bash
python -m modules.energy
```

Provides battery information and CPU-weighted process-level energy estimates when battery discharge measurements are available.

### 4. Process Monitoring

```bash
python -m modules.processes
```

Displays running processes and their resource usage, if the module supports direct execution.

### 5. Generate System Analytics Charts

```bash
python -m charts.history_charts
```

If the chart is generated successfully, open it using:

```bash
xdg-open charts/system_analytics.png
```

## Project Notes

- BatteryScope currently targets Linux systems.
- Battery telemetry depends on hardware and Linux power-supply interfaces.
- Process-level energy attribution uses an estimation model, not direct per-process power measurements.
- Some battery measurements may be unavailable when the laptop is connected to AC power.

## Deactivating the Virtual Environment

When finished:

```bash
deactivate
```
