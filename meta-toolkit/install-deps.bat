@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "VENV=.venv"
set "DEV=0"

if /I "%~1"=="--dev" set "DEV=1"
if /I "%~1"=="-Dev" set "DEV=1"

echo ==> Checking Python...
py -3 --version
if errorlevel 1 (
    echo error: py -3 not found. Install Python 3.10+ from https://www.python.org/downloads/
    exit /b 1
)

if not exist "%VENV%\Scripts\python.exe" (
    echo ==> Creating virtual environment at %VENV%
    py -3 -m venv "%VENV%"
    if errorlevel 1 (
        echo error: failed to create venv
        exit /b 1
    )
) else (
    echo ==> Virtual environment already exists at %VENV%
)

echo ==> Upgrading pip
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

if "%DEV%"=="1" (
    echo ==> Installing requirements-dev.txt
    "%VENV%\Scripts\python.exe" -m pip install -r requirements-dev.txt
) else (
    echo ==> Installing requirements.txt
    "%VENV%\Scripts\python.exe" -m pip install -r requirements.txt
)
if errorlevel 1 exit /b 1

echo.
echo Done. Next steps:
echo   %VENV%\Scripts\activate.bat
echo   python meta_extract -f tests\fixtures\sample.txt --json
if "%DEV%"=="1" echo   pytest -v
echo.
echo Or run without activating:
echo   %VENV%\Scripts\python.exe -m pytest -v

endlocal
