from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import datetime
import requests
import json
import time

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# FRED API配置
FRED_API_KEY = 'd131118f59f8063c3eca49d9881d9fa5'  # 用户的API密钥
FRED_API_URL = 'https://api.stlouisfed.org/fred/series/observations'

# 数据库初始化函数
def init_db():
    conn = sqlite3.connect('exchange_rate.db')
    c = conn.cursor()
    # 创建汇率表，包含日期和汇率两个字段
    c.execute('''CREATE TABLE IF NOT EXISTS rates
                 (date TEXT PRIMARY KEY, rate REAL)''')
    conn.commit()
    conn.close()

# 获取FRED的美元兑人民币汇率数据
def get_fred_rate():
    try:
        # 获取当前日期
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        print(f"尝试获取{today}的汇率数据")
        
        # FRED API参数
        params = {
            'api_key': FRED_API_KEY,
            'series_id': 'DEXCHUS',  # 美元兑人民币汇率系列ID
            'observation_start': '2025-04-02',  # 开始日期
            'observation_end': today,  # 结束日期
            'file_type': 'json',
            'frequency': 'd',  # 使用'd'表示每日频率
            'output_type': 1  # 使用实际值而不是变化率
        }
        
        response = requests.get(FRED_API_URL, params=params)
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
        
        # 解析JSON响应
        data = response.json()
        observations = data.get('observations', [])
        
        if not observations:
            print("未获取到汇率数据")
            return None
        
        # 提取汇率数据
        rates = []
        for obs in observations:
            date = obs['date']
            try:
                rate = float(obs['value'])
                rates.append((date, rate))
                print(f"日期: {date}, 汇率: {rate}")
            except (ValueError, KeyError) as e:
                print(f"解析数据时出错: {e}")
                continue
        
        if not rates:
            print("未能提取到任何汇率数据")
            return None
            
        return rates
            
    except Exception as e:
        print(f"获取汇率数据失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return None

# 初始化历史数据
def init_historical_data():
    conn = sqlite3.connect('exchange_rate.db')
    c = conn.cursor()
    
    # 清空现有数据
    c.execute("DELETE FROM rates")
    conn.commit()
    print("已清空现有数据")
    
    # 获取历史数据
    rates = get_fred_rate()
    if rates:
        # 插入历史数据
        c.executemany("INSERT INTO rates (date, rate) VALUES (?, ?)", rates)
        conn.commit()
        print(f"已插入{len(rates)}条历史数据")
    else:
        print("未能获取历史数据")
    
    conn.close()

# 更新数据库中的汇率数据
def update_rate():
    conn = sqlite3.connect('exchange_rate.db')
    c = conn.cursor()
    
    # 获取当前日期
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    rates = get_fred_rate()
    
    if rates:
        # 更新所有数据
        c.executemany("INSERT OR REPLACE INTO rates (date, rate) VALUES (?, ?)", rates)
        conn.commit()
        print(f"已更新{len(rates)}条汇率数据")
    else:
        print(f"未能获取{today}的汇率数据")
    
    conn.close()

# 获取历史汇率数据
def get_historical_rates():
    conn = sqlite3.connect('exchange_rate.db')
    c = conn.cursor()
    
    # 获取所有数据，按日期排序
    c.execute("SELECT date, rate FROM rates ORDER BY date")
    data = c.fetchall()
    
    # 打印调试信息
    print("数据库中的数据：")
    for row in data:
        print(f"日期: {row[0]}, 汇率: {row[1]}")
    
    conn.close()
    
    # 将数据转换为前端需要的格式
    dates = [row[0] for row in data]
    rates = [row[1] for row in data]
    
    return {'dates': dates, 'rates': rates}

# API路由：获取所有汇率数据
@app.route('/api/rates', methods=['GET'])
def get_rates():
    return jsonify(get_historical_rates())

# API路由：更新汇率数据
@app.route('/api/update', methods=['POST'])
def update_rates():
    update_rate()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_db()  # 初始化数据库
    init_historical_data()  # 初始化历史数据
    app.run(debug=True, port=5000)  # 启动服务器 