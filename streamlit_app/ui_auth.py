from __future__ import annotations

import os
import streamlit as st
from .state import Credentials, ensure_session_defaults, get_credentials, set_credentials


def render_login() -> bool:
    """Render login form. Returns True if authenticated this session."""
    ensure_session_defaults()

    st.header("Login")
    with st.form("login_form", clear_on_submit=False):
        creds = get_credentials()
        email = st.text_input("Dice Email", value=creds.email, placeholder="you@example.com")
        password = st.text_input("Password", type="password", value=creds.password)
        submitted = st.form_submit_button("Sign in")

    if submitted:
        # Demo validation: compare to env if present, else accept non-empty
        env_email = os.getenv("DICE_EMAIL") or os.getenv("EMAIL")
        env_pw = os.getenv("DICE_PASSWORD") or os.getenv("PASSWORD")
        valid = False
        if env_email and env_pw:
            valid = (email == env_email and password == env_pw)
        else:
            valid = bool(email and password)

        if valid:
            set_credentials(Credentials(email=email, password=password))
            st.success("Authenticated.")
            return True
        else:
            st.error("Invalid credentials. Check email/password.")
            return False

    # If already in state and non-empty, consider authenticated
    if get_credentials().email and get_credentials().password:
        return True
    return False
