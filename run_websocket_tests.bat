@echo off
REM Run WebSocket Integration Tests with Live Backend (Windows)

if "%LIVE_INTERVIEW_BASE_URL%"=="" (
    echo ERROR: LIVE_INTERVIEW_BASE_URL not set
    echo.
    echo Please set the following environment variables:
    echo   LIVE_INTERVIEW_BASE_URL              (e.g., http://localhost:8000 or https://api.example.com)
    echo   LIVE_INTERVIEW_ADMIN_EMAIL           (e.g., admin@example.com)
    echo   LIVE_INTERVIEW_ADMIN_PASSWORD        (password)
    echo   LIVE_INTERVIEW_CANDIDATE_EMAIL       (e.g., candidate@example.com)
    echo   LIVE_INTERVIEW_CANDIDATE_PASSWORD    (password)
    echo   LIVE_INTERVIEW_REQUEST_TIMEOUT       (optional, default 60 seconds)
    exit /b 1
)

echo Running WebSocket Integration Tests
echo ====================================
echo Backend URL: %LIVE_INTERVIEW_BASE_URL%
echo Admin Email: %LIVE_INTERVIEW_ADMIN_EMAIL%
echo Candidate Email: %LIVE_INTERVIEW_CANDIDATE_EMAIL%
echo.

REM Run pytest with WebSocket tests
pytest tests\integration\test_websocket_events.py -v -s ^
    --tb=short ^
    --log-cli-level=INFO

pause
