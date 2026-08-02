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

def jobfilter_to_url_args(job_filter, workplace_settings=None):
    """
    Map JobFilter fields to build_dice_search_url keyword arguments.
    Handles enums and string values robustly.
    """
    # Employment types
    employment_types = [_enum_or_str(e) for e in getattr(job_filter, 'employment_types', [])]
    # Employer types
    employer_types = [_enum_or_str(e) for e in getattr(job_filter, 'employer_types', [])]
    # Work setting (workplace types)
    work_setting = workplace_settings if workplace_settings is not None else getattr(job_filter, 'work_setting', None)
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

def userprofile_locations(profile=user_profile) -> list[str]:
    cities = getattr(profile, "cities", None)
    if isinstance(cities, list) and cities:
        country = getattr(profile, "country", "").strip()
        normalized_locations: list[str] = []
        for city in cities:
            if not isinstance(city, str):
                continue
            normalized = city.strip()
            if not normalized:
                continue
            if normalized.casefold() == "remote":
                normalized_locations.append("Remote")
            else:
                normalized_parts = [part.strip() for part in normalized.split(",") if part.strip()]
                if country and (
                    not normalized_parts
                    or normalized_parts[-1].casefold() != country.casefold()
                ):
                    normalized_parts.append(country)
                normalized_locations.append(", ".join(normalized_parts))
        return normalized_locations

    location = ", ".join(
        part for part in [
            getattr(profile, "city", "").strip(),
            getattr(profile, "country", "").strip(),
        ]
        if part
    )
    return [location] if location else []


def userprofile_to_search_url(job_title: str, workplace_settings=None) -> str:
    """
    Build a Dice search URL from the current user_profile and a job title.
    """
    return userprofile_to_search_urls(job_title, workplace_settings=workplace_settings)[0]


def userprofile_to_search_urls(job_title: str, workplace_settings=None) -> list[str]:
    """
    Build Dice search URLs from the current user_profile and a job title,
    one URL per configured city.
    """
    job_filter = user_profile.dice_job_filter
    locations = userprofile_locations(user_profile)
    return [
        build_dice_search_url(
            q=job_title,
            location=location,
            **jobfilter_to_url_args(job_filter, workplace_settings=workplace_settings)
        )
        for location in locations
    ]

# Example usage:
# print(userprofile_to_search_url("Full Stack Engineer"))
