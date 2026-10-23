@echo off
cd /d "%~dp0"
py -3 compression_cli.py
if errorlevel 1 python compression_cli.py
pause
