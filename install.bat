@echo off
chcp 65001 >nul
title GBT AI Short Drama Factory - Installer
echo.
echo =============================================
echo   GBT AI Short Drama Factory v1.0
echo   One-Click Installer
echo =============================================
echo.

set PYTHON=C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe

echo [1/3] Checking Python...
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found at %PYTHON%
    echo Please edit this file and set PYTHON to your python.exe path
    pause
    exit /b 1
)
echo   OK: %PYTHON%

echo.
echo [2/3] Installing dependencies...
%PYTHON% -m pip install gradio edge-tts imageio imageio-ffmpeg pysrt beautifulsoup4 lxml requests -q
if errorlevel 1 (
    echo [WARN] Some packages may have failed, trying to continue...
)
echo   OK

echo.
echo [3/3] Creating desktop shortcut...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%USERPROFILE%\Desktop\GBT-Drama.lnk'); $sc.TargetPath = '%PYTHON%'; $sc.Arguments = 'C:\Users\ADMIN\GBT-AI-ShortDrama\desktop_app.py'; $sc.WorkingDirectory = 'C:\Users\ADMIN\GBT-AI-ShortDrama'; $sc.IconLocation = '%PYTHON%'; $sc.Description = 'GBT AI Short Drama Factory'; $sc.Save()" 2>nul
if errorlevel 1 (
    echo [WARN] Could not create shortcut, use start_app.bat instead
) else (
    echo   Desktop shortcut created
)

echo.
echo =============================================
echo   INSTALLATION COMPLETE!
echo.
echo   Launch: Double-click GBT-Drama on Desktop
echo   OR run: start_app.bat
echo =============================================
pause
