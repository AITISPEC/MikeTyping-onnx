@echo off
chcp 65001 >nul
color a
title MikeTyping-onnx Installer
echo ============================================
echo   MikeTyping-onnx - установка окружения
echo ============================================
echo.

:: Проверка версии Python
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set pyver=%%v
for /f "tokens=1,2 delims=." %%a in ("%pyver%") do (
    set py_major=%%a
    set py_minor=%%b
)
if %py_major% LSS 3 (
    goto py_error
)
if %py_major% EQU 3 if %py_minor% LSS 12 (
    goto py_error
)
goto py_ok

:py_error
echo [ОШИБКА] Требуется Python 3.12 или выше.
echo Установите Python:
echo   - Скачать с официального сайта: https://www.python.org/downloads/
echo   - Или из Microsoft Store: https://apps.microsoft.com/detail/9ncvdn91xzqp
echo Важно: при установке отметьте "Add Python to PATH"
pause
exit /b 1

:py_ok
echo Python %pyver% обнаружен (OK)

:: Создание виртуального окружения
if not exist ".venv" (
    echo Создание виртуального окружения...
    python -m venv .venv
    if errorlevel 1 (
        echo Не удалось создать venv.
        pause
        exit /b 1
    )
) else (
    echo Виртуальное окружение уже существует.
)

:: Активация venv и установка зависимостей
echo Активация окружения и установка пакетов...
call .venv/Scripts/activate.bat
call python -m pip install --upgrade pip
call pip install -r requirements.txt
call pip uninstall pymorphy2 -y
call pip uninstall pymorphy2-dicts-ru -y

if errorlevel 1 (
    echo Ошибка при установке зависимостей.
    pause
    exit /b 1
)

:: Создание папки для логов (если её нет)
if not exist "logs" mkdir logs

:: ========== СОЗДАНИЕ ЯРЛЫКА НА РАБОЧЕМ СТОЛЕ ==========
echo.
echo Создание ярлыка на рабочем столе...

set "SCRIPT_DIR=%~dp0"
set "START_BAT=%SCRIPT_DIR%start.bat"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT_NAME=MikeTyping"
set "ICON_PATH=%SCRIPT_DIR%MikeTyping.ico"

:: Удаляем старый ярлык, если существует
if exist "%DESKTOP%\%SHORTCUT_NAME%.lnk" del "%DESKTOP%\%SHORTCUT_NAME%.lnk"

:: Создаём ярлык через PowerShell
powershell -Command ^
    "$WScriptShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WScriptShell.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%.lnk'); " ^
    "$Shortcut.TargetPath = '%START_BAT%'; " ^
    "$Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$Shortcut.Description = 'MikeTyping - голосовой ввод через onnx'; " ^
    "if (Test-Path '%ICON_PATH%') { $Shortcut.IconLocation = '%ICON_PATH%' }; " ^
    "$Shortcut.Save()"

if exist "%ICON_PATH%" (
    echo Ярлык создан с пользовательской иконкой: %ICON_PATH%
) else (
    echo [ВНИМАНИЕ] Не найден файл иконки MikeTyping.ico в папке проекта.
    echo Ярлык создан со стандартной иконкой. Если хотите зелёного человечка,
    echo поместите файл MikeTyping.ico в папку "%SCRIPT_DIR%" и запустите install.bat повторно.
)

echo.
echo ============================================
echo   Установка завершена успешно!
echo   Ярлык "MikeTyping" находится на рабочем столе.
echo   Запустите его для работы приложения.
echo ============================================
pause
