while ($true) {
    if (Test-Path "D:\Projects\ServiceNow_Automation_ML\run-now.txt") {
        Remove-Item "D:\Projects\ServiceNow_Automation_ML\run-now.txt"
        Start-Process -FilePath "D:\Projects\ServiceNow_Automation_ML\run_automation.bat"
        Write-Host "Batch file executed at $(Get-Date)"
    }
    Start-Sleep -Seconds 5
}
