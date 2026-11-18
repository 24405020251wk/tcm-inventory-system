@echo off
rem ============================================================
rem  Uninstall the server watchdog:
rem    1) remove the autostart entry from the Startup folder
rem    2) stop the running watchdog process
rem  The web server itself is NOT stopped; use stop_server.bat for that.
rem ============================================================
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "LINKBAT=%STARTUP%\TCMInventoryWatchdog.bat"

echo ============================================
echo  Uninstall server watchdog
echo ============================================
echo.

if exist "%LINKBAT%" (
    del /f /q "%LINKBAT%"
    echo [OK] autostart entry removed
) else (
    echo [SKIP] no autostart entry found
)
echo.

echo stopping watchdog process ...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='wscript.exe'\" | Where-Object { $_.CommandLine -like '*watchdog.vbs*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" 2>nul
echo [OK] done
echo.
echo Note: the web server is still running. Use stop_server.bat to stop it.
echo.
if /i "%~1"=="/q" exit /b 0
pause
