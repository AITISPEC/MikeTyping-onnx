@echo off
chcp 65001 >nul
color a
cd /d "%~dp0"

set "VENV_PYTHONW="
if exist ".venv\Scripts\pythonw.exe" set "VENV_PYTHONW=.venv\Scripts\pythonw.exe"
if "%VENV_PYTHONW%"=="" (
    echo Виртуальное окружение не найдено. Запустите install.bat.
    pause
    exit /b 1
)

:: Проверяем, есть ли запущенные pythonw.exe
tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul | find /I "pythonw.exe" >nul
if errorlevel 1 (
    goto do_start
) else (
    goto do_stop
)

:do_start
echo Запускаем приложение...
:: Создаем папку logs, если её вдруг нет, и удаляем старый маркер
if not exist logs mkdir logs
if exist logs\asr_ready.tmp del logs\asr_ready.tmp

if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
start "" "%VENV_PYTHONW%" main.py

:wait_loop
timeout /t 1 > nul
if not exist logs\asr_ready.tmp goto wait_loop

echo Приложение запущено.
del logs\asr_ready.tmp
timeout /t 1 > nul
msg * "MikeTyping работает"
exit /b 0

:do_stop
echo Останавливаем приложение...
taskkill /F /IM pythonw.exe >nul 2>&1
echo Остановлено.
msg * "MikeTyping остановлен"
timeout /t 1 > nul
exit /b 0
