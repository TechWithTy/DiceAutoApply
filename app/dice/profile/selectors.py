"""
Selector registry for Dice profile pages.

The page structure is expected to evolve, so every control has fallback locators.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


PROFILE_URLS = [
    "https://www.dice.com/dashboard/profiles-classic",
    "https://www.dice.com/dashboard/profiles",
]


@dataclass(frozen=True)
class ProfileSelectorRegistry:
    profile_entry_points: List[str] = field(default_factory=lambda: [
        'a[href*="/dashboard/profiles-classic"]',
        'a[href*="/dashboard/profiles"]',
        'button:has-text("Profile")',
        'a:has-text("Profile")',
    ])
    create_profile_buttons: List[str] = field(default_factory=lambda: [
        'button:has-text("Create profile")',
        'button:has-text("Create Profile")',
        'button:has-text("Add profile")',
        'button:has-text("Add Profile")',
        'a:has-text("Create profile")',
    ])
    edit_profile_buttons: List[str] = field(default_factory=lambda: [
        'button:has-text("Edit profile")',
        'button:has-text("Edit Profile")',
        'button:has-text("Edit")',
        'a:has-text("Edit")',
    ])
    save_buttons: List[str] = field(default_factory=lambda: [
        'dhi-candidates-wired-candidate-profile button[type="submit"]',
        'dhi-candidates-wired-onboarding-flow-state-controller button[type="submit"]',
        'dhi-candidates-wired-candidate-profile seds-button[type="submit"]',
        'dhi-candidates-wired-onboarding-flow-state-controller seds-button[type="submit"]',
        'seds-button[type="submit"]',
        'button:has-text("Save profile")',
        'button:has-text("Save changes")',
        'button:has-text("Save")',
        'button[type="submit"]',
    ])
    section_buttons: Dict[str, List[str]] = field(default_factory=lambda: {
        "identity": [
            'button:has-text("Profile")',
            'button:has-text("Add Desired Job Title")',
            'button:has-text("What do you want for your next job title?")',
            'button:has-text("How many years of experience do you have?")',
        ],
        "contact": [
            'button:has-text("Location")',
            'button:has-text("Where are you currently located?")',
            'button:has-text("Do you want to add a phone number?")',
        ],
        "summary": [
            'button:has-text("About")',
            'button:has-text("Summary")',
            'button:has-text("Edit About Me")',
        ],
        "resume": [
            'button:has-text("Resume")',
            'button:has-text("Upload resume")',
        ],
        "skills": [
            'button:has-text("Skills")',
            'button:has-text("Add skill")',
            'button:has-text("Add Skills")',
            'button:has-text("Edit Skills")',
        ],
        "experience": [
            'seds-button:has-text("Add work experience")',
            'seds-button:has-text("Add experience")',
            'button:has-text("Add work experience")',
        ],
        "ideal_job": [
            'seds-button:has-text("Edit Ideal Job")',
            'button:has-text("Edit Ideal Job")',
            'button:has-text("What do you want for your next job title?")',
        ],
        "ideal_company": [
            'seds-button:has-text("Edit Ideal Company")',
            'button:has-text("Edit Ideal Company")',
            'button[data-related-input="ideal_company_size"]',
            'button[data-related-input="ideal_company_age"]',
        ],
        "education": [
            'seds-button:has-text("Add Education")',
            'seds-button:has-text("Add education")',
            'button:has-text("Add Education")',
            'button:has-text("Add education")',
        ],
        "social": [
            'seds-button:has-text("Edit Social Profiles")',
            'button:has-text("Edit Social Profiles")',
            'button:has-text("Social Profiles")',
        ],
    })
    input_candidates: Dict[str, List[str]] = field(default_factory=lambda: {
        "first_name": [
            'input[name="first_name"]',
            'input[id="first_name"]',
            'input[aria-label="First Name"]',
        ],
        "last_name": [
            'input[name="last_name"]',
            'input[id="last_name"]',
            'input[aria-label="Last Name"]',
        ],
        "years_experience": [
            'input[name="years_experience"]',
            'input[id="years_experience"]',
            'input[aria-label="Years Experience"]',
        ],
        "job_title": [
            'input[placeholder="Preferred Job Title"]',
            'input[aria-label="Ideal Job"]',
            'input[name="job_title"]',
            'input[id*="job_title" i]',
        ],
        "summary": [
            'textarea[name*="summary" i]',
            'textarea[id*="summary" i]',
            'textarea[placeholder*="summary" i]',
            '[contenteditable="true"][aria-label*="summary" i]',
        ],
        "email": [
            'input[type="email"]',
            'input[name*="email" i]',
            'input[id*="email" i]',
        ],
        "phone_number": [
            'input[type="tel"]',
            'input[name*="phone" i]',
            'input[id*="phone" i]',
        ],
        "years_experience_value": [
            'input[name="years_experience"]',
            'input[id*="years_experience" i]',
        ],
        "linkedin_url": [
            'input[name*="linkedin" i]',
            'input[id*="linkedin" i]',
            'input[placeholder*="linkedin" i]',
        ],
        "website_url": [
            'input[name*="website" i]',
            'input[id*="website" i]',
            'input[placeholder*="website" i]',
        ],
        "portfolio_url": [
            'input[name*="portfolio" i]',
            'input[id*="portfolio" i]',
        ],
        "booking_link": [
            'input[name*="booking" i]',
            'input[id*="booking" i]',
        ],
        "location": [
            'input[name="city_state"]',
            'input[name="postalCode"]',
            'input[name="location.country"]',
            'input[id*="location" i]',
            'input[placeholder*="location" i]',
        ],
        "skills_input": [
            'input[placeholder*="skill" i]',
            'input[name*="skill" i]',
            'input[id*="skill" i]',
            '[contenteditable="true"][aria-label*="skill" i]',
        ],
        "salary": [
            'input[name="compensation_annual"]',
            'input[name*="salary" i]',
            'input[name*="compensation" i]',
            'input[aria-label*="salary" i]',
            'input[placeholder*="salary" i]',
        ],
        "school": [
            'input[name="institution"]',
            'input[name*="institution" i]',
            'input[name*="school" i]',
            'input[name*="university" i]',
            'input[aria-label*="school" i]',
            'input[aria-label*="institution" i]',
            'input[placeholder*="school" i]',
        ],
        "degree": [
            'select[name="type"]',
            'input[name*="degree" i]',
            'input[aria-label*="degree" i]',
            'input[placeholder*="degree" i]',
            'select[name*="degree" i]',
            'select[aria-label*="degree" i]',
        ],
        "field_of_study": [
            'input[name*="field" i]',
            'input[name*="major" i]',
            'input[name*="study" i]',
            'input[aria-label*="field" i]',
            'input[aria-label*="major" i]',
            'input[placeholder*="field" i]',
        ],
        "education_location": [
            'input[name="location"]',
            'input[aria-label*="location" i]',
            'input[placeholder*="location" i]',
        ],
    })
    resume_upload_candidates: List[str] = field(default_factory=lambda: [
        'input#resume-upload',
        'input[type="file"]',
        'input[name*="resume" i]',
        'input[id*="resume" i]',
        'button:has-text("Upload resume")',
        'button:has-text("Add resume")',
    ])
    success_toasts: List[str] = field(default_factory=lambda: [
        '[role="status"]',
        '[aria-live="polite"]',
        'div:has-text("saved")',
        'div:has-text("updated")',
    ])
    visibility_toggle_candidates: List[str] = field(default_factory=lambda: [
        'input[role="switch"][aria-label="ON"]',
        'input[role="switch"][aria-label="OFF"]',
        'input[type="checkbox"][role="switch"]',
        'dhi-candidates-toggle input[type="checkbox"]',
    ])
