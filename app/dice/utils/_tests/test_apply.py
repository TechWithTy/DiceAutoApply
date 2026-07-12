import csv
from collections import deque

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
        _DetailPage("Success Engineer"),
        _DetailPage("Already Applied Engineer"),
        _DetailPage("No Easy Apply Engineer"),
        _DetailPage("Failed Engineer"),
    ]
    root_page = _RootPage(pages)
    csv_file = tmp_path / "results.csv"
    outcomes = iter(["success", "already_applied", "no_easy_apply", "failed"])

    monkeypatch.setattr(apply_module, "evaluate_and_apply", lambda *_args, **_kwargs: next(outcomes))
    monkeypatch.setattr(apply_module, "_dump_no_apply_debug", lambda *_args, **_kwargs: None)

    result = apply_module.write_job_titles_to_file(
        root_page,
        ["job-success", "job-already", "job-no-button", "job-failed"],
        "https://www.dice.com/jobs?q=python&location=Remote",
        csv_file=str(csv_file),
    )

    assert result == (1, 1, ["Failed Engineer"], 2, 1, 1, 1)
    rows = _read_rows(csv_file)
    assert [row["job_id"] for row in rows] == ["job-success", "job-already", "job-no-button", "job-failed"]
    assert [row["status"] for row in rows] == ["success", "already_applied", "no_apply_button", "failed"]
    assert rows[0]["job_url"].endswith("/job-success?q=python&location=Remote")


def test_write_job_titles_skips_known_applied_jobs(tmp_path, monkeypatch):
    root_page = _RootPage([_DetailPage("Should Not Open")])
    csv_file = tmp_path / "results.csv"
    calls = []

    monkeypatch.setattr(apply_module, "evaluate_and_apply", lambda *_args, **_kwargs: calls.append("called"))

    result = apply_module.write_job_titles_to_file(
        root_page,
        ["job-known"],
        "https://www.dice.com/jobs?q=python",
        csv_file=str(csv_file),
        known_applied_job_ids={"job-known"},
    )

    assert result == (0, 0, [], 1, 1, 0, 0)
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
