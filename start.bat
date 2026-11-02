@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo           FACECORE AI -- ONE-CLICK LOCAL DEPLOYMENT (STEP 10)
echo ======================================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "PYTHON_EXE=%SCRIPT_DIR%backend\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment python.exe not found at:
    echo         %PYTHON_EXE%
    echo Please initialize the backend venv first:
    echo   python -m venv backend\.venv
    echo   backend\.venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

echo [1/4] Verifying neural network model weights integrity...
"%PYTHON_EXE%" backend\scripts\verify_weights.py
if errorlevel 1 (
    echo [ERROR] Model weight verification failed! Check weights directory.
    pause
    exit /b 1
)

echo.
echo [2/4] Checking network ports (8001 and 5173)...
netstat -ano | findstr /R /C:":8001 .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Port 8001 is already in use by an existing process.
    echo        If FACECORE AI is already running, you can connect directly.
)
netstat -ano | findstr /R /C:":5173 .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Port 5173 is already in use. Vite will automatically allocate the next available port.
)

echo.
echo [3/4] Launching FastAPI backend server on http://127.0.0.1:8001 ...
start "FACECORE Backend (FastAPI)" /min cmd /c "%PYTHON_EXE% -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001"

echo.
echo [4/4] Launching Vite frontend server on http://localhost:5173 ...
start "FACECORE Frontend (Vite)" /min cmd /c "npm --prefix frontend run dev"

echo.
echo ======================================================================
echo           FACECORE AI STARTED SUCCESSFULLY!
echo ======================================================================
echo   Frontend UI:  http://localhost:5173
echo   Backend API:  http://127.0.0.1:8001
echo   Swagger Docs: http://127.0.0.1:8001/docs
echo.
echo Close the individual terminal windows or use taskkill to stop services.
echo.
timeout /t 5

