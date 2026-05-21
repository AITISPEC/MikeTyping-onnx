@echo off
chcp 65001 >nul
color a
title Dump for AI Launcher
echo =========================
echo   AITISPEC - Dump for AI
echo =========================
echo.

:: Переход в папку, где находится bat-файл
cd /d "%~dp0"

:: Проверка существования виртуального окружения
if not exist ".venv\Scripts\activate.bat" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo.
    pause
    exit /b 1
)

:: Активация окружения
call .venv\Scripts\activate.bat

:: Запуск приложения
python dump_for_ai.py
