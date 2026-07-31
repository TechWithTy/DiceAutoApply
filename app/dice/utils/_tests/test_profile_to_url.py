"""
Test for profile_to_url.py: ensures userprofile_to_search_url builds a valid Dice job search URL from profile filters.
"""
from _data_.Filters.diceFilterSettings import JobFilter
from app.dice.utils.profile_to_url import jobfilter_to_url_args
from app.dice.utils.profile_to_url import userprofile_to_search_url

def test_userprofile_to_search_url():
    job_title = "Full Stack Engineer"
    url = userprofile_to_search_url(job_title)
    print("Generated URL:", url)
    assert url.startswith("https://www.dice.com/jobs?")
    assert "Full+Stack+Engineer" in url or "Full%20Stack%20Engineer" in url
    assert "filters.workplaceTypes=Remote" not in url


def test_jobfilter_to_url_args_omits_workplace_types_when_unset():
    job_filter = JobFilter()
    job_filter.set_posted_date(JobFilter.PostedDate.LAST_3_DAYS)
    job_filter.set_work_setting(None)

    args = jobfilter_to_url_args(job_filter)

    assert args["workplace_types"] == []

if __name__ == "__main__":
    test_userprofile_to_search_url()
