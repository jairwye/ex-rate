from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import datetime
import requests
import json
import time
from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__, static_folder='.')
CORS(app, resources={r"/*": {"origins": "*"}})  # 允许所有来源的跨域请求

# 从环境变量获取配置
PORT = int(os.getenv('PORT', 5000))
HOST = os.getenv('HOST', '0.0.0.0')
DB_PATH = os.getenv('DB_PATH', 'exchange_rate.db')

# 汇率API配置
EXCHANGE_API_SOURCES = [
    'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@',
    'https://{date}.currency-api.pages.dev/v1/currencies/{currency}.json',
    'https://api.exchangerate-api.com/v4/latest/USD',
    'https://api.exchangerate.host/latest?base=USD'
]

# 数据库初始化
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # 创建汇率表
        c.execute('''CREATE TABLE IF NOT EXISTS rates
                     (date TEXT PRIMARY KEY, rate REAL, is_final INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")

# 获取美元兑人民币汇率数据
def get_exchange_rate(date=None):
    try:
        if date is None:
            date = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"尝试获取{date}的汇率数据")
        
        # 首先检查数据库中是否已有最终数据
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT rate FROM rates WHERE date = ? AND is_final = 1", (date,))
        result = c.fetchone()
        conn.close()
        
        if result:
            print(f"从数据库获取到最终数据：日期: {date}, 汇率: {result[0]}")
            return [(date, result[0])]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        
        # 尝试所有API源
        for api_source in EXCHANGE_API_SOURCES:
            try:
                if 'cdn.jsdelivr.net' in api_source:
                    api_url = f"{api_source}{date}/v1/currencies/usd.json"
                elif 'currency-api.pages.dev' in api_source:
                    api_url = api_source.format(date=date, currency='usd')
                else:
                    api_url = api_source
                
                print(f"尝试访问API: {api_url}")
                response = requests.get(api_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 根据不同API的响应格式处理数据
                    if 'cdn.jsdelivr.net' in api_url or 'currency-api.pages.dev' in api_url:
                        if isinstance(data, dict) and 'usd' in data and 'cny' in data['usd']:
                            rate = float(data['usd']['cny'])
                    elif 'exchangerate-api.com' in api_url:
                        if 'rates' in data and 'CNY' in data['rates']:
                            rate = float(data['rates']['CNY'])
                    elif 'exchangerate.host' in api_url:
                        if 'rates' in data and 'CNY' in data['rates']:
                            rate = float(data['rates']['CNY'])
                    else:
                        continue
                    
                    if rate > 0:
                        print(f"从API获取到数据：日期: {date}, 汇率: {rate}")
                        return [(date, rate)]
                        
            except Exception as e:
                print(f"API请求失败 ({api_source}): {e}")
                continue
        
        raise Exception("所有API源都请求失败")
            
    except Exception as e:
        print(f"获取汇率数据失败: {e}")
        return None

# 将当天数据标记为最终数据
def finalize_today_data():
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"开始将{today}的数据标记为最终数据")
        
        # 获取当天最新数据
        rates = get_exchange_rate(today)
        if not rates:
            print(f"未能获取{today}的数据，无法标记为最终数据")
            return
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 更新数据并标记为最终数据
        c.execute("INSERT OR REPLACE INTO rates (date, rate, is_final) VALUES (?, ?, 1)", (today, rates[0][1]))
        conn.commit()
        conn.close()
        
        print(f"已将{today}的数据标记为最终数据")
    except Exception as e:
        print(f"标记最终数据失败: {e}")

# 更新当天数据（不标记为最终）
def update_today_rate():
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        rates = get_exchange_rate(today)
        
        if rates:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # 只更新非最终数据
            c.execute("INSERT OR REPLACE INTO rates (date, rate, is_final) VALUES (?, ?, 0)", (today, rates[0][1]))
            conn.commit()
            conn.close()
            print(f"已更新{today}的实时数据")
    except Exception as e:
        print(f"更新今日数据失败: {e}")

# 获取历史汇率数据
def get_historical_rates():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 获取所有数据，按日期排序
        c.execute("SELECT date, rate FROM rates ORDER BY date")
        data = c.fetchall()
        
        conn.close()
        
        dates = [row[0] for row in data]
        rates = [row[1] for row in data]
        
        return {'dates': dates, 'rates': rates}
    except Exception as e:
        print(f"获取历史数据失败: {e}")
        return {'dates': [], 'rates': []}

# 静态文件路由
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)

# API路由：获取所有汇率数据
@app.route('/api/rates', methods=['GET'])
def get_rates():
    return jsonify(get_historical_rates())

# API路由：更新今日汇率数据
@app.route('/api/update', methods=['POST'])
def update_rates():
    update_today_rate()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_db()  # 初始化数据库
    
    # 获取历史数据（如果数据库为空）
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM rates")
    count = c.fetchone()[0]
    conn.close()
    
    if count == 0:
        print("\n数据库为空，开始获取历史数据...")
        start_date = datetime.datetime(2024, 4, 2)
        end_date = datetime.datetime.now()
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            print(f"\n正在获取{date_str}的数据...")
            rates = get_exchange_rate(date_str)
            if rates:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                # 将历史数据标记为最终数据
                c.execute("INSERT OR REPLACE INTO rates (date, rate, is_final) VALUES (?, ?, 1)", 
                         (date_str, rates[0][1]))
                conn.commit()
                conn.close()
                print(f"已保存{date_str}的数据")
            current_date += datetime.timedelta(days=1)
            time.sleep(1)
    
    # 设置定时任务
    scheduler = BackgroundScheduler()
    # 每天20:00将当天数据标记为最终数据
    scheduler.add_job(finalize_today_data, 'cron', hour=20, minute=0)
    # 每小时更新一次当天实时数据
    scheduler.add_job(update_today_rate, 'interval', hours=1)
    scheduler.start()
    
    # 启动服务器
    app.run(debug=True, port=PORT, host=HOST) 