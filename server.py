# -*- coding: utf-8 -*-
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
    'https://{date}.currency-api.pages.dev/v1/currencies/{currency}.json'
]

# 数据库初始化
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # 创建汇率表，增加eur和jpy字段
        c.execute('''CREATE TABLE IF NOT EXISTS rates
                     (date TEXT PRIMARY KEY, 
                      usd_rate REAL, 
                      eur_rate REAL,
                      jpy_rate REAL,
                      is_final INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")

# 获取汇率数据
def get_exchange_rate(date=None, currency='usd'):
    try:
        if date is None:
            date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        print(f"尝试获取{date}的{currency.upper()}汇率数据")
        
        # 首先检查数据库中是否已有最终数据
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"SELECT {currency}_rate FROM rates WHERE date = ? AND is_final = 1", (date,))
        result = c.fetchone()
        conn.close()
        
        if result and result[0] is not None:
            print(f"从数据库获取到最终数据：日期: {date}, {currency.upper()}汇率: {result[0]}")
            return [(date, result[0])]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        
        # 尝试所有API源
        for api_source in EXCHANGE_API_SOURCES:
            try:
                if 'cdn.jsdelivr.net' in api_source:
                    api_url = f"{api_source}{date}/v1/currencies/{currency}.json"
                elif 'currency-api.pages.dev' in api_source:
                    api_url = api_source.format(date=date, currency=currency)
                
                print(f"尝试访问API: {api_url}")
                response = requests.get(api_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"API响应数据: {data}")
                    
                    # 根据API文档处理数据
                    if isinstance(data, dict):
                        if currency in data and 'cny' in data[currency]:
                            rate = float(data[currency]['cny'])
                            if rate > 0:
                                print(f"从API获取到数据：日期: {date}, {currency.upper()}汇率: {rate}")
                                return [(date, rate)]
                        else:
                            print(f"API响应数据格式不正确，缺少{currency}或cny字段: {data}")
                    else:
                        print(f"API响应数据不是字典格式: {data}")
                        
            except Exception as e:
                print(f"API请求失败 ({api_source}): {e}")
                continue
        
        print(f"所有API源都请求失败，日期: {date}, 货币: {currency}")
        return None
            
    except Exception as e:
        print(f"获取汇率数据失败: {e}")
        return None

# 更新当天数据（不标记为最终）
def update_today_rate():
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 获取所有货币的汇率
        usd_rates = get_exchange_rate(today, 'usd')
        eur_rates = get_exchange_rate(today, 'eur')
        jpy_rates = get_exchange_rate(today, 'jpy')
        
        if usd_rates or eur_rates or jpy_rates:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # 准备SQL语句
            sql = "INSERT OR REPLACE INTO rates (date, usd_rate, eur_rate, jpy_rate, is_final) VALUES (?, ?, ?, ?, 0)"
            values = [today, None, None, None]
            
            # 更新各个货币的汇率
            if usd_rates:
                values[1] = usd_rates[0][1]
            if eur_rates:
                values[2] = eur_rates[0][1]
            if jpy_rates:
                values[3] = jpy_rates[0][1]
            
            c.execute(sql, values)
            conn.commit()
            conn.close()
            print(f"已更新{today}的实时数据")
            
            # 同时检查历史数据完整性
            check_and_fill_historical_data()
    except Exception as e:
        print(f"更新今日数据失败: {e}")

# 将当天数据标记为最终数据
def finalize_today_data():
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"开始将{today}的数据标记为最终数据")
        
        # 获取当天最新数据
        usd_rates = get_exchange_rate(today, 'usd')
        eur_rates = get_exchange_rate(today, 'eur')
        jpy_rates = get_exchange_rate(today, 'jpy')
        
        if usd_rates or eur_rates or jpy_rates:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # 准备SQL语句
            sql = "INSERT OR REPLACE INTO rates (date, usd_rate, eur_rate, jpy_rate, is_final) VALUES (?, ?, ?, ?, 1)"
            values = [today, None, None, None]
            
            # 更新各个货币的汇率
            if usd_rates:
                values[1] = usd_rates[0][1]
            if eur_rates:
                values[2] = eur_rates[0][1]
            if jpy_rates:
                values[3] = jpy_rates[0][1]
            
            c.execute(sql, values)
            conn.commit()
            conn.close()
            
            print(f"已将{today}的数据标记为最终数据")
    except Exception as e:
        print(f"标记最终数据失败: {e}")

# 获取历史汇率数据
def get_historical_rates():
    try:
        # 首先获取当天的实时数据
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"获取当天({today})的实时数据...")
        
        # 获取所有货币的汇率
        usd_rates = get_exchange_rate(today, 'usd')
        eur_rates = get_exchange_rate(today, 'eur')
        jpy_rates = get_exchange_rate(today, 'jpy')
        
        if usd_rates or eur_rates or jpy_rates:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # 准备SQL语句
            sql = "INSERT OR REPLACE INTO rates (date, usd_rate, eur_rate, jpy_rate, is_final) VALUES (?, ?, ?, ?, 0)"
            values = [today, None, None, None]
            
            # 更新各个货币的汇率
            if usd_rates:
                values[1] = usd_rates[0][1]
            if eur_rates:
                values[2] = eur_rates[0][1]
            if jpy_rates:
                values[3] = jpy_rates[0][1]
            
            c.execute(sql, values)
            conn.commit()
            conn.close()
            print(f"已更新当天({today})的实时数据")
        
        # 获取所有历史数据
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT date, usd_rate, eur_rate, jpy_rate FROM rates ORDER BY date")
        data = c.fetchall()
        conn.close()
        
        dates = [row[0] for row in data]
        usd_rates = [row[1] for row in data]
        eur_rates = [row[2] for row in data]
        jpy_rates = [row[3] for row in data]
        
        return {
            'dates': dates,
            'usd_rates': usd_rates,
            'eur_rates': eur_rates,
            'jpy_rates': jpy_rates
        }
    except Exception as e:
        print(f"获取历史数据失败: {e}")
        return {'dates': [], 'usd_rates': [], 'eur_rates': [], 'jpy_rates': []}

# 检查并补充历史数据
def check_and_fill_historical_data():
    try:
        print("\n开始检查历史数据完整性...")
        # 获取昨天的日期
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        start_date = datetime.datetime(2025, 4, 2)
        end_date = yesterday  # 只检查到昨天
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 获取所有已存在的数据
        c.execute("SELECT date, usd_rate, eur_rate, jpy_rate FROM rates WHERE date <= ?", (yesterday.strftime('%Y-%m-%d'),))
        existing_data = {row[0]: {'usd': row[1], 'eur': row[2], 'jpy': row[3]} for row in c.fetchall()}
        
        print(f"已存在的数据日期: {sorted(list(existing_data.keys()))}")
        
        # 检查每一天的数据
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            needs_update = False
            values = [date_str, None, None, None]
            
            if date_str not in existing_data:
                print(f"\n发现缺失日期：{date_str}，开始获取所有货币数据...")
                needs_update = True
            else:
                # 检查每个货币的数据是否存在
                if existing_data[date_str]['usd'] is None:
                    print(f"\n发现{date_str}的USD数据缺失，尝试获取...")
                    needs_update = True
                if existing_data[date_str]['eur'] is None:
                    print(f"\n发现{date_str}的EUR数据缺失，尝试获取...")
                    needs_update = True
                if existing_data[date_str]['jpy'] is None:
                    print(f"\n发现{date_str}的JPY数据缺失，尝试获取...")
                    needs_update = True
            
            if needs_update:
                # 获取所有货币的汇率
                usd_rates = get_exchange_rate(date_str, 'usd')
                eur_rates = get_exchange_rate(date_str, 'eur')
                jpy_rates = get_exchange_rate(date_str, 'jpy')
                
                # 如果日期已存在，保留现有的非空值
                if date_str in existing_data:
                    values[1] = existing_data[date_str]['usd']
                    values[2] = existing_data[date_str]['eur']
                    values[3] = existing_data[date_str]['jpy']
                
                # 更新缺失的汇率
                if usd_rates:
                    values[1] = usd_rates[0][1]
                if eur_rates:
                    values[2] = eur_rates[0][1]
                if jpy_rates:
                    values[3] = jpy_rates[0][1]
                
                # 只有在有新数据时才更新数据库
                if any(v is not None for v in values[1:]):
                    c.execute("INSERT OR REPLACE INTO rates (date, usd_rate, eur_rate, jpy_rate, is_final) VALUES (?, ?, ?, ?, 1)", values)
                    conn.commit()
                    print(f"已更新{date_str}的数据: USD={values[1]}, EUR={values[2]}, JPY={values[3]}")
                else:
                    print(f"未能获取{date_str}的任何新数据")
            
            current_date += datetime.timedelta(days=1)
            time.sleep(1)  # 避免请求过于频繁
        
        conn.close()
        print("历史数据完整性检查完成")
    except Exception as e:
        print(f"检查历史数据完整性时出错: {e}")

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
        # 获取昨天的日期
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        start_date = datetime.datetime(2025, 4, 2)
        end_date = yesterday
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            print(f"\n正在获取{date_str}的数据...")
            
            # 获取所有货币的汇率
            usd_rates = get_exchange_rate(date_str, 'usd')
            eur_rates = get_exchange_rate(date_str, 'eur')
            jpy_rates = get_exchange_rate(date_str, 'jpy')
            
            if usd_rates or eur_rates or jpy_rates:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                # 将历史数据标记为最终数据
                sql = "INSERT OR REPLACE INTO rates (date, usd_rate, eur_rate, jpy_rate, is_final) VALUES (?, ?, ?, ?, 1)"
                values = [date_str, None, None, None]
                
                # 更新各个货币的汇率
                if usd_rates:
                    values[1] = usd_rates[0][1]
                if eur_rates:
                    values[2] = eur_rates[0][1]
                if jpy_rates:
                    values[3] = jpy_rates[0][1]
                
                c.execute(sql, values)
                conn.commit()
                conn.close()
                print(f"已保存{date_str}的数据")
            else:
                print(f"未能获取{date_str}的数据")
            current_date += datetime.timedelta(days=1)
            time.sleep(1)  # 避免请求过于频繁
    
    # 检查并补充历史数据（只检查到昨天）
    check_and_fill_historical_data()
    
    # 设置定时任务
    scheduler = BackgroundScheduler()
    # 每天20:00将当天数据标记为最终数据
    scheduler.add_job(finalize_today_data, 'cron', hour=20, minute=0)
    # 每小时更新一次当天实时数据，同时检查历史数据完整性
    scheduler.add_job(update_today_rate, 'interval', hours=1)
    scheduler.start()
    
    # 启动服务器
    app.run(debug=True, port=PORT, host=HOST)