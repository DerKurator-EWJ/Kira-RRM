@echo off
cd /d "%~dp0"
py -3 discovery_cli.py
if errorlevel 1 python discovery_cli.py
pause
