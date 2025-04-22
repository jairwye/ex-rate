@echo off
cd /d %~dp0

:: 获取当前目录的完整路径
set "CURRENT_DIR=%~dp0"
set "BAT_PATH=%CURRENT_DIR%start_schedule.bat"

:: 创建每天9点启动的任务
schtasks /create /tn "ExchangeRateServerStart" /tr "%BAT_PATH%" /sc daily /st 09:00 /f

:: 创建每天21点停止的任务
schtasks /create /tn "ExchangeRateServerStop" /tr "taskkill /f /im python.exe /fi \"WINDOWTITLE eq schedule_server.py\"" /sc daily /st 21:00 /f

echo 任务计划已设置完成！
echo 服务器将在每天9:00自动启动
echo 服务器将在每天21:00自动停止
pause 