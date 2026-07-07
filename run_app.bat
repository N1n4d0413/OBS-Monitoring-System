@echo off
setlocal

set "APP_DIR=%~dp0"
set "PYTHON_EXE=C:\N1N4D.k\class projects\obs_m\obs_env\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Compatible Python 3.11 venv was not found:
    echo %PYTHON_EXE%
    echo.
    echo Create/install a Python 3.10-3.12 venv and install requirements.txt.
    pause
    exit /b 1
)

cd /d "%APP_DIR%"
"%PYTHON_EXE%" main.py

endlocal
