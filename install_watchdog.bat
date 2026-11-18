@echo off
rem ============================================================
rem  Install the server watchdog:
rem    1) write an autostart entry into the Startup folder
rem    2) launch the watchdog right now (hidden)
rem  No admin rights and no Task Scheduler needed.
rem ============================================================
set "BASE=%~dp0"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "LINKBAT=%STARTUP%\TCMInventoryWatchdog.bat"

echo ============================================
echo  Install server watchdog
echo ============================================
echo.

if not exist "%BASE%logs" mkdir "%BASE%logs"

echo [1/2] writing autostart entry ...
> "%LINKBAT%" echo @echo off
>> "%LINKBAT%" echo start "" wscript.exe "%BASE%watchdog.vbs" loop
if not exist "%LINKBAT%" (
    echo [FAIL] cannot write to:
    echo        %LINKBAT%
    echo.
    pause
    exit /b 1
)
echo       OK -^> %LINKBAT%
echo.

echo [2/2] starting watchdog in background ...
start "" wscript.exe "%BASE%watchdog.vbs" loop
echo       OK - checks port 8000 every 60 seconds
echo.
echo Log file : %BASE%logs\watchdog.log
echo To stop  : run uninstall_watchdog.bat
echo.
if /i "%~1"=="/q" exit /b 0
pause
