@echo off
cd /d "%~dp0"
py -3 hypothesis_cli.py
if errorlevel 1 python hypothesis_cli.py
pause
