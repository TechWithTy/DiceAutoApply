import csv
from collections import deque
from types import SimpleNamespace

import app.dice.utils.apply as apply_module


class _CountLocator:
    def __init__(self, count=0):
        self._count = count

    def count(self):
        return self._count


class _DetailPage:
    def __init__(self, title):
        self.title = title
        self.url = ""
        self.closed = False

    def goto(self, url):
        self.url = url

    def wait_for_load_state(self, *_args, **_kwargs):
        return None

    def evaluate(self, script, *_args):
        if script == "document.title":
            return self.title
        return None

    def query_selector(self, *_args, **_kwargs):
        return None

    def locator(self, *_args, **_kwargs):
        return _CountLocator(0)

    def close(self):
        self.closed = True


class _RootPage:
    def __init__(self, detail_pages):
        self.context = self
        self._detail_pages = deque(detail_pages)

    def new_page(self):
        return self._detail_pages.popleft()


def _read_rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_write_job_titles_records_apply_outcomes(tmp_path, monkeypatch):
    pages = [
        _DetailPage("Success Engineer - Remote"),
        _DetailPage("Already Applied Engineer - Remote"),
        _DetailPage("No Easy Apply Engineer - Remote"),
        _DetailPage("Failed Engineer - Remote"),
    ]
    root_page = _RootPage(pages)
    csv_file = tmp_path / "results.csv"
    outcomes = iter(["success", "already_applied", "no_easy_apply", "failed"])

    monkeypatch.setattr(apply_module, "evaluate_and_apply", lambda *_args, **_kwargs: next(outcomes))
    monkeypatch.setattr(apply_module, "_dump_no_apply_debug", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        apply_module,
        "user_profile",
        type("Profile", (), {"cities": ["Remote"], "city": "Remote"})(),
    )

    result = apply_module.write_job_titles_to_file(
        root_page,
        ["job-success", "job-already", "job-no-button", "job-failed"],
        "https://www.dice.com/jobs?q=python&location=Remote",
        csv_file=str(csv_file),
    )

    assert result == (1, 1, ["Failed Engineer - Remote"], 2, 1, 1, 1, 4)
    rows = _read_rows(csv_file)
    assert [row["job_id"] for row in rows] == ["job-success", "job-already", "job-no-button", "job-failed"]
    assert [row["status"] for row in rows] == ["success", "already_applied", "no_apply_button", "failed"]
    assert rows[0]["job_url"].endswith("/job-success?q=python&location=Remote")


def test_write_job_titles_skips_known_applied_jobs(tmp_path, monkeypatch):
    root_page = _RootPage([_DetailPage("Should Not Open")])
    csv_file = tmp_path / "results.csv"
    calls = []

    monkeypatch.setattr(apply_module, "evaluate_and_apply", lambda *_args, **_kwargs: calls.append("called"))
    monkeypatch.setattr(
        apply_module,
        "user_profile",
        type("Profile", (), {"cities": ["Remote"], "city": "Remote"})(),
    )

    result = apply_module.write_job_titles_to_file(
        root_page,
        ["job-known"],
        "https://www.dice.com/jobs?q=python",
        csv_file=str(csv_file),
        known_applied_job_ids={"job-known"},
    )

    assert result == (0, 0, [], 1, 1, 0, 0, 0)
    assert calls == []
    assert _read_rows(csv_file) == []


def test_load_applied_job_ids_reads_success_and_already_applied(tmp_path):
    csv_file = tmp_path / "results.csv"
    csv_file.write_text(
        "job_id,job_title,job_url,datetime,status,error_message\n"
        "job-success,Engineer,https://www.dice.com/job-detail/job-success,,success,\n"
        "job-old,Engineer,https://www.dice.com/job-detail/job-old,,already_applied,\n"
        "job-failed,Engineer,https://www.dice.com/job-detail/job-failed,,failed,\n",
        encoding="utf-8",
    )

    assert apply_module.load_applied_job_ids(str(csv_file)) == {"job-success", "job-old"}


