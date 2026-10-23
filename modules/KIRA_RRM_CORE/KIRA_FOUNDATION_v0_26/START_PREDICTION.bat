@echo off
cd /d "%~dp0"
py -3 live_cli.py
if errorlevel 1 pause
