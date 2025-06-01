@echo off
cd /d D:\Projects\ServiceNow_Automation_ML

REM Activate your virtual environment
call pyEnv310\Scripts\activate.bat

REM Run the automation
python src\utils\automation_trigger.py

pause
