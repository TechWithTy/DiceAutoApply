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


def fetch_and_display_entitlements() -> int:
    """Fetch entitlements for token and show credits metric in sidebar. Returns credits."""
    token = get_auth_token()
    if not token:
        return 0
    data = get_entitlements(token)
    set_entitlements_state(data)
    credits = get_credits()
    st.sidebar.metric("Credits", credits)
    return credits


def can_use_features() -> bool:
    return get_credits() > 0
