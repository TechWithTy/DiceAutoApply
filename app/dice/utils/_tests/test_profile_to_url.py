"""
Test for profile_to_url.py: ensures userprofile_to_search_url builds a valid Dice job search URL from profile filters.
"""
from app.dice.utils.profile_to_url import userprofile_to_search_url

def test_userprofile_to_search_url():
    job_title = "Full Stack Engineer"
    url = userprofile_to_search_url(job_title)
    print("Generated URL:", url)
    assert url.startswith("https://www.dice.com/jobs?")
    assert "Full+Stack+Engineer" in url or "Full%20Stack%20Engineer" in url

if __name__ == "__main__":
    test_userprofile_to_search_url()
