@echo off
REM Run the RSS News Digest Pipeline Once (Fetch -> Analyze -> Summarize -> Deliver)

cd /d "%~dp0"
"%~dp0myenv\Scripts\python.exe" "%~dp0main.py"
"%~dp0myenv\Scripts\python.exe" "%~dp0analyzer.py"
"%~dp0myenv\Scripts\python.exe" "%~dp0summarizer.py"
"%~dp0myenv\Scripts\python.exe" "%~dp0delivery.py"
pause
