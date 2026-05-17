@echo off
chcp 65001 >nul
color a
title MikeTyping-onnx Installer
echo ============================================
echo   MikeTyping-onnx - установка окружения
echo ============================================
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден. Установите Python 3.12+ и добавьте в PATH.
    pause
    exit /b 1
)

:: Создание виртуального окружения
if not exist ".venv" (
    echo Создание виртуального окружения...
    python -m venv venv
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
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

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
