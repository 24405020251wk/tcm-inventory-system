@echo off
rem Installs a tiny launcher into the Windows Startup folder so the server
rem starts automatically every time you log in.
setlocal
set "DEST=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\TCMInventoryServer.bat"

if not exist "%~dp0start_server.vbs" (
    echo [ERROR] start_server.vbs not found in %~dp0
    goto done
)

>"%DEST%" echo @echo off
>>"%DEST%" echo start "" wscript.exe "%~dp0start_server.vbs"

if exist "%DEST%" (
    echo Installed successfully:
    echo   %DEST%
    echo.
    echo The server will start automatically from the next login.
) else (
    echo [ERROR] Failed to write %DEST%
)

:done
echo.
if /i not "%~1"=="/q" pause
