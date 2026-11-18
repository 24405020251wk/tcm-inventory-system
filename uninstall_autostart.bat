@echo off
rem Removes the automatic startup launcher.
setlocal
set "DEST=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\TCMInventoryServer.bat"

if exist "%DEST%" (
    del /f /q "%DEST%"
    echo Removed: %DEST%
) else (
    echo Autostart is not installed.
)

echo.
if /i not "%~1"=="/q" pause
