import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlencode

from dotenv import load_dotenv

from _data_.Filters.indeedFilterSettings import indeed_job_filter
from _data_.Resumes.indeedResumes import get_indeed_resume_config

load_dotenv()


@dataclass(frozen=True)
class IndeedSearchPreference:
    query: str
    location: str = "Remote"
    radius: int = 25
    start: int = 0
    end: int = 0
    posted_days: Optional[int] = 3
    sort: str = "date"
    job_type: Optional[str] = None
    only_indeed_apply: bool = False

    def base_url(self, site_url: str) -> str:
        indeed_job_types = {
            "Full-time": "fulltime",
            "Part-time": "parttime",
            "Contract": "contract",
            "Temporary": "temporary",
        }
        params = {
            "q": self.query,
            "l": self.location,
            "radius": self.radius,
        }
        if self.posted_days is not None:
            params["fromage"] = self.posted_days
        if self.sort:
            params["sort"] = self.sort
        if self.job_type:
            params["jt"] = indeed_job_types.get(self.job_type, self.job_type)
        return f"{site_url.rstrip('/')}/jobs?{urlencode(params)}"

    def as_config(self, site_url: str) -> Dict[str, object]:
        return {
            "base_url": self.base_url(site_url),
            "start": self.start,
            "end": self.end,
            "only_indeed_apply": self.only_indeed_apply,
        }


@dataclass(frozen=True)
class IndeedCandidateProfile:
    name: str = os.getenv("INDEED_NAME", os.getenv("NAME", "Blue Collar Operations Candidate"))
    email: str = os.getenv("INDEED_EMAIL", os.getenv("EMAIL", ""))
    phone_number: str = os.getenv("INDEED_PHONE_NUMBER", os.getenv("PHONE_NUMBER", ""))
    city: str = os.getenv("INDEED_CITY", "Denver")
    state: str = os.getenv("INDEED_STATE", "CO")
    country: str = "USA"
    linkedin_profile: str = os.getenv("INDEED_LINKEDIN_PROFILE", "")
    about_me: str = (
        "Reliable hands-on operations worker seeking warehouse, general labor, delivery, "
        "production, facilities, or maintenance support roles in the Denver metro area."
    )
    preferred_job_titles: List[str] = field(
        default_factory=lambda: [
            "Warehouse Associate",
            "General Laborer",
            "Material Handler",
            "Delivery Driver",
            "Maintenance Technician",
            "Production Worker",
            "Facilities Technician",
            "Forklift Operator",
        ]
    )
    skills: List[str] = field(
        default_factory=lambda: [
            "Warehouse Operations",
            "Inventory Control",
            "Shipping and Receiving",
            "Loading and Unloading",
            "Pallet Jack",
            "Forklift Safety",
            "Order Picking",
            "Packing",
            "Hand Tools",
            "Power Tools",
            "Preventive Maintenance",
            "OSHA Safety",
            "Customer Service",
            "Route Delivery",
            "Reliable Attendance",
            "Team Communication",
        ]
    )
    certifications: List[str] = field(
        default_factory=lambda: [
            "Driver's License",
            "Forklift certification preferred",
            "OSHA safety training preferred",
        ]
    )

    def as_config(self, resume_config: Dict[str, object]) -> Dict[str, object]:
        return {
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "linkedin_profile": self.linkedin_profile,
            "online_presence": {},
            "about_me": self.about_me,
            "preferred_job_titles": self.preferred_job_titles,
            "skills": self.skills,
            "certifications": self.certifications,
            "resume_path": resume_config["default_resume_path"],
            "resumes": resume_config["resumes"],
        }


