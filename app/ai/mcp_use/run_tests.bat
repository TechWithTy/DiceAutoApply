@echo off
setlocal ENABLEDELAYEDEXPANSION
REM Change to the directory of this script so relative paths work
pushd %~dp0

REM Ensure project root is on PYTHONPATH for imports like 'from app...'
set PYTHONPATH=%~dp0..\..\..

REM Install/sync project dependencies via uv (reads pyproject.toml)
uv sync

REM Run Lettuce via uv (uses project-local venv automatically)
uv run -m lettuce _tests

popd
endlocal
