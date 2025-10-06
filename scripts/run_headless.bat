@echo off

REM Activate virtual environment
call .venv\Scripts\activate

REM Run the headless command
uv run apply-dice-headless

pause
