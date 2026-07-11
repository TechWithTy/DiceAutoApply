"""
Normalize the Dice profile data we want to create or edit.
"""
from __future__ import annotations

import struct
import zlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from _data_.Profiles.main_profile import user_profile


@dataclass(frozen=True)
class WorkExperiencePayload:
    title: str
    company: str
    start_month: str
    start_year: str
    end_month: str
    end_year: str
    current: bool
    description: str


@dataclass(frozen=True)
class EducationPayload:
    institution: str
    degree: str
    field_of_study: str
    start_year: str
    end_year: str


@dataclass(frozen=True)
class DiceProfilePayload:
    full_name: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    linkedin_url: str
    website_url: str
    portfolio_url: str
    booking_link: str
    resume_path: str
    profile_photo_path: str
    headline: str
    summary: str
    location: str
    skills: List[str]
    job_titles: List[str]
    work_experiences: List[WorkExperiencePayload]
    educations: List[EducationPayload]
    years_experience: int
    desired_salary: str
    ideal_company_size: str
    ideal_company_age: str
    profile_visible: Optional[bool]


def _unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        value = (value or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _first_existing_path(paths: Sequence[str]) -> str:
    for raw_path in paths:
        if not raw_path:
            continue
        path = Path(raw_path)
        if path.exists():
            return str(path)
        if path.parent.exists():
            matches = sorted(path.parent.glob("*.pdf"))
            if matches:
                return str(matches[0])
    return paths[0] if paths else ""


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _ensure_placeholder_profile_photo() -> str:
    path = Path(__file__).resolve().parents[3] / "_data_" / "profile_photo_placeholder.png"
    if path.exists():
        return str(path)

    width = 512
    height = 512
    background = bytes((22, 96, 136))
    accent = bytes((238, 194, 79))
    rows = []
    for y in range(height):
        row = bytearray()
        row.append(0)
        for x in range(width):
            in_circle = (x - 256) ** 2 + (y - 256) ** 2 <= 150 ** 2
            row.extend(accent if in_circle else background)
        rows.append(bytes(row))

    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(b"".join(rows), level=9))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)
    return str(path)


def _optional_bool_from_env(name: str) -> Optional[bool]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return None
    value = raw_value.strip().lower()
    if value in {"1", "true", "yes", "y", "on", "visible"}:
        return True
    if value in {"0", "false", "no", "n", "off", "hidden"}:
        return False
    return None


def build_profile_payload(profile=user_profile) -> DiceProfilePayload:
    """
    Build a normalized payload from _data_.Profiles.main_profile.
    """
    job_titles = [jt.title.strip() for jt in getattr(profile, "job_titles", []) if getattr(jt, "title", "").strip()]
    skills = _unique_preserve_order(
        skill
        for job_title in getattr(profile, "job_titles", [])
        for skill in getattr(job_title, "skills", [])
    )
    resume_path = _first_existing_path([
        getattr(job_title, "relevant_resume_path", "") for job_title in getattr(profile, "job_titles", [])
    ])
    website_url = getattr(profile, "online_presence", {}).get("website", "")
    portfolio_url = getattr(profile, "online_presence", {}).get("portfolio", "")
    booking_link = getattr(profile, "online_presence", {}).get("booking_link", "")
    location = ", ".join(
        part for part in [
            getattr(profile, "city", "").strip(),
            getattr(profile, "country", "").strip(),
        ]
        if part
    )
    headline = job_titles[0] if job_titles else getattr(profile, "about_me", "Dice candidate")
    summary = getattr(profile, "about_me", "").strip()
    first_name, last_name = "", ""
    parts = [part for part in getattr(profile, "name", "").strip().split() if part]
    if parts:
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    years_experience = 0
    if getattr(profile, "job_titles", []):
        first_job = profile.job_titles[0]
        years_experience = int(getattr(first_job, "experience", 0) or 0)
    work_experiences = [
        WorkExperiencePayload(
            title="AI Training Expert - Advanced Coder",
            company="Outlier",
            start_month="July",
            start_year="2024",
            end_month="",
            end_year="",
            current=True,
            description=(
                "Developed and implemented AI training programs, collaborated with cross-functional teams "
                "on machine learning solutions, analyzed AI models, and maintained experimental frameworks "
                "for reproducible AI research and coding workflows."
            ),
        ),
        WorkExperiencePayload(
            title="ML Research Engineer / Trainer",
            company="Deep Mind",
            start_month="March",
            start_year="2023",
            end_month="August",
            end_year="2024",
            current=False,
            description=(
                "Led design, training, and optimization of machine learning models using TensorFlow and "
                "PyTorch. Built scalable ML infrastructure with Docker and Kubernetes and improved testing "
                "with retrieval-augmented generation systems."
            ),
        ),
        WorkExperiencePayload(
            title="AI Automation Engineer",
            company="Google",
            start_month="February",
            start_year="2022",
            end_month="January",
            end_year="2023",
            current=False,
            description=(
                "Developed CI/CD pipelines, implemented React and Redux component architecture, and used "
                "BDD, TDD, Jest, and Cypress to improve reliability, scalability, and deployment speed."
            ),
        ),
    ]
    educations = [
        EducationPayload(
            institution="Western Governors University",
            degree="Bachelors",
            field_of_study="Software Development",
            start_year="2020",
            end_year="2023",
        ),
        EducationPayload(
            institution="Florida A&M University",
            degree="Associate",
            field_of_study="Computer Science",
            start_year="2014",
            end_year="2016",
        ),
    ]
    return DiceProfilePayload(
        full_name=getattr(profile, "name", "").strip(),
        first_name=first_name,
        last_name=last_name,
        email=getattr(profile, "email", "").strip(),
        phone_number=getattr(profile, "phone_number", "").strip(),
        linkedin_url=getattr(profile, "linkedin_profile", "").strip(),
        website_url=website_url.strip(),
        portfolio_url=portfolio_url.strip(),
        booking_link=booking_link.strip(),
        resume_path=resume_path.strip(),
        profile_photo_path=_ensure_placeholder_profile_photo(),
        headline=headline.strip(),
        summary=summary,
        location=location,
        skills=skills,
        job_titles=job_titles,
        work_experiences=work_experiences,
        educations=educations,
        years_experience=years_experience,
        desired_salary="120000",
        ideal_company_size="51-100 employees",
        ideal_company_age="11-20 years",
        profile_visible=_optional_bool_from_env("DICE_PROFILE_VISIBLE"),
    )
