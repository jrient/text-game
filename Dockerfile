FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --retries 5 --timeout 60

# 复制后端代码
COPY backend/ ./backend/
# 复制前端代码
COPY frontend/ ./frontend/

# 设置工作目录为backend
WORKDIR /app/backend

ENV PORT=5000
ENV DEBUG=false
ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/textgame.db

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 5000

CMD ["python", "app.py"]
