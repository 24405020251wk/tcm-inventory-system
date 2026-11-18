@echo off
rem ============================================================
rem  Fallback watchdog (batch version).
rem  Use this only if the VBS guardian is blocked by policy.
rem  A console window must stay open; closing it stops the guard.
rem ============================================================
cd /d "%~dp0"
set "PYTHONPATH="
if not exist "logs" mkdir "logs"

echo Server watchdog started, checking port 8000 every 60 seconds.
echo Keep this window open. Log file: %~dp0logs\watchdog.log
echo.

:loop
set "UP="
for /f "delims=" %%L in ('netstat -ano -p tcp ^| findstr LISTENING') do (
    echo %%L | findstr /c:":8000 " >nul && set "UP=1"
)
if defined UP (
    >> "logs\watchdog.log" echo %date% %time%  OK
) else (
    >> "logs\watchdog.log" echo %date% %time%  DOWN -^> restarting
    start "" /b cmd /c serve.bat
)
rem ping is used as sleep: the timeout command fails in a non-interactive console
ping -n 61 127.0.0.1 >nul 2>&1
goto loop
