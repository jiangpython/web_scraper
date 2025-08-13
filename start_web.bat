@echo off
chcp 65001 >nul
cls

echo ======================================================
echo  ShuYing Project Data Panel - Web Server
echo ======================================================
echo.

echo [INFO] Current directory: %CD%
echo [INFO] Changing to script directory...
cd /d "%~dp0"
echo [INFO] Project directory: %CD%
echo.

echo [INFO] Checking for virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found! Please create it first.
    echo.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    echo.
    pause
    exit /b 1
)
echo [INFO] Virtual environment activated successfully.
echo.

echo [INFO] Checking and installing dependencies from requirements.txt...
python -m pip install -r requirements.txt
echo.

echo [INFO] Checking for required files...
if not exist "web_server.py" (
    echo [ERROR] web_server.py not found!
    pause
    exit /b 1
)

echo [INFO] Starting Web Server...
echo [INFO] Access URL: http://localhost:5000
echo [INFO] AI Assistant is integrated, chat is available.
echo [INFO] Press Ctrl+C to stop the server.
echo ======================================================
echo.

echo [INFO] Attempting to open in browser automatically...
start http://localhost:5000

python web_server.py

echo.
echo ======================================================
echo [INFO] Web Server has stopped.
echo ======================================================
pause
