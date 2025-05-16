@echo off
chcp 65001 > nul
echo [INFO] Cleaning up processes and lock files...

:: 删除锁文件
if exist schedule_server.lock (
    echo [INFO] Removing lock file...
    del /f /q schedule_server.lock
)

:: 使用 taskkill 直接终止所有 Python 进程
echo [INFO] Terminating Python processes...
taskkill /F /IM python.exe /T 2>nul

:: 使用 PowerShell 再次检查并确保清理
echo [INFO] Double checking with PowerShell...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Get-WmiObject Win32_Process -Filter \"name='python.exe'\" | Where-Object {$_.CommandLine -like '*schedule_server.py*' -or $_.CommandLine -like '*server.py*'} | ForEach-Object { $_.Terminate() }"

:: 等待进程完全终止
echo [INFO] Waiting for processes to terminate...
timeout /t 3 /nobreak > nul

echo [INFO] Cleanup completed! 