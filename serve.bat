@echo off
rem TCM Inventory System - background server launcher
rem Auto migrate + seed demo data (idempotent), output to logs\server.log
setlocal
cd /d "%~dp0"
set "PYTHONPATH="
if not exist "logs" mkdir "logs"
echo. >> "logs\server.log"
echo [%date% %time%] ---- server starting ---- >> "logs\server.log"
".venv\Scripts\python.exe" manage.py migrate --noinput >> "logs\server.log" 2>&1
".venv\Scripts\python.exe" manage.py init_demo >> "logs\server.log" 2>&1
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload >> "logs\server.log" 2>&1
echo [%date% %time%] ---- server stopped ---- >> "logs\server.log"
endlocal
