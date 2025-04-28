# 使用官方 Python 运行时作为父镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY server.py .
COPY schedule_server.py .
COPY index.html .
COPY js/ ./js/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 9088

# 启动命令
CMD ["python", "server.py"] 