@dataclass(frozen=True)
class IndeedAutomationProfile:
    site_url: str = "https://www.indeed.com"
    auth_hl: str = "en"
    language: str = "en"
    user_data_dir: str = "user_data_dir"
    dry_run: bool = True
    max_jobs: int = 1
    login_wait_seconds: int = 60
    only_indeed_apply: bool = False
    candidate: IndeedCandidateProfile = field(default_factory=IndeedCandidateProfile)
    searches: List[IndeedSearchPreference] = field(default_factory=list)

    def as_bot_config(self) -> Dict[str, object]:
        resume_config = get_indeed_resume_config()
        return {
            "searches": [search.as_config(self.site_url) for search in self.searches],
            "application": {
                "dry_run": self.dry_run,
                "max_jobs": self.max_jobs,
                "login_wait_seconds": self.login_wait_seconds,
                "only_indeed_apply": self.only_indeed_apply,
            },
            "filters": {
                "work_setting": indeed_job_filter.work_setting,
                "preferred_locations": indeed_job_filter.preferred_locations,
                "posted_days": indeed_job_filter.posted_days,
                "radius": indeed_job_filter.radius,
                "sort": indeed_job_filter.sort,
                "employment_types": indeed_job_filter.employment_types,
                "only_indeed_apply": indeed_job_filter.only_indeed_apply,
                "excluded_keywords": indeed_job_filter.excluded_keywords,
            },
            "camoufox": {
                "user_data_dir": self.user_data_dir,
                "site_url": self.site_url,
                "auth_hl": self.auth_hl,
                "language": self.language,
            },
            "candidate": self.candidate.as_config(resume_config),
        }


indeed_profile = IndeedAutomationProfile(
    searches=[
        IndeedSearchPreference(
            query="Warehouse Associate",
            location=indeed_job_filter.preferred_locations[0],
            radius=indeed_job_filter.radius,
            posted_days=indeed_job_filter.posted_days,
            sort=indeed_job_filter.sort,
            job_type=indeed_job_filter.employment_types[0],
            only_indeed_apply=indeed_job_filter.only_indeed_apply,
            end=20,
        ),
        IndeedSearchPreference(
            query="General Laborer",
            location=indeed_job_filter.preferred_locations[0],
            radius=indeed_job_filter.radius,
            posted_days=indeed_job_filter.posted_days,
            sort=indeed_job_filter.sort,
            job_type=indeed_job_filter.employment_types[0],
            only_indeed_apply=indeed_job_filter.only_indeed_apply,
            end=20,
        ),
        IndeedSearchPreference(
            query="Material Handler",
            location=indeed_job_filter.preferred_locations[0],
            radius=indeed_job_filter.radius,
            posted_days=indeed_job_filter.posted_days,
            sort=indeed_job_filter.sort,
            job_type=indeed_job_filter.employment_types[0],
            only_indeed_apply=indeed_job_filter.only_indeed_apply,
            end=20,
        ),
        IndeedSearchPreference(
            query="Delivery Driver",
            location=indeed_job_filter.preferred_locations[0],
            radius=indeed_job_filter.radius,
            posted_days=indeed_job_filter.posted_days,
            sort=indeed_job_filter.sort,
            job_type=indeed_job_filter.employment_types[0],
            only_indeed_apply=indeed_job_filter.only_indeed_apply,
            end=20,
        ),
        IndeedSearchPreference(
            query="Maintenance Technician",
            location=indeed_job_filter.preferred_locations[0],
            radius=indeed_job_filter.radius,
            posted_days=indeed_job_filter.posted_days,
            sort=indeed_job_filter.sort,
            job_type=indeed_job_filter.employment_types[0],
            only_indeed_apply=indeed_job_filter.only_indeed_apply,
            end=20,
        ),
        IndeedSearchPreference(
            query="Production Worker",
            location=indeed_job_filter.preferred_locations[0],
            radius=indeed_job_filter.radius,
            posted_days=indeed_job_filter.posted_days,
            sort=indeed_job_filter.sort,
            job_type=indeed_job_filter.employment_types[0],
            only_indeed_apply=indeed_job_filter.only_indeed_apply,
            end=20,
        ),
    ],
)


def get_indeed_config() -> Dict[str, object]:
    """Return explicit blue-collar Indeed automation settings."""
    return indeed_profile.as_bot_config()
