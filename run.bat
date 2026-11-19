@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONPATH="
set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [ERROR] Virtual environment not found: .venv\Scripts\python.exe
    echo Please create it first: python -m venv .venv
    pause
    exit /b 1
)

echo [1/2] Applying database migrations...
"%PYTHON%" manage.py migrate --noinput
if errorlevel 1 (
    echo [ERROR] migrate failed.
    pause
    exit /b 1
)

echo [2/3] Seeding demo data (idempotent, skips if data exists)...
"%PYTHON%" manage.py init_demo
if errorlevel 1 (
    echo [ERROR] init_demo failed.
    pause
    exit /b 1
)

echo [3/3] Starting dev server at http://127.0.0.1:8000
start "" "http://127.0.0.1:8000/accounts/login/"
"%PYTHON%" manage.py runserver 127.0.0.1:8000

echo.
echo Server stopped.
pause
