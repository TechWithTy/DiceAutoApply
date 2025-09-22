from __future__ import annotations

from typing import Dict, Any, List
import streamlit as st
from _data_.Profiles.main_profile import user_profile
from .state import get_params, set_params


def render_search_and_filters() -> Dict[str, Any]:
    """Render search inputs and Dice filters. Returns current params dict."""
    params = get_params()

    with st.expander("Job Search Parameters", expanded=True):
        params["keywords"] = st.text_input("Keywords", value=params.get("keywords", "software engineer"))
        params["location"] = st.text_input("Location", value=params.get("location", "United States"))
        params["radius"] = st.slider("Radius (miles)", 0, 100, int(params.get("radius", 50)))

    with st.expander("Filters (Dice)"):
        f = params.get("filters", {})
        f["work_setting"] = st.selectbox(
            "Work Setting",
            options=["On-Site", "Remote", "Hybrid"],
            index={"On-Site": 0, "Remote": 1, "Hybrid": 2}.get(f.get("work_setting", "Remote"), 1),
        )
        f["posted_date"] = st.selectbox(
            "Posted Date",
            options=["Any Date", "Today", "Last 3 Days", "Last 7 Days"],
            index={"Any Date": 0, "Today": 1, "Last 3 Days": 2, "Last 7 Days": 3}.get(
                f.get("posted_date", "Last 3 Days"), 2
            ),
        )
        f["employment_types"] = st.multiselect(
            "Employment Types",
            options=["Full-time", "Part-time", "Contract", "Third Party"],
            default=f.get("employment_types", ["Full-time", "Contract", "Third Party"]),
        )
        f["employer_types"] = st.multiselect(
            "Employer Types",
            options=["Direct Hire", "Recruiter", "Other"],
            default=f.get("employer_types", ["Direct Hire", "Recruiter"]),
        )
        f["willing_to_sponsor"] = st.toggle("Willing to Sponsor", value=bool(f.get("willing_to_sponsor", False)))
        f["easy_apply"] = st.toggle("Easy Apply Only", value=bool(f.get("easy_apply", True)))
        params["filters"] = f

    set_params(params)
    return params


def render_profile_and_target() -> Dict[str, Any]:
    """Render profile target job title and run controls. Returns updated params."""
    params = get_params()
    target = params.get("target", {})

    with st.expander("Profile & Target Job Title"):
        available_titles: List[str] = [jt.title for jt in user_profile.job_titles]
        default_idx = 0
        if target.get("job_title") in available_titles:
            default_idx = available_titles.index(target.get("job_title"))
        target["job_title"] = st.selectbox("Target Job Title", options=available_titles, index=default_idx)
        target["max_apply_jobs"] = int(
            st.number_input("Max Apply Jobs", min_value=1, max_value=1000, value=int(target.get("max_apply_jobs", 100)), step=1)
        )

    params["target"] = target
    set_params(params)
    return params
