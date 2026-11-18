#!/usr/bin/env bash
# ============================================================
# 公网部署启动脚本（平台会注入 PORT 环境变量）
#   migrate → 初始化演示数据（幂等） → 启动 HTTP 服务
# ============================================================
set -e

export DJANGO_DEBUG="${DJANGO_DEBUG:-1}"
export DJANGO_DYNAMIC_CSRF="${DJANGO_DYNAMIC_CSRF:-1}"
PORT="${PORT:-8000}"

python manage.py migrate --noinput
python manage.py init_demo || true

echo "[start] listening on 0.0.0.0:${PORT}"
exec python manage.py runserver "0.0.0.0:${PORT}" --noreload
