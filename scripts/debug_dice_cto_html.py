from pathlib import Path
import os
import time

from dotenv import load_dotenv, find_dotenv
from playwright.sync_api import sync_playwright

from app.dice.utils.login import login
from app.dice.utils.profile_to_url import userprofile_to_search_url


def load_env() -> None:
    project_root = Path(__file__).resolve().parents[1]
    candidates = [
        project_root / ".env",
        project_root / ".env.local",
        Path.cwd() / ".env",
    ]
    for env_path in candidates:
        if env_path.is_file():
            if load_dotenv(dotenv_path=str(env_path)):
                return
    found = find_dotenv(usecwd=True)
    if found:
        load_dotenv(dotenv_path=found)
    else:
        load_dotenv()


def main() -> None:
    load_env()
    email = os.getenv("EMAIL") or os.getenv("DICE_EMAIL")
    password = os.getenv("PASSWORD") or os.getenv("DICE_PASSWORD")
    if not email or not password:
        raise RuntimeError("Missing EMAIL/PASSWORD in environment.")

    search_url = userprofile_to_search_url("CTO")
    print(f"[DEBUG] CTO search URL: {search_url}")

    debug_dir = Path("app/dice/_experimental_/debug")
    debug_dir.mkdir(parents=True, exist_ok=True)
    html_path = debug_dir / "cto_search_results.html"
    screenshot_path = debug_dir / "cto_search_results.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        login(page, email, password)
        page.goto(search_url, wait_until="domcontentloaded", timeout=90000)
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        time.sleep(3)

        primary_count = page.locator('a[data-testid="job-search-job-detail-link"]').count()
        alt_count = page.locator('a[data-cy="search-card-title"], a[data-testid="search-card-title"]').count()
        no_results_text_count = page.locator(':text("No matching jobs found")').count()
        no_results_short_count = page.locator(':text("No jobs found")').count()

        html_path.write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(screenshot_path), full_page=True)

        print(f"[DEBUG] Final URL: {page.url}")
        print(f"[DEBUG] Page title: {page.title()}")
        print(f"[DEBUG] Primary selector count: {primary_count}")
        print(f"[DEBUG] Alt selector count: {alt_count}")
        print(f"[DEBUG] 'No matching jobs found' count: {no_results_text_count}")
        print(f"[DEBUG] 'No jobs found' count: {no_results_short_count}")
        print(f"[DEBUG] Saved HTML: {html_path}")
        print(f"[DEBUG] Saved screenshot: {screenshot_path}")

        browser.close()


if __name__ == "__main__":
    main()
