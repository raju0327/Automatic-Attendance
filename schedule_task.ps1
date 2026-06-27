# PowerShell script to register the attendance automation script in Windows Task Scheduler
# Run this script to schedule the automation daily at 09:00 AM.

$TaskName = "DailyAttendanceAutomation"
$BatPath = "C:\Users\Hp\.gemini\antigravity\scratch\attendance_automation\run_attendance.bat"

# Verify batch file exists
if (-not (Test-Path $BatPath)) {
    Write-Error "Batch file not found at $BatPath. Please make sure the path is correct."
    exit 1
}

Write-Host "Creating task action to execute: $BatPath"
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatPath`"" -WorkingDirectory "C:\Users\Hp\.gemini\antigravity\scratch\attendance_automation"

Write-Host "Creating daily trigger at 09:00 AM..."
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM

Write-Host "Configuring task settings..."
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Write-Host "Registering scheduled task '$TaskName'..."
try {
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -Description "Automates HRMS attendance check-in daily at 9:00 AM" -Force
    Write-Host "Successfully registered scheduled task! It will now run daily at 9:00 AM." -ForegroundColor Green
} catch {
    Write-Error "Failed to register scheduled task. Error details: $_"
    Write-Host "Tip: Try running this PowerShell script as Administrator if registration failed." -ForegroundColor Yellow
}
