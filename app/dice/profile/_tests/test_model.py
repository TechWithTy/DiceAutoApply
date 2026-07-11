from pathlib import Path
from types import SimpleNamespace

from app.dice.profile.model import build_profile_payload


def test_build_profile_payload_deduplicates_skills_and_picks_resume_path(tmp_path, monkeypatch):
    monkeypatch.delenv("DICE_PROFILE_VISIBLE", raising=False)
    resume_path = tmp_path / "existing-resume.pdf"
    resume_path.write_text("resume", encoding="utf-8")

    profile = SimpleNamespace(
        name="Tyrique Daniel",
        email="tyriq@example.com",
        phone_number="555-111-2222",
        linkedin_profile="https://linkedin.com/in/example",
        about_me="Senior full stack engineer",
        city="Denver",
        country="USA",
        online_presence={
            "website": "https://example.com",
            "portfolio": "https://portfolio.example.com",
            "booking_link": "https://cal.example.com",
        },
        job_titles=[
            SimpleNamespace(
                title="Full Stack Engineer",
                relevant_resume_path="C:/tmp/missing-resume.pdf",
                skills=["Python", "React", "Python"],
            ),
            SimpleNamespace(
                title="Platform Engineer",
                relevant_resume_path=str(resume_path),
                skills=["Docker", "React"],
            ),
        ],
    )

    payload = build_profile_payload(profile)

    assert payload.full_name == "Tyrique Daniel"
    assert payload.first_name == "Tyrique"
    assert payload.last_name == "Daniel"
    assert payload.resume_path == str(resume_path)
    assert payload.profile_photo_path.endswith("profile_photo_placeholder.png")
    assert Path(payload.profile_photo_path).exists()
    assert payload.skills == ["Python", "React", "Docker"]
    assert payload.location == "Denver, USA"
    assert payload.headline == "Full Stack Engineer"
    assert payload.years_experience == 6
    assert payload.work_experiences[0].title == "AI Training Expert - Advanced Coder"
    assert payload.work_experiences[0].company == "Outlier"
    assert payload.educations[0].institution == "Western Governors University"
    assert payload.educations[0].field_of_study == "Software Development"
    assert payload.desired_salary == "120000"
    assert payload.ideal_company_size == "51-100 employees"
    assert payload.ideal_company_age == "11-20 years"
    assert payload.profile_visible is None
