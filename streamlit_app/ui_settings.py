from __future__ import annotations

from typing import Dict, Any
import streamlit as st
from streamlit_app.state import get_credentials, set_credentials, get_params, set_params


def render_settings() -> None:
    """Settings page for user profile and app preferences.

    - Manage Dice credentials (stored in session only)
    - Manage default search parameters (keywords/location/radius)
    - Manage target job title defaults
    - Resume Builder generation lives on its own page
    """
    st.header("Settings")

    # Dice credentials (session-only; not persisted to disk)
    st.subheader("Dice Credentials")
    creds = get_credentials()
    with st.form("dice_creds_form"):
        email = st.text_input("Dice Email", value=creds.email)
        password = st.text_input("Dice Password", type="password", value=creds.password)
        submitted = st.form_submit_button("Save Credentials")
        if submitted:
            set_credentials(type(creds)(email=email, password=password))
            st.success("Credentials updated (session only).")

    st.divider()

    # Defaults for search/filters
    st.subheader("Default Search Parameters")
    params = get_params()
    with st.form("defaults_form"):
        params["keywords"] = st.text_input("Default Keywords", value=params.get("keywords", "software engineer"))
        params["location"] = st.text_input("Default Location", value=params.get("location", "United States"))
        params["radius"] = int(st.slider("Default Radius (miles)", 0, 100, int(params.get("radius", 50))))
        # Target
        tgt = params.get("target", {})
        tgt["max_apply_jobs"] = int(st.number_input("Default Max Apply Jobs", min_value=1, max_value=1000, value=int(tgt.get("max_apply_jobs", 100))))
        params["target"] = tgt
        save = st.form_submit_button("Save Defaults")
        if save:
            set_params(params)
            st.success("Defaults updated for this session.")

    st.caption("Note: Settings are stored in memory for this session only.")
    st.caption("Use the Resume Builder page to generate optimized resumes from your profile and existing resume files.")
