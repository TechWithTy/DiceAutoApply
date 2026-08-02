from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class JobFilter:
    class WorkSetting:
        ONSITE = "On-Site"
        REMOTE = "Remote"
        HYBRID = "Hybrid"

    class EmploymentType:
        FULL_TIME = "Full-time"
        PART_TIME = "Part-time"
        CONTRACT = "Contract"
        THIRD_PARTY = "Third Party"

    class EmployerType:
        DIRECT_HIRE = "Direct Hire"
        RECRUITER = "Recruiter"
        OTHER = "Other"
    class PostedDate:
        ANY_DATE = "Any Date"
        TODAY = "Today"
        LAST_3_DAYS = "Last 3 Days"
        LAST_7_DAYS = "Last 7 Days"

    work_setting: List[str] = field(default_factory=list)
    posted_date: Optional[str] = None  # Only one can be selected
    employment_types: List[str] = field(default_factory=list)  # Multiple can be selected
    willing_to_sponsor: bool = False  # Only one can be true
    employer_types: List[str] = field(default_factory=list)  # Multiple can be selected
    easy_apply: bool = False  # Only one can be true

    def _validate_work_setting(self, setting: str) -> str:
        if setting not in [self.WorkSetting.ONSITE, self.WorkSetting.REMOTE, self.WorkSetting.HYBRID]:
            raise ValueError(f"Invalid work setting: {setting}")
        return setting

    def set_work_setting(self, setting: Optional[str | List[str]]):
        if setting is None:
            self.work_setting = []
            return
        if isinstance(setting, list):
            self.work_setting = []
            for item in setting:
                self.add_work_setting(item)
            return
        self.work_setting = [self._validate_work_setting(setting)]

    def add_work_setting(self, setting: str):
        normalized = self._validate_work_setting(setting)
        if normalized not in self.work_setting:
            self.work_setting.append(normalized)

    def set_posted_date(self, date: str):
        if date not in [self.PostedDate.ANY_DATE, self.PostedDate.TODAY, self.PostedDate.LAST_3_DAYS, self.PostedDate.LAST_7_DAYS]:
            raise ValueError(f"Invalid posted date: {date}")
        self.posted_date = date

    def add_employment_type(self, employment_type: str):
        if employment_type not in [self.EmploymentType.FULL_TIME, self.EmploymentType.PART_TIME, self.EmploymentType.CONTRACT, self.EmploymentType.THIRD_PARTY]:
            raise ValueError(f"Invalid employment type: {employment_type}")
        if employment_type not in self.employment_types:
            self.employment_types.append(employment_type)

    def add_employer_type(self, employer_type: str):
        if employer_type not in [self.EmployerType.DIRECT_HIRE, self.EmployerType.RECRUITER, self.EmployerType.OTHER]:
            raise ValueError(f"Invalid employer type: {employer_type}")
        if employer_type not in self.employer_types:
            self.employer_types.append(employer_type)

    def set_willing_to_sponsor(self, willing: bool):
        self.willing_to_sponsor = willing

    def set_easy_apply(self, easy: bool):
        if easy is not True:
            raise ValueError("easy_apply can only be set to True.")
        self.easy_apply = easy

# Default Dice filter configuration used by the app/profile modules.
dice_job_filter = JobFilter()
# Dice's Last 7 Days option includes both 0-3 and 4-7 day postings.
dice_job_filter.set_posted_date(JobFilter.PostedDate.LAST_7_DAYS)
dice_job_filter.set_work_setting(
    [
        JobFilter.WorkSetting.REMOTE,
        JobFilter.WorkSetting.HYBRID,
        JobFilter.WorkSetting.ONSITE,
    ]
)
dice_job_filter.add_employment_type(JobFilter.EmploymentType.FULL_TIME)
dice_job_filter.add_employment_type(JobFilter.EmploymentType.CONTRACT)
dice_job_filter.add_employment_type(JobFilter.EmploymentType.THIRD_PARTY)
dice_job_filter.set_willing_to_sponsor(False)
dice_job_filter.add_employer_type(JobFilter.EmployerType.DIRECT_HIRE)
dice_job_filter.add_employer_type(JobFilter.EmployerType.RECRUITER)
dice_job_filter.set_easy_apply(True)
