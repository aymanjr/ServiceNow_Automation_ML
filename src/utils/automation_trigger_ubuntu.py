import os
import re
import subprocess
from datetime import datetime

# ========== Configuration ==========
project_root = "/root/n8n-docker/automation_project" # This is already set by cd in run_automation.sh
raw_data_path = os.path.join(project_root, "data", "raw")
processed_data_path = os.path.join(project_root, "data", "processed")
# ===================================

# Search for the latest matching file
pattern = r"unlabeled_tickets__Start_(\d{4}_\d{2}_\d{2})_End_(\d{4}_\d{2}_\d{2})\.csv"
latest_file = None
latest_mtime = 0

for file in os.listdir(raw_data_path):
    match = re.match(pattern, file)
    if match:
        full_path = os.path.join(raw_data_path, file)
        mtime = os.path.getmtime(full_path)
        if mtime > latest_mtime:
            latest_mtime = mtime
            latest_file = file
            start_date = match.group(1).replace("_", "-")
            end_date = match.group(2).replace("_", "-")

if not latest_file:
    print(" No valid input file found.")
    exit(1)

# Define the Python executable from the virtual environment
# This assumes run_automation.sh has set up the environment or is calling this script
# with the environment's python.
# If run_automation.sh uses /root/n8n-docker/automation_project/pyEnv310/bin/python,
# then just 'python' might be sufficient here if that env is active,
# or you can be explicit if needed, but it's better handled by the calling shell script.
# For simplicity, we'll assume the calling shell script uses the correct python interpreter.
python_executable = "python" # Or the specific path if needed, but ideally inherited

# Build all commands into a single line
# The 'cd' command is removed as run_automation.sh should handle the CWD.
# The environment activation is removed as run_automation.sh should handle it.
commands = [
    f'{python_executable} src/classifier.py --predict "data/raw/{latest_file}" --output "data/processed/predictions.csv"',
    f'{python_executable} src/utils/data_to_json.py --input data/processed/predictions.csv --start-date {start_date} --end-date {end_date}',
    f'{python_executable} src/utils/charts.py --input data/processed/service_summary.json --csv data/processed/predictions.csv --output data/charts',
    f'{python_executable} src/utils/visualization.py --input data/processed/service_summary.json --output data/reports/'
]

full_command = " && ".join(commands)

print("🚀 Starting automation...\n")
print(f"Executing from: {os.getcwd()}")
print(f"Command: {full_command}")

# Execute the command
# Note: It's generally better for run_automation.sh to call these scripts sequentially
# rather than chaining them with '&&' inside a Python subprocess call.
# This simplifies error handling and environment management.
result = subprocess.run(full_command, shell=True, capture_output=True, text=True, executable='/bin/bash')


print("\n📤 STDOUT:\n", result.stdout)
if result.stderr:
    print("\n❗ STDERR:\n", result.stderr)
print("\n [✔]  Done.")