def test_write_job_titles_skips_out_of_area_jobs_but_allows_remote(tmp_path, monkeypatch):
    pages = [
        _DetailPage("Senior Full Stack Developer - FourthSquare - New York, NY, US | Dice.com"),
        _DetailPage("Dispatch Engineer - Remote in New York, NY, US | Dice.com"),
    ]
    root_page = _RootPage(pages)
    csv_file = tmp_path / "results.csv"
    calls = []

    monkeypatch.setattr(
        apply_module,
        "evaluate_and_apply",
        lambda page, *_args, **_kwargs: calls.append(page.title) or "success",
    )
    monkeypatch.setattr(
        apply_module,
        "user_profile",
        type("Profile", (), {"cities": ["Remote", "Denver", "Boulder", "Aurora"], "city": "Remote"})(),
    )

    result = apply_module.write_job_titles_to_file(
        root_page,
        ["job-ny", "job-remote-ny"],
        "https://www.dice.com/jobs?q=python&location=Denver%2C+USA",
        csv_file=str(csv_file),
    )

    assert result == (1, 0, [], 1, 0, 0, 1, 1)
    rows = _read_rows(csv_file)
    assert [row["status"] for row in rows] == ["location_filtered", "success"]
    assert calls == ["Dispatch Engineer - Remote in New York, NY, US | Dice.com"]


def test_write_job_titles_cap_ignores_location_filtered_jobs(tmp_path, monkeypatch):
    pages = [
        _DetailPage("Senior Full Stack Developer - FourthSquare - New York, NY, US | Dice.com"),
        _DetailPage("Dispatch Engineer - Remote in New York, NY, US | Dice.com"),
        _DetailPage("Frontend Engineer - Denver, CO, US | Dice.com"),
    ]
    root_page = _RootPage(pages)
    csv_file = tmp_path / "results.csv"
    calls = []

    monkeypatch.setattr(
        apply_module,
        "evaluate_and_apply",
        lambda page, *_args, **_kwargs: calls.append(page.title) or "success",
    )
    monkeypatch.setattr(
        apply_module,
        "user_profile",
        type("Profile", (), {"cities": ["Remote", "Denver"], "city": "Remote"})(),
    )

    result = apply_module.write_job_titles_to_file(
        root_page,
        ["job-ny", "job-remote", "job-denver"],
        "https://www.dice.com/jobs?q=python&location=Remote",
        csv_file=str(csv_file),
        max_jobs_to_process=2,
    )

    assert result == (2, 0, [], 1, 0, 0, 2, 2)
    rows = _read_rows(csv_file)
    assert [row["status"] for row in rows] == ["location_filtered", "success", "success"]
    assert calls == [
        "Dispatch Engineer - Remote in New York, NY, US | Dice.com",
        "Frontend Engineer - Denver, CO, US | Dice.com",
    ]


def test_resolve_resume_choice_prefers_direct_resume_path(tmp_path):
    resume_path = tmp_path / "frontend-resume.pdf"
    resume_path.write_text("pdf", encoding="utf-8")

    choice = apply_module._resolve_resume_choice(
        SimpleNamespace(
            title="Frontend Engineer",
            relevant_resume_path=str(resume_path),
            uploaded_resume_name="Frontend Resume.pdf",
            generated_resume_profile_id=None,
        )
    )

    assert choice["path"] == str(resume_path.resolve())
    assert choice["label"] == "Frontend Resume.pdf"


def test_resolve_resume_choice_can_fall_back_to_generated_resume(monkeypatch, tmp_path):
    generated_resume = tmp_path / "generated-resume.pdf"
    generated_resume.write_text("pdf", encoding="utf-8")

    monkeypatch.setattr(apply_module, "_load_generated_resume_path", lambda **_kwargs: generated_resume)

    choice = apply_module._resolve_resume_choice(
        SimpleNamespace(
            title="AI Integration Engineer",
            relevant_resume_path="",
            uploaded_resume_name="",
            generated_resume_profile_id="generated_ai-integration-engineer",
        )
    )

    assert choice["path"] == str(generated_resume)
    assert choice["label"] == "generated-resume.pdf"
