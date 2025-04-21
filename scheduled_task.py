import schedule
import time
import requests
import datetime

def update_exchange_rate():
    # 检查是否为工作日（周一至周五）
    if datetime.datetime.now().weekday() < 5:  # 0-4 表示周一到周五
        try:
            response = requests.post('http://localhost:5000/api/update')
            if response.status_code == 200:
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 汇率数据更新成功")
            else:
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 汇率数据更新失败")
        except Exception as e:
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 更新出错: {str(e)}")

# 设置每天10:10执行更新
schedule.every().day.at("10:10").do(update_exchange_rate)

print("定时任务已启动，将在每个工作日10:10更新汇率数据...")

while True:
    schedule.run_pending()
    time.sleep(60)  # 每分钟检查一次 