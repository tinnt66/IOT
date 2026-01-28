@echo off
echo ================================================
echo   IoT Sensor Data REST API Server
echo ================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please create venv first: python -m venv .venv
    pause
    exit /b 1
)

echo [1/2] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [2/2] Starting FastAPI server...
echo.
echo Server will start at: http://0.0.0.0:8000
echo API Docs: http://localhost:8000/docs
echo.

python run_api_server.py

pause

