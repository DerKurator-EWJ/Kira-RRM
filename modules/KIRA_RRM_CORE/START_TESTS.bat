@echo off
cd /d "%~dp0"
python -m unittest discover -p "test_*.py" -v
pause
