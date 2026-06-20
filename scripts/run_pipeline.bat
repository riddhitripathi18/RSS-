@echo off
REM Run the RSS News Digest Pipeline Once (Fetch -> Analyze -> Summarize -> Deliver)

cd /d "%~dp0.."
"%~dp0..\myenv\Scripts\python.exe" -c "from scripts.scheduler import run_daily_pipeline; run_daily_pipeline()"
pause
