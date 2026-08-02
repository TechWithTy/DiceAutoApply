"""
Test for profile_to_url.py: ensures userprofile_to_search_url builds a valid Dice job search URL from profile filters.
"""
from types import SimpleNamespace

from _data_.Filters.diceFilterSettings import JobFilter
from app.dice.utils import profile_to_url as profile_to_url_module
from app.dice.utils.profile_to_url import jobfilter_to_url_args
from app.dice.utils.profile_to_url import userprofile_locations
from app.dice.utils.profile_to_url import userprofile_to_search_url
from app.dice.utils.profile_to_url import userprofile_to_search_urls

def test_userprofile_to_search_url():
    job_title = "Full Stack Engineer"
    url = userprofile_to_search_url(job_title)
    print("Generated URL:", url)
    assert url.startswith("https://www.dice.com/jobs?")
    assert "Full+Stack+Engineer" in url or "Full%20Stack%20Engineer" in url
    assert "filters.workplaceTypes=" in url


def test_jobfilter_to_url_args_omits_workplace_types_when_unset():
    job_filter = JobFilter()
    job_filter.set_posted_date(JobFilter.PostedDate.LAST_3_DAYS)
    job_filter.set_work_setting(None)

    args = jobfilter_to_url_args(job_filter)

    assert args["workplace_types"] == []


def test_jobfilter_to_url_args_supports_multiple_workplace_types():
    job_filter = JobFilter()
    job_filter.set_work_setting(
        [
            JobFilter.WorkSetting.REMOTE,
            JobFilter.WorkSetting.HYBRID,
            JobFilter.WorkSetting.ONSITE,
        ]
    )

    args = jobfilter_to_url_args(job_filter)

    assert args["workplace_types"] == ["remote", "hybrid", "on_site"]


def test_userprofile_locations_uses_multiple_cities():
    profile = SimpleNamespace(cities=["Remote", "Denver", "Austin"], country="USA")

    locations = userprofile_locations(profile)

    assert locations == ["Remote", "Denver, USA", "Austin, USA"]


def test_userprofile_to_search_urls_builds_one_url_per_city(monkeypatch):
    job_filter = JobFilter()
    job_filter.set_posted_date(JobFilter.PostedDate.LAST_3_DAYS)
    job_filter.set_work_setting(
        [
            JobFilter.WorkSetting.REMOTE,
            JobFilter.WorkSetting.HYBRID,
            JobFilter.WorkSetting.ONSITE,
        ]
    )
    profile = SimpleNamespace(
        cities=["Remote", "Denver", "Austin"],
        country="USA",
        dice_job_filter=job_filter,
    )
    monkeypatch.setattr(profile_to_url_module, "user_profile", profile)

    urls = userprofile_to_search_urls("Full Stack Engineer")

    assert len(urls) == 3
    assert "location=Remote" in urls[0]
    assert "location=Denver%2C+USA" in urls[1]
    assert "location=Austin%2C+USA" in urls[2]
    assert all("filters.workplaceTypes=Remote|Hybrid|On-Site" in url for url in urls)


def test_userprofile_to_search_urls_can_override_workplace_types(monkeypatch):
    job_filter = JobFilter()
    job_filter.set_work_setting(
        [
            JobFilter.WorkSetting.REMOTE,
            JobFilter.WorkSetting.HYBRID,
            JobFilter.WorkSetting.ONSITE,
        ]
    )
    profile = SimpleNamespace(
        cities=["Remote"],
        country="USA",
        dice_job_filter=job_filter,
    )
    monkeypatch.setattr(profile_to_url_module, "user_profile", profile)

    url = userprofile_to_search_urls(
        "Full Stack Engineer",
        workplace_settings=[JobFilter.WorkSetting.REMOTE],
    )[0]

    assert "filters.workplaceTypes=Remote" in url
    assert "filters.workplaceTypes=Remote|Hybrid|On-Site" not in url


def test_userprofile_locations_preserves_state_and_appends_country_once():
    profile = SimpleNamespace(cities=["Remote", "Denver, CO", "Austin, TX, USA"], country="USA")

    locations = userprofile_locations(profile)

    assert locations == ["Remote", "Denver, CO, USA", "Austin, TX, USA"]

if __name__ == "__main__":
    test_userprofile_to_search_url()
