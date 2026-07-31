from __future__ import annotations

from pathlib import Path

import streamlit as st

from backend.resume_builder.service import (
    build_optimized_resume_payload,
    collect_resume_sources,
    generate_optimized_resume,
    save_generated_resume_profile,
)
from _data_.Profiles.main_profile import user_profile
from streamlit_app.state import (
    get_resume_builder_message,
    get_resume_builder_result,
    set_resume_builder_message,
    set_resume_builder_result,
)


def render_resume_builder() -> None:
    st.header("Resume Builder")

    sources = collect_resume_sources(user_profile)
    job_titles = [job.title for job in user_profile.job_titles]
    source_labels = {
        source["path"]: (
            f"{source['label']} ({Path(source['path']).name})"
            + (" [Structured]" if source.get("structured_profile") else " [Parsed]")
        )
        for source in sources
    }

    with st.expander("Available Source Resumes", expanded=False):
        st.dataframe(
            [
                {
                    "Label": source["label"],
                    "File": Path(source["path"]).name,
                    "Structured": "Yes" if source.get("structured_profile") else "No",
                    "Exists": "Yes" if source.get("exists") else "No",
                    "Job Titles": ", ".join(source.get("job_titles", [])),
                }
                for source in sources
            ],
            use_container_width=True,
            hide_index=True,
        )

    with st.form("resume_builder_form"):
        target_job_title = st.selectbox("Target Job Title", options=job_titles, index=0)
        default_sources = [source["path"] for source in sources if target_job_title in source["job_titles"]]
        if not default_sources and sources:
            default_sources = [sources[0]["path"]]

        selected_sources = st.multiselect(
            "Source Resumes",
            options=[source["path"] for source in sources],
            default=default_sources,
            format_func=lambda path: source_labels.get(path, path),
            help="Structured sources use curated resume data. Parsed sources fall back to text extraction from the file.",
        )
        output_name = st.text_input("Output File Name", value=f"{target_job_title} Optimized Resume")
        target_company = st.text_input("Target Company", value="")
        target_role = st.text_input("Target Role Override", value=target_job_title)
        additional_skills = st.text_input("Additional Skills", value="", help="Comma-separated skills to inject.")
        custom_summary = st.text_area("Custom Summary Override", value="", height=100)
        job_description = st.text_area("Job Description / Keywords", value="", height=220)
        save_as_profile = st.checkbox("Save generated resume as reusable structured source", value=True)
        generate = st.form_submit_button("Generate Optimized Resume")

    if generate:
        if not selected_sources:
            st.error("Select at least one source resume.")
        else:
            payload = build_optimized_resume_payload(
                target_job_title=target_job_title,
                source_resume_paths=selected_sources,
                target_company=target_company,
                target_role=target_role,
                job_description=job_description,
                custom_summary=custom_summary,
                additional_skills=additional_skills,
                profile=user_profile,
            )
            output_path = generate_optimized_resume(payload=payload, output_name=output_name)
            saved_profile_path = None
            if save_as_profile:
                saved_profile_path = save_generated_resume_profile(
                    payload=payload,
                    output_pdf_path=str(output_path),
                    profile_name=output_name,
                    target_job_title=target_job_title,
                    target_company=target_company,
                )
                set_resume_builder_message(f"Saved reusable structured profile: {saved_profile_path.name}")
            else:
                set_resume_builder_message(None)
            set_resume_builder_result(
                {
                    "payload": payload,
                    "path": str(output_path),
                    "filename": output_path.name,
                    "bytes": output_path.read_bytes(),
                    "saved_profile_path": str(saved_profile_path) if saved_profile_path else None,
                }
            )

    result = get_resume_builder_result()
    message = get_resume_builder_message()
    if message:
        st.info(message)
    if not result:
        return

    st.success(f"Generated resume: {result['filename']}")
    st.download_button(
        "Download Resume PDF",
        data=result["bytes"],
        file_name=result["filename"],
        mime="application/pdf",
    )

    with st.expander("Generated Resume Payload", expanded=False):
        st.json(result["payload"])

    if result.get("saved_profile_path"):
        st.caption(f"Reusable structured profile saved at {Path(result['saved_profile_path']).name}")

    excerpt = result["payload"].get("source_resume_excerpt", "")
    if excerpt:
        with st.expander("Source Resume Extract", expanded=False):
            st.code(excerpt, language="text")
