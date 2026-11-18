@echo off
rem ============================================================
rem  Double-click: start the server in the background,
rem  start the watchdog, then open the browser.
rem  No console window stays open.
rem ============================================================
cd /d "%~dp0"
set "PYTHONPATH="

rem 1) start the web server (a second instance exits harmlessly)
start "" wscript.exe "%~dp0start_server.vbs"

rem 2) start the watchdog (it skips itself if one is already running)
start "" wscript.exe "%~dp0watchdog.vbs" loop

rem 3) wait for the port to bind, then open the browser
ping -n 5 127.0.0.1 >nul 2>&1
start "" "http://127.0.0.1:8000/accounts/login/"
exit
