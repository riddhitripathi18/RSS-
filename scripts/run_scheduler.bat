@echo off
REM Run the RSS News Digest System Scheduler
REM This script properly uses the virtual environment

cd /d "%~dp0.."
"%~dp0..\myenv\Scripts\python.exe" "%~dp0scheduler.py"
pause
