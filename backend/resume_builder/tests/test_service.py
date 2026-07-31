from __future__ import annotations

from pathlib import Path

from backend.resume_builder.service import (
    _extract_focus_keywords,
    _parse_experience,
    _parse_education,
    _parse_certifications,
    build_optimized_resume_payload,
    collect_resume_sources,
    generate_optimized_resume,
    load_structured_resume_profile,
    save_generated_resume_profile,
)


def test_collect_resume_sources_includes_existing_profile_resume():
    sources = collect_resume_sources()

    assert sources
    assert any(source["exists"] for source in sources)
    assert any("Full Stack AI Engineer" in source["job_titles"] for source in sources)
    assert any(source["structured_profile"] for source in sources)
    assert any("Warehouse Associate" in source["job_titles"] and source["structured_profile"] for source in sources)


def test_parse_experience_extracts_roles_and_bullets():
    text = """
    Senior Frontend Engineer | Example Corp | 01/2024 - Present
    Led migration to Next.js App Router across customer-facing surfaces.
    Improved accessibility compliance and page performance.
    Staff Engineer | Other Co | 02/2022 - 12/2023
    Built design system primitives and CI quality gates.
    """

    experience = _parse_experience(text)

    assert len(experience) == 2
    assert experience[0]["title"] == "Senior Frontend Engineer"
    assert experience[0]["org"] == "Example Corp"
    assert experience[0]["bullets"]


def test_parse_resume_sections_for_realistic_layout():
    text = """
    Experience
    Led migration to Next.js App Router across customer-facing surfaces.
    Improved accessibility compliance and page performance.
    Senior Frontend Engineer | Example Corp | 01/2024 - Present
    Built design system primitives and CI quality gates.
    Staff Engineer | Other Co | 02/2022 - 12/2023
    Education
    Bachelors Software Development
    Western Governors University
    2020-2023 BA
    Certifications
    IBM AI Engineering
    Professional Certificate
    CASP
    """

    experience = _parse_experience(text)
    education = _parse_education(text)
    certifications = _parse_certifications(text)

    assert experience[0]["title"] == "Senior Frontend Engineer"
    assert experience[0]["org"] == "Example Corp"
    assert education[0]["school"] == "Western Governors University"
    assert "Bachelors Software Development" in education[0]["degree"]
    assert any("IBM AI Engineering Professional Certificate" == cert for cert in certifications)
    assert "CASP" in certifications


def test_extract_focus_keywords_filters_common_words():
    keywords = _extract_focus_keywords(
        "We need a Next.js engineer with healthcare, accessibility, GraphQL, and TypeScript delivery experience.",
        ["Next.js"],
    )

    assert "Next.js" not in keywords
    assert any(word in keywords for word in ["healthcare", "accessibility", "GraphQL", "TypeScript"])


def test_build_payload_uses_profile_and_resume_sources():
    payload = build_optimized_resume_payload(
        target_job_title="Full Stack AI Engineer",
        source_resume_paths=[r"_data_\Resumes\Dice\8-5-24-Ai-Full-Stack.pdf"],
        target_company="Example Co",
        job_description="Looking for Python, React, TypeScript, GraphQL, and AI platform experience.",
    )

    assert payload["name"]
    assert payload["headline"] == "Full Stack AI Engineer"
    assert payload["experience"]
    assert payload["source_resume_paths"]
    assert "Example Co" in payload["summary"]


def test_structured_resume_profile_matches_primary_dice_resume():
    profile = load_structured_resume_profile(r"_data_\Resumes\Dice\8-5-24-Ai-Full-Stack.pdf")

    assert profile is not None
    assert profile["id"] == "dice_ai_full_stack"
    assert profile["experience"]


def test_build_payload_prefers_structured_source_profile():
    payload = build_optimized_resume_payload(
        target_job_title="Full Stack AI Engineer",
        source_resume_paths=[r"_data_\Resumes\Dice\8-5-24-Ai-Full-Stack.pdf"],
        target_company="Structured Co",
        job_description="Need GraphQL, TypeScript, React, and AI engineering experience.",
    )

    assert payload["structured_source_ids"] == ["dice_ai_full_stack"]
    assert payload["experience"][0]["org"] == "Deep Mind"
    assert payload["certifications"][0] == "IBM AI Engineering Professional Certificate"


def test_build_payload_prefers_structured_indeed_source_profile():
    payload = build_optimized_resume_payload(
        target_job_title="Full Stack AI Engineer",
        source_resume_paths=[r"_data_\Resumes\Indeed\indeed_blue_collar_resume.txt"],
        target_company="Warehouse Co",
        target_role="Warehouse Associate",
        job_description="Need warehouse operations, shipping, receiving, pallet jack, safety, and dependable attendance.",
    )

    assert payload["structured_source_ids"] == ["indeed_blue_collar"]
    assert payload["headline"] == "Warehouse Associate"
    assert payload["experience"][0]["org"] == "Operations Experience Summary"
    assert "Driver's License" in payload["certifications"]


def test_generate_optimized_resume_writes_pdf(tmp_path: Path):
    payload = {
        "name": "Test User",
        "headline": "Software Engineer",
        "contact": ["Denver, USA", "555-111-2222", "test@example.com"],
        "links_line": "Portfolio: example.com",
        "summary": "Targeting software engineering roles.",
        "skills": [{"label": "Core", "items": ["Python", "TypeScript"]}],
        "experience": [{"org": "Example", "title": "Engineer", "dates": "2024 - Present", "location": "Remote", "bullets": ["Built software."]}],
        "education": [{"school": "Test University", "degree": "B.S. CS", "dates": "2020"}],
    }

    from backend.resume_builder import service

    original_output_dir = service.OUTPUT_DIR
    service.OUTPUT_DIR = tmp_path
    try:
        out_path = generate_optimized_resume(payload=payload, output_name="Test Resume")
    finally:
        service.OUTPUT_DIR = original_output_dir

    assert out_path.exists()
    assert out_path.suffix == ".pdf"


def test_save_generated_resume_profile_writes_generated_library_entry(tmp_path: Path):
    payload = {
        "headline": "Software Engineer",
        "summary": "Targeted summary.",
        "skills": [{"label": "Core", "items": ["Python"]}],
        "experience": [{"org": "Example", "title": "Engineer", "dates": "2024", "location": "Remote", "bullets": ["Built software."]}],
        "education": [],
        "certifications": ["Cert A"],
        "source_resume_paths": [r"_data_\Resumes\Dice\8-5-24-Ai-Full-Stack.pdf"],
        "structured_source_ids": ["dice_ai_full_stack"],
    }

    from backend.resume_builder import service

    original_generated_dir = service.GENERATED_PROFILE_DIR
    service.GENERATED_PROFILE_DIR = tmp_path
    try:
        out_path = save_generated_resume_profile(
            payload=payload,
            output_pdf_path="backend/resume_builder/output/test.pdf",
            profile_name="My Generated Resume",
            target_job_title="Software Engineer",
            target_company="Example Co",
        )
    finally:
        service.GENERATED_PROFILE_DIR = original_generated_dir

    assert out_path.exists()
    data = __import__("json").loads(out_path.read_text(encoding="utf-8"))
    assert data["id"] == "generated_my-generated-resume"
    assert data["resume_paths"] == ["backend/resume_builder/output/test.pdf"]
    assert data["metadata"]["target_company"] == "Example Co"
