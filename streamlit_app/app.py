import streamlit as st
import time
from typing import Optional

from streamlit_app.state import (
    ensure_session_defaults,
    get_credentials,
    append_log,
    clear_logs,
    set_summary,
    get_summary,
)
from streamlit_app.ui_auth import render_login
from streamlit_app.ui_params import render_search_and_filters, render_profile_and_target
from streamlit_app.ui_results import render_live_logs, render_summary
from streamlit_app.runner import stream_headless_run


st.set_page_config(page_title="Dice Job Automation Dashboard", layout="wide")


def run_headless_once() -> None:
    """Start the headless run and stream logs to the UI."""
    creds = get_credentials()
    if not creds.email or not creds.password:
        st.error("Please login with your Dice email and password first.")
        return

    # Clear previous state for a fresh run
    clear_logs()
    set_summary(None)

    # Launch process
    rc, line_iter = stream_headless_run({"email": creds.email, "password": creds.password})

    applied: Optional[int] = None
    failed: Optional[int] = None
    failed_jobs: list[str] = []

    status_placeholder = st.empty()
    progress = st.progress(0)

    # Stream lines
    for i, line in enumerate(line_iter):
        append_log(line)
        # Parse live summary signals
        if line.startswith("Jobs successfully applied:"):
            try:
                applied = int(line.split(":", 1)[1].strip())
            except Exception:
                pass
        elif line.startswith("Jobs failed:"):
            try:
                failed = int(line.split(":", 1)[1].strip())
            except Exception:
                pass
        elif line.strip().startswith("- "):
            failed_jobs.append(line.strip()[2:])

        # Update UI
        render_live_logs(st.session_state.get("logs", []))
        progress.progress(min(((i + 1) % 100), 100))
        time.sleep(0.02)

    # Finalize
    summary = {
        "applied": applied or 0,
        "failed": failed or 0,
        "failed_jobs": failed_jobs,
    }
    set_summary(summary)
    status_placeholder.success("Automation completed. See summary below.")


def main() -> None:
    ensure_session_defaults()

    st.title("Dice Job Automation Dashboard")

    # Auth
    authed = render_login()
    if not authed:
        st.stop()

    # Parameters
    render_search_and_filters()
    render_profile_and_target()

    # Run controls
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("Run Automation (Headless)"):
            run_headless_once()
    with col2:
        if st.button("Clear Logs"):
            clear_logs()

    # Live logs
    render_live_logs(st.session_state.get("logs", []))

    # Summary
    render_summary(get_summary())


if __name__ == "__main__":
    main()