from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any
import streamlit as st

AUTH_KEY = "auth"
PARAMS_KEY = "params"
LOGS_KEY = "logs"
SUMMARY_KEY = "summary"
AUTH_TOKEN_KEY = "auth_token"
ENTITLEMENTS_KEY = "entitlements"
RESUME_BUILDER_RESULT_KEY = "resume_builder_result"
RESUME_BUILDER_MESSAGE_KEY = "resume_builder_message"


@dataclass
class Credentials:
    email: str = ""
    password: str = ""

    def to_env(self) -> Dict[str, str]:
        return {
            "DICE_EMAIL": self.email or "",
            "EMAIL": self.email or "",
            "DICE_PASSWORD": self.password or "",
            "PASSWORD": self.password or "",
        }


DEFAULT_PARAMS: Dict[str, Any] = {
    "keywords": "software engineer",
    "location": "United States",
    "radius": 50,
    "filters": {
        "work_setting": "Remote",
        "posted_date": "Last 3 Days",
        "employment_types": ["Full-time", "Contract", "Third Party"],
        "employer_types": ["Direct Hire", "Recruiter"],
        "willing_to_sponsor": False,
        "easy_apply": True,
    },
    "target": {
        "job_title": "Full Stack AI Engineer",
        "max_apply_jobs": 100,
    },
}


def ensure_session_defaults() -> None:
    if AUTH_KEY not in st.session_state:
        st.session_state[AUTH_KEY] = asdict(Credentials())
    if PARAMS_KEY not in st.session_state:
        st.session_state[PARAMS_KEY] = DEFAULT_PARAMS.copy()
    if LOGS_KEY not in st.session_state:
        st.session_state[LOGS_KEY] = []
    if SUMMARY_KEY not in st.session_state:
        st.session_state[SUMMARY_KEY] = None
    if AUTH_TOKEN_KEY not in st.session_state:
        st.session_state[AUTH_TOKEN_KEY] = None
    if ENTITLEMENTS_KEY not in st.session_state:
        st.session_state[ENTITLEMENTS_KEY] = {"credits": 0}
    if RESUME_BUILDER_RESULT_KEY not in st.session_state:
        st.session_state[RESUME_BUILDER_RESULT_KEY] = None
    if RESUME_BUILDER_MESSAGE_KEY not in st.session_state:
        st.session_state[RESUME_BUILDER_MESSAGE_KEY] = None


def get_credentials() -> Credentials:
    data = st.session_state.get(AUTH_KEY, {})
    return Credentials(email=data.get("email", ""), password=data.get("password", ""))


def set_credentials(creds: Credentials) -> None:
    st.session_state[AUTH_KEY] = asdict(creds)


def get_params() -> Dict[str, Any]:
    return st.session_state.get(PARAMS_KEY, DEFAULT_PARAMS.copy())


def set_params(params: Dict[str, Any]) -> None:
    st.session_state[PARAMS_KEY] = params


def append_log(line: str) -> None:
    st.session_state[LOGS_KEY].append(line)


def clear_logs() -> None:
    st.session_state[LOGS_KEY] = []


def set_summary(summary: Dict[str, Any] | None) -> None:
    st.session_state[SUMMARY_KEY] = summary


def get_summary() -> Dict[str, Any] | None:
    return st.session_state.get(SUMMARY_KEY)


# --- Token & entitlements utilities ---
def get_auth_token() -> str | None:
    return st.session_state.get(AUTH_TOKEN_KEY)


def set_auth_token(token: str | None) -> None:
    st.session_state[AUTH_TOKEN_KEY] = token


def get_entitlements_state() -> Dict[str, Any]:
    return st.session_state.get(ENTITLEMENTS_KEY, {"credits": 0})


def set_entitlements_state(data: Dict[str, Any]) -> None:
    st.session_state[ENTITLEMENTS_KEY] = data or {"credits": 0}


def get_credits() -> int:
    ents = get_entitlements_state()
    try:
        return int(ents.get("credits", 0))
    except Exception:
        return 0


def logout_user() -> None:
    """Clear all authentication-related state and transient data."""
    for k in [AUTH_TOKEN_KEY, ENTITLEMENTS_KEY, AUTH_KEY, LOGS_KEY, SUMMARY_KEY, RESUME_BUILDER_RESULT_KEY, RESUME_BUILDER_MESSAGE_KEY]:
        if k in st.session_state:
            del st.session_state[k]
    # Re-seed defaults so app doesn't error on next render
    ensure_session_defaults()


def get_resume_builder_result() -> Dict[str, Any] | None:
    return st.session_state.get(RESUME_BUILDER_RESULT_KEY)


def set_resume_builder_result(result: Dict[str, Any] | None) -> None:
    st.session_state[RESUME_BUILDER_RESULT_KEY] = result


def get_resume_builder_message() -> str | None:
    return st.session_state.get(RESUME_BUILDER_MESSAGE_KEY)


def set_resume_builder_message(message: str | None) -> None:
    st.session_state[RESUME_BUILDER_MESSAGE_KEY] = message
