@echo off
chcp 65001 > nul
cd /d %~dp0

echo [INFO] Starting schedule server...

:: 先运行清理脚本
call cleanup.bat

:: 检查虚拟环境
if not exist venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)

:: 激活虚拟环境并启动服务器
echo [INFO] Activating virtual environment and starting server...
call venv\Scripts\activate.bat

:: 使用 PowerShell 启动服务器，避免编码问题
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "& {. venv\Scripts\activate.ps1; python schedule_server.py}"

:: 检查退出状态
if errorlevel 1 (
    echo [ERROR] Server exited with error! Check server_schedule.log for details.
    pause
    exit /b 1
) 