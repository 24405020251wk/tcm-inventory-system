@echo off
rem TCM Inventory System - background server launcher
rem Output is written to logs\server.log instead of the console.
cd /d "%~dp0"
set "PYTHONPATH="
if not exist "logs" mkdir "logs"
echo. >> "logs\server.log"
echo [%date% %time%] ---- server starting ---- >> "logs\server.log"
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload >> "logs\server.log" 2>&1
echo [%date% %time%] ---- server stopped ---- >> "logs\server.log"
