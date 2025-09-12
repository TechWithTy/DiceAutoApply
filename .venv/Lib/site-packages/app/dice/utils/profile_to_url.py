"""
profile_to_url.py
Converts a UserProfile (main_profile) + JobFilter into a Dice search URL using the robust search_url_builder.
"""
from _data_.Profiles.main_profile import user_profile
from app.dice.utils.search_url_builder import build_dice_search_url

def _enum_or_str(val):
    # Helper: returns lowercase string for enum or string
    if hasattr(val, "name"):
        return val.name.lower()
    elif isinstance(val, str):
        return val.lower().replace(" ", "_").replace("-", "_")
    return str(val).lower()

def jobfilter_to_url_args(job_filter):
    """
    Map JobFilter fields to build_dice_search_url keyword arguments.
    Handles enums and string values robustly.
    """
    # Employment types
    employment_types = [_enum_or_str(e) for e in getattr(job_filter, 'employment_types', [])]
    # Employer types
    employer_types = [_enum_or_str(e) for e in getattr(job_filter, 'employer_types', [])]
    # Work setting (workplace types)
    work_setting = getattr(job_filter, 'work_setting', None)
    if isinstance(work_setting, list):
        workplace_types = [_enum_or_str(w) for w in work_setting]
    elif work_setting:
        workplace_types = [_enum_or_str(work_setting)]
    else:
        workplace_types = []
    # Posted date
    posted_date = getattr(job_filter, 'posted_date', None)
    if posted_date:
        posted_date = posted_date.lower().replace(' ', '_')  # e.g., 'today', 'last_3_days'
    # Other fields
    return dict(
        employment_types=employment_types,
        employer_types=employer_types,
        workplace_types=workplace_types,
        posted_date=posted_date,
        easy_apply=getattr(job_filter, 'easy_apply', False),
        radius=getattr(job_filter, 'radius', None),
    )

def userprofile_to_search_url(job_title: str) -> str:
    """
    Build a Dice search URL from the current user_profile and a job title.
    """
    job_filter = user_profile.dice_job_filter
    # Location string
    location = f"{user_profile.city}, {user_profile.country}"
    # Optionally, add geo fields if available
    url = build_dice_search_url(
        q=job_title,
        location=location,
        **jobfilter_to_url_args(job_filter)
    )
    return url

# Example usage:
# print(userprofile_to_search_url("Full Stack Engineer"))
