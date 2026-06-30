@echo off
echo Stopping any existing Python processes...
taskkill /F /IM python.exe 2>nul

echo.
echo Starting Faster Whisper API with Sentiment Analysis...
echo.
echo The server will start at http://localhost:8000
echo Swagger UI: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
python app.py

pause