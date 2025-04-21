@echo off
echo 正在启动汇率数据服务...

REM 激活虚拟环境
call .\venv\Scripts\activate

REM 检查是否已安装依赖
pip list | findstr "flask"
if %errorlevel% neq 0 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

REM 启动后端服务
start "后端服务" cmd /k "python server.py"

REM 等待3秒确保后端服务启动
timeout /t 3

REM 启动定时任务
start "定时任务" cmd /k "python scheduled_task.py"

echo 服务已启动！
echo 请在浏览器中打开 index.html 查看汇率走势图。
pause 