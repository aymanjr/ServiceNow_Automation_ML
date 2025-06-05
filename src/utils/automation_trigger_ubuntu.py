import os
import re
import subprocess
from datetime import datetime

# ========== Configuration ==========
project_root = "/root/n8n-docker/automation_project"
env_activate = os.path.join(project_root, "pyEnv310", "Scripts", "activate.bat")
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

# Build all commands into a single line to run in the same shell session
commands = [
    f'cd /d "{project_root}"',
    f'call "{env_activate}"',
    f'python src/classifier.py --predict "data/raw/{latest_file}" --output "data/processed/predictions.csv"',
    f'python src/utils/data_to_json.py --input data/processed/predictions.csv --start-date {start_date} --end-date {end_date}',
    f'python src/utils/charts.py --input data/processed/service_summary.json --csv data/processed/predictions.csv --output data/charts',
    f'python src/utils/visualization.py --input data/processed/service_summary.json --output data/reports/'
]

full_command = " && ".join(commands)

print("🚀 Starting automation...\n")
print(full_command)

result = subprocess.run(full_command, shell=True, capture_output=True, text=True)

print("\n📤 STDOUT:\n", result.stdout)
print("\n❗ STDERR:\n", result.stderr)
print("\n [✔]  Done.")
