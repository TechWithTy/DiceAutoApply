from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class IndeedResume:
    label: str
    path: str
    job_titles: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    default: bool = False

    def existing_path(self) -> Optional[str]:
        configured = Path(self.path)
        candidates = [configured]
        if not configured.is_absolute():
            candidates.append(Path.cwd() / configured)
            candidates.append(Path(__file__).resolve().parents[2] / configured)
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return None

    def as_config(self) -> Dict[str, object]:
        return {
            "label": self.label,
            "path": self.existing_path() or self.path,
            "job_titles": self.job_titles,
            "skills": self.skills,
            "default": self.default,
        }


_blue_collar_resume = "_data_\\Resumes\\Indeed\\indeed_blue_collar_resume.txt"
_fallback_resume = "_data_\\Resumes\\Dice\\8-5-24-Ai-Full-Stack.pdf"

indeed_resumes = [
    IndeedResume(
        label="Indeed Blue Collar Operations Resume",
        path=_blue_collar_resume,
        job_titles=[
            "Warehouse Associate",
            "General Laborer",
            "Material Handler",
            "Delivery Driver",
            "Maintenance Technician",
            "Production Worker",
        ],
        skills=[
            "Warehouse Operations",
            "Inventory Control",
            "Shipping and Receiving",
            "Loading and Unloading",
            "Pallet Jack",
            "Forklift Safety",
            "Order Picking",
            "Hand Tools",
            "Preventive Maintenance",
            "OSHA Safety",
            "Customer Service",
            "Route Delivery",
        ],
        default=True,
    ),
    IndeedResume(
        label="Indeed Fallback Resume",
        path=_fallback_resume,
        job_titles=["General Laborer", "Warehouse Associate"],
        skills=["Safety", "Reliable Attendance", "Teamwork", "Material Handling"],
    ),
]


def default_indeed_resume() -> IndeedResume:
    for resume in indeed_resumes:
        if resume.default and resume.existing_path():
            return resume
    for resume in indeed_resumes:
        if resume.existing_path():
            return resume
    return indeed_resumes[0]


def get_indeed_resume_config() -> Dict[str, object]:
    selected = default_indeed_resume()
    return {
        "default_resume_path": selected.existing_path() or selected.path,
        "resumes": [resume.as_config() for resume in indeed_resumes],
    }
