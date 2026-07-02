@echo off
REM Sales Intelligence Platform - Startup Script
REM This script helps you start the server and client

setlocal enabledelayedexpansion

cls
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Sales Intelligence Platform - Startup Menu               ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo 1. Quick Test (single conversation analysis)
echo 2. Run System Tests (validate all components)
echo 3. Batch Scoring Demo (score multiple leads)
echo 4. Start Server (WebSocket streaming ready)
echo 5. Start Full System (Server + Client)
echo 6. View Documentation
echo 7. Exit
echo.
set /p choice="Select option (1-7): "

if "%choice%"=="1" (
    echo.
    echo Starting quick test...
    python test_demo_simple.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo Running system tests...
    python test_system.py
    pause
) else if "%choice%"=="3" (
    echo.
    echo Starting batch scoring demo...
    python demo_complete.py
    pause
) else if "%choice%"=="4" (
    echo.
    echo Starting FastAPI Server...
    echo Server will run on: http://0.0.0.0:8000
    echo WebSocket endpoint: ws://localhost:8000/ws/stream
    echo API docs: http://localhost:8000/docs
    echo.
    echo Press Ctrl+C to stop the server
    echo.
    python server_prod.py
) else if "%choice%"=="5" (
    echo.
    echo This will start both server and client...
    echo You need TWO terminals for this:
    echo.
    echo Terminal 1: python server_prod.py
    echo Terminal 2: python client_prod.py
    echo.
    echo Starting server in new window...
    start cmd /k "cd /d %CD% && python server_prod.py"
    echo.
    echo Waiting 3 seconds for server to start...
    timeout /t 3
    echo.
    echo Starting client...
    python client_prod.py
) else if "%choice%"=="6" (
    echo.
    echo Opening documentation...
    start notepad PRODUCTION_GUIDE.md
) else if "%choice%"=="7" (
    echo.
    echo Exiting...
    exit /b 0
) else (
    echo.
    echo Invalid option. Exiting...
    exit /b 1
)

exit /b 0
