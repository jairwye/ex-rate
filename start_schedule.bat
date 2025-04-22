@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
python schedule_server.py
pause 