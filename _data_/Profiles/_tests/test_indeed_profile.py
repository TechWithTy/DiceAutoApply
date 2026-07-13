from pathlib import Path
from urllib.parse import parse_qs, urlparse

from _data_.Filters.indeedFilterSettings import IndeedJobFilter, indeed_job_filter
from _data_.Profiles.indeed_profile import get_indeed_config
from _data_.Resumes.indeedResumes import get_indeed_resume_config


def test_indeed_profile_is_blue_collar_specific():
    config = get_indeed_config()
    searches = config["searches"]
    candidate = config["candidate"]

    search_text = " ".join(search["base_url"] for search in searches).lower()
    assert "warehouse" in search_text
    assert "general+laborer" in search_text
    assert "developer" not in search_text
    assert "full+stack" not in search_text

    assert "Warehouse Associate" in candidate["preferred_job_titles"]
    assert "Warehouse Operations" in candidate["skills"]
    assert "Python" not in candidate["skills"]
    assert "React" not in candidate["skills"]


def test_indeed_filters_generate_indeed_specific_query_params():
    config = get_indeed_config()
    first_url = config["searches"][0]["base_url"]
    query = parse_qs(urlparse(first_url).query)

    assert query["q"] == ["Warehouse Associate"]
    assert query["l"] == ["Denver, CO"]
    assert query["radius"] == [str(indeed_job_filter.radius)]
    assert query["fromage"] == [str(indeed_job_filter.posted_days)]
    assert query["sort"] == [IndeedJobFilter.Sort.DATE]
    assert query["jt"] == ["fulltime"]
    assert config["filters"]["excluded_keywords"]


def test_indeed_resume_config_points_to_existing_blue_collar_resume():
    resume_config = get_indeed_resume_config()
    resume_path = Path(resume_config["default_resume_path"])

    assert resume_path.name == "indeed_blue_collar_resume.txt"
    assert resume_path.parent.name == "Indeed"
    assert resume_path.exists()
    assert "Warehouse Associate" in resume_config["resumes"][0]["job_titles"]
    assert "Forklift Safety" in resume_config["resumes"][0]["skills"]
