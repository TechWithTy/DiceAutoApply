from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class IndeedJobFilter:
    class WorkSetting:
        REMOTE = "Remote"
        HYBRID = "Hybrid"
        ONSITE = "On-site"

    class EmploymentType:
        FULL_TIME = "Full-time"
        CONTRACT = "Contract"
        PART_TIME = "Part-time"
        TEMPORARY = "Temporary"

    class Sort:
        DATE = "date"
        RELEVANCE = ""

    work_setting: str = WorkSetting.ONSITE
    preferred_locations: List[str] = field(default_factory=lambda: ["Denver, CO", "Aurora, CO", "Lakewood, CO"])
    posted_days: Optional[int] = 3
    radius: int = 25
    sort: str = Sort.DATE
    employment_types: List[str] = field(
        default_factory=lambda: [
            IndeedJobFilter.EmploymentType.FULL_TIME,
            IndeedJobFilter.EmploymentType.CONTRACT,
            IndeedJobFilter.EmploymentType.TEMPORARY,
        ]
    )
    only_indeed_apply: bool = False
    excluded_keywords: List[str] = field(
        default_factory=lambda: [
            "senior manager",
            "director",
            "principal",
            "clearance required",
            "cdl required",
            "registered nurse",
            "software",
            "developer",
        ]
    )


indeed_job_filter = IndeedJobFilter()
