@echo off
chcp 65001 >nul
color a
title MikeTyping-onnx Installer
echo ============================================
echo   MikeTyping-onnx - установка окружения
echo ============================================
echo.

:: Проверка, установлен ли Python вообще
where python >nul 2>nul
if errorlevel 1 (
    set "pyver=Не установлен"
    goto py_error
)

:: Если установлен, проверяем версию
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
echo Текущая версия: %pyver%
echo.
echo Установите Python:
echo   - Скачать с официального сайта: https://python.org
echo   - Или из Microsoft Store: https://microsoft.com
echo Важно: при установке отметьте галочку "Add Python to PATH"
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
call .venv\Scripts\activate.bat

echo Обновление pip...
python -m pip install --upgrade pip || goto install_error

echo Установка зависимостей из requirements.txt...
pip install -r requirements.txt || goto install_error

echo Удаление конфликтующих пакетов...
pip uninstall pymorphy2 -y 2>nul
pip uninstall pymorphy2-dicts-ru -y 2>nul

goto install_ok

:install_error
pip cache purge
echo [ОШИБКА] Не удалось установить зависимости.
pause
exit /b 1

:install_ok
pip cache purge
:: Создание папки для логов (если её нет)
if not exist "logs" mkdir logs

:: ========== СОЗДАНИЕ ЯРЛЫКА НА РАБОЧЕМ СТОЛЕ ==========
echo.
echo Создание ярлыка на рабочем столе...

set "SCRIPT_DIR=%~dp0"
set "START_BAT=%SCRIPT_DIR%start.bat"

:: Корректное получение пути к Рабочему столу через реестр
for /f "usebackq tokens=2,*" %%A in (`reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v Desktop`) do set "DESKTOP=%%B"
:: Раскрываем переменные среды в пути (например, %USERPROFILE%)
call set "DESKTOP=%DESKTOP%"

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
    echo Ярлык создан со стандартной иконкой. Чтобы задать иконку,
    echo поместите файл MikeTyping.ico в папку "%SCRIPT_DIR%" и запустите install.bat повторно.
)

echo.
echo ============================================
echo   Установка завершена успешно!
echo   Ярлык "MikeTyping" находится на рабочем столе.
echo   Запустите его для работы приложения.
echo ============================================
pause
