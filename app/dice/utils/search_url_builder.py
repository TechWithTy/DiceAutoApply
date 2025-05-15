"""
search_url_builder.py
Handles robust Dice job search URL construction for all filter options.
"""
from urllib.parse import urlencode, quote_plus
from typing import List, Optional

# Employment types accepted by Dice
EMPLOYMENT_TYPE_MAP = {
    "fulltime": "FULLTIME",
    "contract": "CONTRACTS",
    "third_party": "THIRD_PARTY",
    "internship": "INTERNSHIP",
    "parttime": "PARTTIME"
}

# Employer types
EMPLOYER_TYPE_MAP = {
    "direct_hire": "Direct Hire",
    "recruiter": "Recruiter"
}

# Workplace types
WORKPLACE_TYPE_MAP = {
    "remote": "Remote",
    "on_site": "On-Site",
    "hybrid": "Hybrid"
}

# Posted date
POSTED_DATE_MAP = {
    None: None,
    "none": None,
    "today": "ONE",
    "last_3_days": "THREE",
    "last_7_days": "SEVEN"
}

# Radius options (miles)
RADIUS_OPTIONS = [None, 10, 30, 50, 75]


def build_dice_search_url(
    q: str,
    location: Optional[str] = None,
    radius: Optional[int] = None,
    employment_types: Optional[List[str]] = None,
    employer_types: Optional[List[str]] = None,
    workplace_types: Optional[List[str]] = None,
    posted_date: Optional[str] = None,
    easy_apply: bool = False,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    country_code: Optional[str] = None,
    location_precision: Optional[str] = None,
    admin_district_code: Optional[str] = None
) -> str:
    """
    Build a Dice job search URL with all filter options.
    Args:
        q: search keywords
        location: city/state/country string
        radius: search radius in miles (None, 10, 30, 50, 75)
        employment_types: list of employment type keys (see EMPLOYMENT_TYPE_MAP)
        employer_types: list of employer type keys (see EMPLOYER_TYPE_MAP)
        workplace_types: list of workplace type keys (see WORKPLACE_TYPE_MAP)
        posted_date: 'none', 'today', 'last_3_days', 'last_7_days'
        easy_apply: True/False
        latitude, longitude, country_code, location_precision, admin_district_code: optional geo fields
    Returns:
        Full Dice job search URL
    """
    base_url = "https://www.dice.com/jobs"
    params = {}

    # Python 3.10+ structural pattern matching ("match" statement)
    # Note: switch/case in Python = "match", but for sequential filter logic, 
    # we use match for each variable, not as a replacement for if-chains on different variables.
    # Here we implement each as a match-case for clarity.
    match easy_apply:
        case True:
            params["filters.easyApply"] = "true"
    match posted_date:
        case str() if posted_date:
            pd = POSTED_DATE_MAP.get(posted_date, None)
            if pd:
                params["filters.postedDate"] = pd
    match employment_types:
        case list() if employment_types:
            mapped = [EMPLOYMENT_TYPE_MAP[e] for e in employment_types if e in EMPLOYMENT_TYPE_MAP]
            if mapped:
                params["filters.employmentType"] = "|".join(mapped)
    match employer_types:
        case list() if employer_types:
            mapped = [EMPLOYER_TYPE_MAP[e] for e in employer_types if e in EMPLOYER_TYPE_MAP]
            if mapped:
                params["filters.employerType"] = "|".join(mapped)
    match workplace_types:
        case list() if workplace_types:
            mapped = [WORKPLACE_TYPE_MAP[w] for w in workplace_types if w in WORKPLACE_TYPE_MAP]
            if mapped:
                params["filters.workplaceTypes"] = "|".join(mapped)
    match radius:
        case int() if radius in RADIUS_OPTIONS and radius is not None:
            params["radius"] = str(radius)
    match location:
        case str() if location:
            params["location"] = location
    match q:
        case str() if q:
            params["q"] = q
    match latitude:
        case float() | int() if latitude is not None:
            params["latitude"] = str(latitude)
    match longitude:
        case float() | int() if longitude is not None:
            params["longitude"] = str(longitude)
    match country_code:
        case str() if country_code:
            params["countryCode"] = country_code
    match location_precision:
        case str() if location_precision:
            params["locationPrecision"] = location_precision
    match admin_district_code:
        case str() if admin_district_code:
            params["adminDistrictCode"] = admin_district_code

    return f"{base_url}?" + urlencode(params, doseq=True, safe="|+")

# Example usage:
# url = build_dice_search_url(
#     q="Full Stack Engineer",
#     location="Denver, CO, USA",
#     radius=10,
#     employment_types=["fulltime", "contract", "third_party"],
#     employer_types=["direct_hire", "recruiter"],
#     workplace_types=["remote", "on_site", "hybrid"],
#     posted_date="today",
#     easy_apply=True,
#     latitude=39.7392358,
#     longitude=-104.990251,
#     country_code="US",
#     location_precision="City",
#     admin_district_code="CO"
# )
# print(url)
