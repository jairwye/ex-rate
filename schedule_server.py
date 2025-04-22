import schedule
import time
import subprocess
import os
import signal
import sys
import logging
import requests
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_schedule.log'),
        logging.StreamHandler()
    ]
)

server_process = None

def start_server():
    global server_process
    if server_process is None or server_process.poll() is not None:
        try:
            # 激活虚拟环境并启动服务器
            activate_script = os.path.join('venv', 'Scripts', 'activate.bat')
            if os.path.exists(activate_script):
                server_process = subprocess.Popen(
                    f'call {activate_script} && python server.py',
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
                logging.info(f'服务器已启动，进程ID: {server_process.pid}')
            else:
                logging.error('找不到虚拟环境激活脚本')
        except Exception as e:
            logging.error(f'启动服务器时出错: {e}')
    else:
        logging.warning('服务器已经在运行中')

def stop_server():
    global server_process
    if server_process is not None and server_process.poll() is None:
        try:
            # 在Windows下，发送CTRL_BREAK_EVENT信号来终止进程组
            os.kill(server_process.pid, signal.CTRL_BREAK_EVENT)
            server_process.wait(timeout=5)  # 等待进程结束
            logging.info('服务器已停止')
        except Exception as e:
            logging.error(f'停止服务器时出错: {e}')
            # 如果无法正常停止，强制终止
            try:
                server_process.kill()
                logging.info('服务器已强制终止')
            except:
                pass
        server_process = None
    else:
        logging.warning('服务器未在运行')

def update_exchange_rate():
    # 检查是否为工作日（周一至周五）
    if datetime.now().weekday() < 5:  # 0-4 表示周一到周五
        try:
            response = requests.post('http://localhost:5000/api/update')
            if response.status_code == 200:
                logging.info('汇率数据更新成功')
            else:
                logging.error('汇率数据更新失败')
        except Exception as e:
            logging.error(f'更新汇率数据时出错: {e}')

def main():
    # 设置定时任务
    schedule.every().day.at("09:00").do(start_server)
    schedule.every().day.at("21:00").do(stop_server)
    schedule.every().day.at("10:10").do(update_exchange_rate)  # 在工作日10:10更新汇率数据
    
    logging.info('定时任务管理器已启动')
    
    # 如果当前时间在9:00-21:00之间，立即启动服务器
    current_time = datetime.now().time()
    if current_time.hour >= 9 and current_time.hour < 21:
        start_server()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logging.info('收到终止信号')
        stop_server()
        sys.exit(0)

if __name__ == '__main__':
    main() 