FROM python:3.11-slim

WORKDIR /app

# 安装 psycopg 等依赖需要的系统库（如有多余可再精简）
RUN apt-get update && apt-get install -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 把整个 backend 拷进去
COPY . .

# Copy entrypoint that runs migrations before starting the app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 默认命令（实际会被 docker-compose 覆盖）
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]