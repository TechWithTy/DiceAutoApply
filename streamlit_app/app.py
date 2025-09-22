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
from streamlit_app.ui_saas import (
    ensure_token_from_query,
    render_login_prompt,
    fetch_and_display_entitlements,
    can_use_features,
)
from streamlit_app.api import generate_report
from streamlit_app.ui_saas import render_demo_login
from streamlit_app.state import logout_user
from streamlit_app.ui_settings import render_settings


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
    # Single live log placeholder (keeps UI stable while streaming)
    live_log_block = st.empty()

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

        # Update a compact live log view here (full controls are below in the main logs section)
        try:
            live_text = "\n".join(st.session_state.get("logs", [])[-200:])
            if live_text:
                live_log_block.code(live_text, language="text")
        except Exception:
            pass
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

    # --- SaaS auth & credits ---
    token = ensure_token_from_query()
    if not token:
        render_login_prompt()
        # Demo-only helper to simulate a successful redirect/token without a backend
        render_demo_login(sim_credits=10)
        st.stop()
    credits = fetch_and_display_entitlements()
    if credits <= 0:
        st.info("You need credits to use automation features.")

    # --- Sidebar navigation & logout ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", options=["Dashboard", "Settings"], index=0)
    if st.sidebar.button("Logout"):
        logout_user()
        try:
            st.rerun()
        except Exception:
            pass

    # Auth
    authed = render_login()
    if not authed:
        st.stop()

    # Render selected page
    if page == "Settings":
        render_settings()
        return
    else:
        # Dashboard contents
        render_search_and_filters()
        render_profile_and_target()

    # Run controls
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        run_disabled = not can_use_features()
        if st.button("Run Automation (Headless)", disabled=run_disabled):
            run_headless_once()
    with col2:
        if st.button("Clear Logs"):
            clear_logs()

    # Example SaaS-gated feature: Generate Report
    st.subheader("SaaS Features")
    gen_disabled = not can_use_features()
    if st.button("Generate Report", disabled=gen_disabled):
        r = generate_report(token)
        if r.get("ok"):
            st.success("Report generated!")
        else:
            st.error(f"Error generating report: {r.get('detail')}")

    # Live logs
    render_live_logs(st.session_state.get("logs", []))

    # Summary
    render_summary(get_summary())


if __name__ == "__main__":
    main()