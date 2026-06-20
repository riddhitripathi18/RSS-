# Run the RSS News Digest System Scheduler
# This script properly uses the virtual environment

Set-Location $PSScriptRoot\..
& "$PSScriptRoot\..\myenv\Scripts\python.exe" "$PSScriptRoot\scheduler.py"
