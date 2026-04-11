@echo off
REM MMDx Local Development Startup Script for Windows
REM =====================================================

cd /d "%~dp0"

REM Check if .env file exists
if not exist .env (
    echo Creating .env from .env.example...
    if exist .env.example (
        copy .env.example .env
    ) else (
        echo FLASK_ENV=development > .env
        echo SECRET_KEY=dev-secret-key-change-in-production-12345 >> .env
        echo ADMIN_PASSWORD=admin >> .env
        echo DATABASE_PATH=warehouse.db >> .env
        echo FLASK_DEBUG=1 >> .env
        echo FLASK_RUN_HOST=127.0.0.1 >> .env
        echo PORT=5000 >> .env
    )
)

REM Load environment variables from .env
for /f "usebackq tokens=1,* delims=" %%a in ("%~dp0.env") do (
    set "%%a=%%b"
)

REM Check for virtual environment
if exist .venv (
    echo Activating virtual environment...
    .venv\Scripts\activate.bat
) else (
    echo Note: No .venv found, using system Python
)

REM Check dependencies
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Run the Flask application
echo.
echo Starting MMDx on http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
