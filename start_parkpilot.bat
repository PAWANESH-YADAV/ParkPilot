@echo off
chcp 65001 >nul
title ParkPilot - Full Stack Starter

echo ================================================
echo    ParkPilot - Backend + Frontend Auto Start
echo ================================================
echo.

set PROJECT_DIR=%~dp0
set BACKEND_DIR=%PROJECT_DIR%backend
set FRONTEND_DIR=%PROJECT_DIR%frontend
set VENV_PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe

echo [1/3] Checking Virtual Environment...
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment nahi mila! Creating new one...
    cd /d "%BACKEND_DIR%"
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Python install nahi hai ya PATH mein nahi hai!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created!
    echo.
    echo Installing dependencies...
    "%VENV_PYTHON%" -m pip install --upgrade pip
    "%VENV_PYTHON%" -m pip install fastapi==0.115.0 "uvicorn[standard]==0.32.0" sqlalchemy==2.0.36 pydantic==2.10.1 pydantic-settings==2.6.1 "python-jose[cryptography]==3.3.0" "bcrypt==4.1.3" python-multipart==0.0.12 python-dotenv==1.0.1 email-validator httpx==0.27.2 stripe==11.2.0 paho-mqtt==2.1.0
    if errorlevel 1 (
        echo [ERROR] Dependencies install mein problem!
        pause
        exit /b 1
    )
) else (
    echo [OK] Virtual environment found!
)
echo.

echo [2/3] Starting BACKEND Server (port 8000)...
echo     URL: http://localhost:8000
echo     API Docs: http://localhost:8000/docs
start "ParkPilot Backend" cmd /k "cd /d "%BACKEND_DIR%" && "%VENV_PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
echo [OK] Backend started in new window!
echo.

echo [3/3] Starting FRONTEND Dev Server (port 3000)...
echo     URL: http://localhost:3000
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo [INFO] node_modules nahi mila, running npm install first...
    call npm install
)
start "ParkPilot Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"
echo [OK] Frontend started in new window!
echo.

echo ================================================
echo   DONE! Both servers ab chal rahe hain!
echo.
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Frontend: http://localhost:3000  (ya 3001/3002)
echo.
echo   Admin Login (custom):
echo     Email: Admin9936@gmail.com
echo     Pass:  9936313819
echo.
echo   Demo Accounts:
echo     User:  user@parkpilot.com / User@123
echo     Admin: admin@parkpilot.com / Admin@123
echo.
echo   Band karne ke liye: windows close karein
echo ================================================
echo.
pause
