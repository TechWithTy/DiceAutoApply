# Streamlit UI Guide — Single Logs Area & Full‑Width Layout

This guide documents the UI/UX improvements we added to the Streamlit dashboard and how to use them effectively. It also explains where the logic lives in the codebase and how to tweak it.

## Overview

- A single, stable "Live Logs" area that updates during a run and is easy to read.
- Full‑width layout to maximize space for logs and content.
- Sidebar navigation (Dashboard/Settings) and Logout.
- Demo login to simulate SaaS auth and credits; Dice login for automation.

## Files and Responsibilities

- `streamlit_app/app.py`
  - Page orchestration, sidebar navigation (Dashboard/Settings), Logout button.
  - Starts headless automation and streams a compact live log view during the run.
  - Renders the main "Live Logs" section once (to avoid duplicates).
- `streamlit_app/ui_results.py`
  - The main "Live Logs" section with controls for Lines, Wrap, Clear, and Download.
  - Accessibility label fix for `st.text_area`.
- `streamlit_app/runner.py`
  - Launches the headless script unbuffered (`python -u -m app.dice._experimental_.headless_test`) for real‑time streaming.
  - Forces `PYTHONUNBUFFERED=1` to improve log stream responsiveness.
- `streamlit_app/ui_saas.py`
  - SaaS token capture from query params.
  - Demo Login expander (sets `DEMO_TOKEN`, seeds credits, reruns app).
  - Entitlements fetch + credit gating (`can_use_features()`).
- `streamlit_app/state.py`
  - Session state helpers (credentials, params, logs, summary, token, credits).
  - `logout_user()` to clear auth/credits/logs/summary.
- `streamlit_app/ui_settings.py`
  - Settings page for Dice creds and default parameters (session‑scoped).

## What’s Fixed

- **Single logs area:**
  - We render logs once in `ui_results.py` with a stable container.
  - During a run, `app.py` shows a compact live log preview while the main logs update below.
  - No more duplicate "Live Logs" sections.

- **Full‑width layout:**
  - `st.set_page_config(layout="wide")` in `app.py` ensures the content spans the available width.
  - The logs panel can be set to show up to 1000 lines with wrapping for readability.

- **Better controls:**
  - "Lines": 100/200/500/1000
  - "Wrap": toggle long lines wrapping
  - "Clear": clears session logs and reruns the app for a fresh view
  - "Download Full Logs": exports a `.txt` of all collected logs

- **Real‑time streaming:**
  - Unbuffered child process (`python -u -m …`) + `PYTHONUNBUFFERED=1`.
  - Iterator based on `readline` to stream line‑by‑line.

## How to Use

1. **Start the app**
   - PowerShell
     ```powershell
     .\.venv\Scripts\Activate.ps1
     streamlit run streamlit_app/app.py
     ```
   - Git Bash
     ```bash
     source .venv/Scripts/activate
     streamlit run streamlit_app/app.py
     ```

2. **Authenticate**
   - SaaS token (Demo): open `http://localhost:8501?token=DEMO_TOKEN` or use the Demo Login expander (sets token + credits and reruns).
   - Dice login: enter email/password in the Login section and click "Sign in" (shows "Authenticated.").

3. **Run Automation**
   - Ensure sidebar Credits > 0 (gates the Run button).
   - Click "Run Automation (Headless)".
   - Watch the progress bar and the compact live log preview.
   - The main "Live Logs" section refreshes with the latest lines; use Wrap and Lines to adjust viewing.

4. **Logs management**
   - Click "Clear" before a new run to avoid mixing logs.
   - Click "Download Full Logs" to export all logs for review.

5. **Settings and Logout**
   - Sidebar → Navigation: switch between **Dashboard** and **Settings**.
   - **Settings** lets you update Dice creds and default parameters (session‑only).
   - **Logout** clears token, entitlements, Dice creds, logs, and summary; the app reruns to the login prompt.

## Troubleshooting

- **Run button disabled**
  - Sidebar must show Credits > 0 (use Demo Login or real backend).
  - Dice login must show "Authenticated." after clicking Sign in.

- **No new logs while running**
  - The first output often includes profile and navigation info from Playwright.
  - Give it 30–60 seconds; if still idle, click "Clear" and try again.
  - Ensure `runner.py` changes are active (restart Streamlit + hard refresh).

- **Still seeing `experimental_rerun` error**
  - Restart Streamlit (the server didn’t pick up the updated `ui_saas.py`).
  - We now use `st.rerun()` with a fallback; older code in memory will throw until restarted.

## Developer Notes

- **Credit gating:**
  - `can_use_features()` → true if `get_credits() > 0`.
  - Demo token: `fetch_and_display_entitlements()` skips remote call and keeps demo credits.

- **Where to tweak UI layout:**
  - Expand the compact live log preview in `app.py` (`live_log_block`) or remove it entirely if you prefer only the main logs.
  - Adjust default Lines/Wrap in `ui_results.py`.

- **Persistence:**
  - All settings are session‑scoped. To persist across restarts, add a simple JSON store and load on startup.

## Change Summary

- `app.py`: single live logs area, sidebar nav + logout, structured run streaming.
- `ui_results.py`: logs controls (Lines/Wrap/Clear/Download), label fix, cleaner UX.
- `runner.py`: unbuffered child process + `readline` iteration + `PYTHONUNBUFFERED=1`.
- `ui_saas.py`: demo login sets token/credits then reruns; entitlements fetch respects demo mode.
- `state.py`: added `logout_user()` convenience.
- `ui_settings.py`: new settings page.

If you want me to also include screenshots or a short screencast workflow in this README, let me know and I’ll embed them.
