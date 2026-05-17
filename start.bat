@echo off
chcp 65001 >nul
color a
cd /d "%~dp0"

:: Check if pythonw.exe is running
tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul | find /I "pythonw.exe" >nul
if errorlevel 1 (
    echo Starting application...
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
    ) else if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
    )
    start /B pythonw main.py
    echo Application started.
) else (
    echo Stopping application...
    taskkill /F /IM pythonw.exe >nul
    echo Application stopped.
)
