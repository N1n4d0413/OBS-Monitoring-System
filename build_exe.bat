@echo off
setlocal

set "APP_DIR=%~dp0"
set "PYTHON_EXE=C:\N1N4D.k\class projects\obs_m\obs_env\Scripts\python.exe"
set "ICON_FILE=%APP_DIR%assets\app.ico"

if not exist "%PYTHON_EXE%" (
    echo Compatible Python 3.11 venv was not found:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%ICON_FILE%" (
    echo WARNING: assets\app.ico was not found.
    echo The EXE will still build, but it will use the default PyInstaller icon.
    echo.
)

cd /d "%APP_DIR%"
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm OBS-Lecture-Guard.spec

if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete:
echo %APP_DIR%dist\OBS-Lecture-Guard.exe
pause

endlocal
