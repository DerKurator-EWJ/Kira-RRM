@echo off
cd /d "%~dp0"
py -3 partial_routing_cli.py
if errorlevel 1 python partial_routing_cli.py
pause
