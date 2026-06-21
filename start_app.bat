@echo off
chcp 65001 >nul
title GBT AI Short Drama Factory
echo.
echo =========================================
echo   GBT AI Short Drama Factory v1.0
echo   AI Short Drama Auto-Generator
echo =========================================
echo.

:: Use system Python
set PYTHON=C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe

%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo [INFO] Checking dependencies...
%PYTHON% -c "import gradio" >nul 2>&1 || %PYTHON% -m pip install gradio edge-tts imageio imageio-ffmpeg pysrt -q

echo [INFO] Starting GBT AI Drama Factory...
echo [INFO] Browser will open: http://127.0.0.1:7860
echo.
%PYTHON% desktop_app.py

pause

