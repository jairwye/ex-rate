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
- 定时任务：APScheduler
- 容器化：Docker

## 安装和使用

### 使用 Docker 部署（推荐）

1. 克隆仓库：
```bash
git clone https://github.com/jairwye/ex-rate.git
cd ex-rate
```

2. 构建并启动服务：
```bash
docker-compose up --build
```

3. 在后台运行：
```bash
docker-compose up -d
```

4. 停止服务：
```bash
docker-compose down
```

### 手动部署

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

4. 启动服务器：
```bash
python server.py
```

## 自动化功能

- 每小时自动更新汇率数据
- 每天 20:00 将当天数据标记为最终数据
- 自动检查并补充历史数据

## 访问应用

启动服务后，访问：
- http://localhost:9088

## 数据来源

- fawazahmed0/currency-api
- exchangerate-api.com
- exchangerate.host

# 汇率走势图

一个实时显示美元、欧元、日元兑人民币汇率的可视化工具。

## 版本历史

### v1.2 (2024-03-21)
- 支持 Docker 容器化部署
- 优化服务架构，分离 Web 和调度器服务
- 改进数据持久化方案
- 更新端口为 9088
- 完善部署文档

### v1.1 (2024-03-21)
- 优化了图表切换动画效果
- 实现了全屏图表显示
- 改进了页面布局和标题显示
- 优化了背景渐变效果
- 提升了整体视觉体验

### v1.0 (2024-03-20)
- 初始版本发布
- 支持实时汇率数据获取
- 提供美元、欧元、日元三种货币的汇率走势图
- 自动定时更新数据
- 支持图表切换和交互 