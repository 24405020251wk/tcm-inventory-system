FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_DYNAMIC_CSRF=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HF Spaces / Render / Railway 等平台通过 PORT 环境变量指定端口
ENV PORT=7860
EXPOSE 7860

# 迁移 → 初始化演示数据（幂等）→ 启动
RUN python manage.py migrate --noinput && python manage.py init_demo || true

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:$PORT --noreload"]
