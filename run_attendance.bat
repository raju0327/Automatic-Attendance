@echo off
cd /d "C:\Users\Hp\.gemini\antigravity\scratch\attendance_automation"
echo ========================================= >> attendance_log.txt
echo Execution Time: %date% %time% >> attendance_log.txt
echo Running Attendance Automation... >> attendance_log.txt

python automate_attendance.py --action auto --headless >> attendance_log.txt 2>&1

echo Done. Exit Code: %errorlevel% >> attendance_log.txt
echo ========================================= >> attendance_log.txt
