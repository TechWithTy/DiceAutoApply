from __future__ import annotations

from typing import Optional
import streamlit as st
from .state import (
    ensure_session_defaults,
    get_auth_token,
    set_auth_token,
    set_entitlements_state,
    get_credits,
)
from .api import build_login_url, get_entitlements


def ensure_token_from_query() -> Optional[str]:
    """If a token is present in query params, store it in session state."""
    ensure_session_defaults()
    token: Optional[str] = None
    try:
        # Streamlit newer API
        qp = st.query_params  # type: ignore[attr-defined]
        token = qp.get("token") if isinstance(qp.get("token"), str) else None
    except Exception:
        qp = st.experimental_get_query_params()
        vals = qp.get("token") or []
        token = vals[0] if vals else None

    if token:
        set_auth_token(token)
    return get_auth_token()


timeout_warn_key = "saas_login_warned"


def render_login_prompt() -> None:
    """Render a login link to SaaS provider."""
    url = build_login_url()
    st.warning("You must log in to continue.")
    st.markdown(f"[Login Here]({url})")


def render_demo_login(sim_credits: int = 10) -> None:
    """Provide a demo-only way to simulate a successful redirect and entitlements.

    - Sets a demo token in session
    - Updates the URL's query params with ?token=DEMO_TOKEN to mimic redirect
    - Seeds entitlements with provided credits
    """
    with st.expander("Demo: Simulate Login (No Backend)"):
        credits = st.number_input("Demo credits", min_value=0, max_value=10000, value=sim_credits, step=1)
        if st.button("Simulate Login"):
            demo_token = "DEMO_TOKEN"
            set_auth_token(demo_token)
            set_entitlements_state({"credits": int(credits)})
            try:
                # Newer Streamlit supports dict-like assignment
                st.query_params["token"] = demo_token  # type: ignore[attr-defined]
            except Exception:
                # Fallback for older versions
                st.experimental_set_query_params(token=demo_token)
            st.success(f"Demo login complete. Token set and {credits} credits granted.")
            # Immediately rerun so main() sees the token and proceeds to dashboard
            try:
                st.rerun()
            except Exception:
                # Fallback for very old Streamlit versions
                try:
                    st.experimental_rerun()  # type: ignore[attr-defined]
                except Exception:
                    pass


def fetch_and_display_entitlements() -> int:
    """Fetch entitlements for token and show credits metric in sidebar. Returns credits."""
    token = get_auth_token()
    if not token:
        return 0
    # If we are in demo mode, keep the locally set credits and skip API calls
    if token == "DEMO_TOKEN":
        credits = get_credits()
        st.sidebar.metric("Credits", credits)
        return credits
    data = get_entitlements(token)
    # If the remote call fails or returns fewer credits than we already have, keep the higher value
    if not data or data.get("credits", 0) < get_credits():
        credits = get_credits()
    else:
        set_entitlements_state(data)
        credits = get_credits()
    st.sidebar.metric("Credits", credits)
    return credits


def can_use_features() -> bool:
    return get_credits() > 0
