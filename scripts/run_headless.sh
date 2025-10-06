#!/bin/bash
# Dice automation headless runner for Git Bash/MINGW64

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Navigate to project root
cd "$SCRIPT_DIR" || exit 1

echo "[Headless] Starting Dice automation"
echo "[Headless] Activating virtual environment"

# Activate virtual environment
source "$SCRIPT_DIR/.venv/Scripts/activate"

# Check if activation succeeded
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment"
    echo "Possible solutions:"
    echo "1. Run 'python -m venv .venv' to create the venv"
    echo "2. Install requirements: 'pip install -r requirements.txt'"
    exit 1
fi

echo "[Headless] Running automation..."
python -m app.dice._experimental_.headless_test

# Capture exit code
EXIT_CODE=$?

echo "[Headless] Automation completed with exit code: $EXIT_CODE"

# Pause to see results if not in CI
if [ -z "$CI" ]; then
    echo "Press any key to continue..."
    read -n 1 -s
fi

exit $EXIT_CODE
