# 美元兑人民币汇率监控系统

这是一个用于监控和展示美元兑人民币汇率的 Web 应用程序。

## 功能特点

- 自动获取美元兑人民币汇率数据
- 美观的图表展示
- 支持历史数据查询
- 自动定时更新
- 数据本地存储

## 技术栈

- 后端：Python Flask
- 前端：HTML5, ECharts
- 数据库：SQLite
- 定时任务：Schedule

## 安装和使用

1. 克隆仓库：
```bash
git clone https://github.com/jairwye/ex-rate.git
cd ex-rate
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 设置自动运行（Windows）：
```bash
.\setup_schedule.bat
```

5. 手动启动服务器：
```bash
.\start_schedule.bat
```

## 自动化功能

- 每天 9:00 自动启动服务器
- 每天 21:00 自动停止服务器
- 每个工作日 10:10 自动更新汇率数据

## 访问应用

启动服务器后，访问：
- http://localhost:5000

## 数据来源

- fawazahmed0/currency-api
- exchangerate-api.com
- exchangerate.host 