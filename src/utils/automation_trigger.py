import os
import re
import subprocess
from datetime import datetime

# ========== Configuration ==========
project_root = r"D:\Projects\ServiceNow_Automation_ML"
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
    print("❌ No valid input file found.")
    exit(1)

# Commands to run
commands = [
    f'cd /d "{project_root}"',
    f'call {env_activate}',
    f'python src/classifier.py --predict "data/raw/{latest_file}" --output "data/processed/predictions.csv"',
    f'python src/utils/data_to_json.py --input data/processed/predictions.csv --start-date {start_date} --end-date {end_date}',
    f'python src/utils/charts.py --input data/processed/service_summary.json --csv data/processed/predictions.csv --output data/charts',
    f'python src/utils/visualization.py --input data/processed/service_summary.json --output data/reports/'
]

print("🚀 Starting automation...")
for cmd in commands:
    print(f"\n➡ Running: {cmd}")
    subprocess.run(cmd, shell=True)

print("\n✅ Done.")
