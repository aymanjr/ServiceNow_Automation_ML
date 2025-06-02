$flagFile = "D:\Projects\ServiceNow_Automation_ML\run-now.txt"
$batFile  = "D:\Projects\ServiceNow_Automation_ML\run_automation.bat"

if (Test-Path $flagFile) {
    Remove-Item $flagFile
    Start-Process -FilePath $batFile
}
