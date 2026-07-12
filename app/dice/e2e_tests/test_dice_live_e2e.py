import csv
import os
from dataclasses import replace

import pytest
from dotenv import dotenv_values
from playwright.sync_api import sync_playwright

from _data_.Profiles.main_profile import user_profile
from app.dice.profile.model import build_profile_payload
from app.dice.profile.selectors import ProfileSelectorRegistry
from app.dice.profile.workflow import DiceProfileWorkflow, _load_test_credentials
from app.dice.utils.apply import write_job_titles_to_file
from app.dice.utils.extract import extract_job_ids
from app.dice.utils.login import login
from app.dice.utils.profile_to_url import userprofile_to_search_url


pytestmark = pytest.mark.e2e


def _require_live_e2e():
    if os.getenv("RUN_DICE_E2E", "").strip().lower() not in {"1", "true", "yes", "on"}:
        pytest.skip("Set RUN_DICE_E2E=1 to run live Dice e2e tests.")
    return _load_test_credentials()


def _normalize_env_value(value):
    if value is None:
        return None
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return value.strip() or None


def _require_main_credentials():
    if os.getenv("RUN_DICE_E2E", "").strip().lower() not in {"1", "true", "yes", "on"}:
        pytest.skip("Set RUN_DICE_E2E=1 to run live Dice e2e tests.")
    email = _normalize_env_value(os.getenv("EMAIL") or os.getenv("DICE_EMAIL"))
    password = _normalize_env_value(os.getenv("PASSWORD") or os.getenv("DICE_PASSWORD"))
    if not email or not password:
        for env_path in [".env", ".env.local"]:
            vals = dotenv_values(env_path)
            email = email or _normalize_env_value(vals.get("EMAIL") or vals.get("DICE_EMAIL"))
            password = password or _normalize_env_value(vals.get("PASSWORD") or vals.get("DICE_PASSWORD"))
    if not email or not password:
        pytest.skip("Missing EMAIL/PASSWORD or DICE_EMAIL/DICE_PASSWORD for main-account e2e.")
    return email, password


def _new_logged_in_page(email, password):
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1440, "height": 1024},
    )
    context.set_default_navigation_timeout(60000)
    context.set_default_timeout(45000)
    page = context.new_page()
    login(page, email, password)
    return playwright, browser, context, page


def _close_browser(playwright, browser, context, page):
    for resource in (page, context, browser):
        try:
            resource.close()
        except Exception:
            pass
    try:
        playwright.stop()
    except Exception:
        pass


def test_live_profile_creation_workflow_completes_and_verifies():
    email, password = _require_live_e2e()
    playwright, browser, context, page = _new_logged_in_page(email, password)
    try:
        payload = replace(build_profile_payload(), profile_visible=False)
        workflow = DiceProfileWorkflow(page, payload, ProfileSelectorRegistry())

        workflow.run()

        assert workflow.verify_profile() is True
    finally:
        _close_browser(playwright, browser, context, page)


def test_live_dice_search_and_dry_run_apply_preflight(tmp_path, monkeypatch):
    email, password = _require_live_e2e()
    monkeypatch.setenv("DICE_DRY_RUN", "1")
    playwright, browser, context, page = _new_logged_in_page(email, password)
    try:
        search_keyword = user_profile.job_titles[0].title
        search_url = userprofile_to_search_url(search_keyword)
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass

        job_ids = []
        extract_job_ids(page, job_ids, only_easy_apply=False)
        if not job_ids:
            pytest.skip(f"No jobs discovered for live search: {search_keyword}")

        csv_file = tmp_path / "dice_dry_run_results.csv"
        result = write_job_titles_to_file(
            page,
            job_ids[:1],
            page.url,
            csv_file=str(csv_file),
            known_applied_job_ids=set(),
        )

        with csv_file.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 1
        assert rows[0]["job_id"] == job_ids[0]
        assert rows[0]["status"] in {"dry_run", "already_applied", "no_apply_button"}
        assert result[0] == 0
    finally:
        _close_browser(playwright, browser, context, page)


def test_live_recommended_jobs_and_dry_run_apply_preflight(tmp_path, monkeypatch):
    email, password = _require_live_e2e()
    monkeypatch.setenv("DICE_DRY_RUN", "1")
    playwright, browser, context, page = _new_logged_in_page(email, password)
    try:
        page.goto("https://www.dice.com/recommended-jobs", wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass

        assert "login" not in page.url.lower()
        assert "recommended" in page.url.lower()

        job_ids = []
        extract_job_ids(page, job_ids, only_easy_apply=True)
        if not job_ids:
            pytest.skip("No Recommended Easy Apply jobs discovered in the live Dice account.")

        csv_file = tmp_path / "dice_recommended_dry_run_results.csv"
        result = write_job_titles_to_file(
            page,
            job_ids[:1],
            page.url,
            csv_file=str(csv_file),
            known_applied_job_ids=set(),
        )

        with csv_file.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 1
        assert rows[0]["job_id"] == job_ids[0]
        assert rows[0]["status"] in {"dry_run", "already_applied", "no_apply_button"}
        assert result[0] == 0
    finally:
        _close_browser(playwright, browser, context, page)


def test_live_main_account_recommended_jobs_and_dry_run_apply_preflight(tmp_path, monkeypatch):
    email, password = _require_main_credentials()
    monkeypatch.setenv("DICE_DRY_RUN", "1")
    playwright, browser, context, page = _new_logged_in_page(email, password)
    try:
        page.goto("https://www.dice.com/recommended-jobs", wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass

        assert "login" not in page.url.lower()
        assert "recommended" in page.url.lower()

        job_ids = []
        extract_job_ids(page, job_ids, only_easy_apply=False)
        if not job_ids:
            pytest.skip("No Recommended jobs discovered in the live main Dice account.")

        csv_file = tmp_path / "dice_main_recommended_dry_run_results.csv"
        result = write_job_titles_to_file(
            page,
            job_ids[:1],
            page.url,
            csv_file=str(csv_file),
            known_applied_job_ids=set(),
        )

        with csv_file.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 1
        assert rows[0]["job_id"] == job_ids[0]
        assert rows[0]["status"] in {"dry_run", "already_applied", "no_apply_button"}
        assert result[0] == 0
    finally:
        _close_browser(playwright, browser, context, page)
