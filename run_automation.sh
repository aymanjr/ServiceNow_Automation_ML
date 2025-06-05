#!/bin/bash
# Script to trigger the automation Python script

# Navigate to the project directory (optional, but good practice if the script relies on relative paths)
# cd /root/n8n-docker/automation_project

# Execute the Python script
# Replace 'python3' with the specific path to your Python interpreter if needed (e.g., /root/n8n-docker/automation_project/pyEnv/bin/python)
python src/utils/automation_trigger_ubuntu.py

echo "Automation script triggered."
