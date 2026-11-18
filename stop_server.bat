@echo off
rem Stops whatever process is listening on port 8000.
setlocal enabledelayedexpansion
set "FOUND="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":8000 "') do (
    taskkill /f /pid %%a >nul 2>&1
    if not errorlevel 1 (
        echo Stopped process PID %%a
        set "FOUND=1"
    )
)
if not defined FOUND echo Nothing is listening on port 8000.
echo.
rem Keep the window open when double-clicked, but stay silent when called with /q
if /i not "%~1"=="/q" pause
