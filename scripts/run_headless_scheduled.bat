@echo off
setlocal enabledelayedexpansion

REM =================================================================
REM Automated Dice Job Application - Scheduled Task Runner
REM Runs every 6 hours via Windows Task Scheduler or GitHub Actions
REM Includes Slack notifications and detailed reporting
REM =================================================================

REM Set project directory (parent of scripts folder)
for %%i in ("%~dp0..") do set "PROJECT_DIR=%%~fi"
set "LOG_DIR=%PROJECT_DIR%\logs"
set "SUMMARY_FILE=%PROJECT_DIR%\job_summary.json"
set "LOG_FILE=%LOG_DIR%\headless_run_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Initialize counters
set "JOBS_ATTEMPTED=0"
set "JOBS_SUCCEEDED=0"
set "JOBS_FAILED=0"
set "ERROR_DETAILS="
set "START_TIME=%date% %time%"

REM =================================================================
REM LOGGING FUNCTIONS
REM =================================================================
echo [%date% %time%] Starting headless Dice automation... >> "%LOG_FILE%" 2>&1
echo [%date% %time%] Project directory: %PROJECT_DIR% >> "%LOG_FILE%" 2>&1
echo [%date% %time%] Log file: %LOG_FILE% >> "%LOG_FILE%" 2>&1
echo [%date% %time%] Summary file: %SUMMARY_FILE% >> "%LOG_FILE%" 2>&1

REM =================================================================
REM ENVIRONMENT SETUP
REM =================================================================

REM Navigate to project directory
cd /d "%PROJECT_DIR%"

echo [%date% %time%] Setting up environment... >> "%LOG_FILE%" 2>&1

REM Check if virtual environment exists and activate it
if exist ".venv\Scripts\activate.bat" (
    echo [%date% %time%] Activating virtual environment... >> "%LOG_FILE%" 2>&1
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [%date% %time%] ERROR: Failed to activate virtual environment >> "%LOG_FILE%" 2>&1
        set "ERROR_DETAILS=Virtual environment activation failed"
        goto :error
    )
) else (
    echo [%date% %time%] WARNING: Virtual environment not found, using system Python >> "%LOG_FILE%" 2>&1
)

REM =================================================================
REM MAIN EXECUTION
REM =================================================================

echo [%date% %time%] Running headless script... >> "%LOG_FILE%" 2>&1

REM Run the headless script using uv (modern Python package manager)
uv run apply-dice-headless >> "%LOG_FILE%" 2>&1

REM Capture the exit code
set "EXIT_CODE=%errorlevel%"
set /a "JOBS_ATTEMPTED+=1"

REM =================================================================
REM RESULT ANALYSIS
REM =================================================================

if %EXIT_CODE% equ 0 (
    echo [%date% %time%] SUCCESS: Headless script completed successfully >> "%LOG_FILE%" 2>&1
    set /a "JOBS_SUCCEEDED+=1"
    set "JOB_STATUS=SUCCESS"
    set "JOB_MESSAGE=All jobs completed successfully"
) else (
    echo [%date% %time%] ERROR: Headless script failed with exit code %EXIT_CODE% >> "%LOG_FILE%" 2>&1
    set /a "JOBS_FAILED+=1"
    set "JOB_STATUS=FAILED"
    set "JOB_MESSAGE=Script execution failed with exit code %EXIT_CODE%"
    set "ERROR_DETAILS=%ERROR_DETAILS% - Exit code: %EXIT_CODE%"
)

REM =================================================================
REM SUMMARY GENERATION
REM =================================================================

set "END_TIME=%date% %time%"

echo [%date% %time%] Generating job summary... >> "%LOG_FILE%" 2>&1

REM Create JSON summary file
(
    echo {
    echo   "execution_id": "%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%",
    echo   "start_time": "%START_TIME%",
    echo   "end_time": "%END_TIME%",
    echo   "status": "%JOB_STATUS%",
    echo   "jobs_attempted": %JOBS_ATTEMPTED%,
    echo   "jobs_succeeded": %JOBS_SUCCEEDED%,
    echo   "jobs_failed": %JOBS_FAILED%,
    echo   "message": "%JOB_MESSAGE%",
    echo   "error_details": "%ERROR_DETAILS%",
    echo   "log_file": "%LOG_FILE%"
    echo }
) > "%SUMMARY_FILE%"

echo [%date% %time%] Summary saved to: %SUMMARY_FILE% >> "%LOG_FILE%" 2>&1

REM =================================================================
REM SLACK NOTIFICATION
REM =================================================================

echo [%date% %time%] Sending Slack notification... >> "%LOG_FILE%" 2>&1

REM Check if Slack webhook URL is configured
if defined SLACK_WEBHOOK_URL (
    call :send_slack_notification
) else (
    echo [%date% %time%] WARNING: SLACK_WEBHOOK_URL not configured, skipping notification >> "%LOG_FILE%" 2>&1
)

goto :cleanup

REM =================================================================
REM SLACK NOTIFICATION FUNCTION
REM =================================================================

:send_slack_notification
REM Create Slack message based on job status
if "%JOB_STATUS%"=="SUCCESS" (
    set "SLACK_COLOR=good"
    set "SLACK_EMOJI=:white_check_mark:"
) else (
    set "SLACK_COLOR=danger"
    set "SLACK_EMOJI=:x:"
)

REM Prepare JSON payload for Slack
set "SLACK_PAYLOAD={\"text\": \"Dice Automation %SLACK_EMOJI%\", \"attachments\": [{\"color\": \"%SLACK_COLOR%\", \"fields\": [{\"title\": \"Execution Summary\", \"value\": \"*Status:* %JOB_STATUS%\\n*Jobs Attempted:* %JOBS_ATTEMPTED%\\n*Jobs Succeeded:* %JOBS_SUCCEEDED%\\n*Jobs Failed:* %JOBS_FAILED%\\n*Duration:* %START_TIME% to %END_TIME%\\n*Log File:* %LOG_FILE%\", \"short\": false}]}]}"

REM Send notification to Slack
powershell -Command "try { Invoke-RestMethod -Uri '%SLACK_WEBHOOK_URL%' -Method Post -Body '%SLACK_PAYLOAD%' -ContentType 'application/json' } catch { Write-Host 'Slack notification failed' }"

if errorlevel 1 (
    echo [%date% %time%] WARNING: Failed to send Slack notification >> "%LOG_FILE%" 2>&1
) else (
    echo [%date% %time%] SUCCESS: Slack notification sent >> "%LOG_FILE%" 2>&1
)

goto :eof

REM =================================================================
REM ERROR HANDLING
REM =================================================================

:error
set "JOB_STATUS=FAILED"
set "JOB_MESSAGE=Script execution failed"
set /a "JOBS_ATTEMPTED=0"
set /a "JOBS_FAILED=1"
goto :summary

REM =================================================================
REM CLEANUP
REM =================================================================

:cleanup
echo [%date% %time%] Cleaning up old log files... >> "%LOG_FILE%" 2>&1
forfiles /p "%LOG_DIR%" /m "headless_run_*.log" /d -7 /c "cmd /c del @path" >> "%LOG_FILE%" 2>&1

echo [%date% %time%] Cleaning up old summary files... >> "%LOG_FILE%" 2>&1
forfiles /p "%PROJECT_DIR%" /m "job_summary.json" /d -7 /c "cmd /c del @path" >> "%LOG_FILE%" 2>&1

echo [%date% %time%] Job execution completed. Status: %JOB_STATUS% >> "%LOG_FILE%" 2>&1
exit /b %EXIT_CODE%
