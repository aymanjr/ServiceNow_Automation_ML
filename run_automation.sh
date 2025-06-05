#!/bin/bash

cd /root/n8n-docker/automation_project

# Optional Git pull
git pull origin main

# Run automation using specific Python
/root/n8n-docker/automation_project/pyEnv310/Scripts/python.exe src/utils/automation_trigger_ubuntu.py

echo "Automation script triggered."
