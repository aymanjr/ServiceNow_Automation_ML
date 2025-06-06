#!/bin/bash

echo "🚀 Starting automation..."

project_root="/app/data"

latest_file=$(ls -t "$project_root/data/raw/"unlabeled_tickets__*.csv | head -n 1)
start_date=$(echo "$latest_file" | grep -oP 'Start_\K[0-9_]+')
end_date=$(echo "$latest_file" | grep -oP 'End_\K[0-9_]+')
start_date=${start_date//_/-}
end_date=${end_date//_/-}

cmds="
cd \"$project_root\" &&
python3 src/classifier.py --predict \"data/raw/$(basename "$latest_file")\" --output \"data/processed/predictions.csv\" &&
python3 src/utils/data_to_json.py --input data/processed/predictions.csv --start-date $start_date --end-date $end_date &&
python3 src/utils/charts.py --input data/processed/service_summary.json --csv data/processed/predictions.csv --output data/charts &&
python3 src/utils/visualization.py --input data/processed/service_summary.json --output data/reports/
"

echo -e "📦 Commands to run:\n$cmds"

eval "$cmds"
echo "[✔] Done."
