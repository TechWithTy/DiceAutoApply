"""
Normalize the Dice profile data we want to create or edit.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from _data_.Profiles.main_profile import user_profile


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
    headline: str
    summary: str
    location: str
    skills: List[str]
    job_titles: List[str]
    years_experience: int


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
    return paths[0] if paths else ""


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
        headline=headline.strip(),
        summary=summary,
        location=location,
        skills=skills,
        job_titles=job_titles,
        years_experience=years_experience,
    )
