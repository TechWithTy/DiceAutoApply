from playwright.sync_api import sync_playwright
from dotenv import load_dotenv, find_dotenv, dotenv_values
import os
from pathlib import Path
from _data_.Profiles.main_profile import user_profile, display_profile
from app.dice.utils.login import login
from app.dice.utils.extract import extract_job_ids
from app.dice.utils.apply import write_job_titles_to_file
from app.dice.utils.utils import close_extra_tabs, logout_and_close
from typing import List
import time
from app.dice.utils.profile_to_url import userprofile_to_search_url

# Load environment variables
project_root = Path(__file__).resolve().parents[2]
candidate_envs = [
    project_root / ".env",
    project_root / ".env.local",
    Path.cwd() / ".env",
]
loaded_from = None
for env_path in candidate_envs:
    if env_path.is_file():
        if load_dotenv(dotenv_path=str(env_path)):
            loaded_from = str(env_path)
            break

if not loaded_from:
    found = find_dotenv(usecwd=True)
    if found:
        if load_dotenv(dotenv_path=found):
            loaded_from = found
    if not loaded_from:
        if load_dotenv():
            loaded_from = "CWD/.env"

print(f"[dotenv] Loaded from: {loaded_from if loaded_from else 'None found'}")

def _print_compact_profile() -> None:
    """Print a compact summary of the active job filter to reduce log noise."""
    jf = getattr(user_profile, "job_filter", None) or getattr(user_profile, "jobFilter", None)
    def _get(obj, name, default=None):
        return getattr(obj, name, default) if obj else default
    print("Job Filter Settings:", flush=True)
    print(f"  Work Setting: {_get(jf, 'work_setting', 'Unknown')}", flush=True)
    print(f"  Posted Date: {_get(jf, 'posted_date', 'Unknown')}", flush=True)
    print(f"  Employment Types: {_get(jf, 'employment_types', [])}", flush=True)
    print(f"  Willing to Sponsor: {_get(jf, 'willing_to_sponsor', False)}", flush=True)
    print(f"  Employer Types: {_get(jf, 'employer_types', [])}", flush=True)
    print(f"  Easy Apply: {_get(jf, 'easy_apply', True)}", flush=True)


def main() -> None:
    """
    Main workflow for headless Dice automation.
    """
    # Use a compact profile log instead of full Q&A to keep Streamlit logs clean
    _print_compact_profile()

    secret_email = os.getenv('EMAIL') or os.getenv('DICE_EMAIL')
    secret_password = os.getenv('PASSWORD') or os.getenv('DICE_PASSWORD')

    if not secret_email or not secret_password:
        direct_env_path = None
        for p in [project_root / ".env", Path.cwd() / ".env", project_root / ".env.local"]:
            if p.is_file():
                direct_env_path = p
                break
        if direct_env_path:
            vals = dotenv_values(direct_env_path)
            def norm(v):
                if v is None:
                    return None
                v = v.strip()
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                return v.strip()
            e = norm(vals.get('EMAIL') or vals.get('DICE_EMAIL'))
            pw = norm(vals.get('PASSWORD') or vals.get('DICE_PASSWORD'))
            if e and not secret_email:
                os.environ['EMAIL'] = e
                secret_email = e
            if pw and not secret_password:
                os.environ['PASSWORD'] = pw
                secret_password = pw

    if not secret_email or not secret_password:
        raise RuntimeError(
            "Missing EMAIL or PASSWORD environment variables."
        )

    # Use a common user agent
    custom_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    first_run = True

    with sync_playwright() as p:
        # Launch in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=custom_user_agent)
        try:
            context.set_default_navigation_timeout(60000)
            context.set_default_timeout(45000)
        except Exception as e:
            print(f"[timeouts] Could not set default timeouts: {e}")
        context.clear_cookies()
        page = context.new_page()
        login(page, secret_email, secret_password)

        grand_applied = 0
        grand_failed = 0
        grand_failed_jobs: List[str] = []

        for job_title in user_profile.job_titles:
            search_keyword = job_title.title
            print('Processing job title:', search_keyword, flush=True)
            search_url = userprofile_to_search_url(search_keyword)
            print(f"Navigating to search URL: {search_url}", flush=True)
            if not first_run:
                close_extra_tabs(context)
                page = context.new_page()
            else:
                first_run = False

            try:
                page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                print(f"[NAVIGATE] First attempt failed ({e}). Retrying once...", flush=True)
                try:
                    page.close()
                except Exception:
                    pass
                page = context.new_page()
                try:
                    page.goto(search_url, wait_until="domcontentloaded", timeout=90000)
                except Exception as e2:
                    print(f"[NAVIGATE] Second attempt failed: {e2}", flush=True)
                    continue

            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass
            time.sleep(2)
            job_ids: List[str] = []
            url = page.url
            extract_job_ids(page, job_ids)
            print(f"[JOBS] Extracted job IDs: {len(job_ids)}", flush=True)
            if len(job_ids) == 0:
                # Provide hints for why this might be zero to aid debugging
                print("[ZERO_JOBS] No jobs found. Possible reasons:", flush=True)
                print(" - Filters too strict (try widening date/employment types/location)", flush=True)
                print(" - DOM selectors outdated (check extract_job_ids)", flush=True)
                print(" - Page not fully loaded (increase waits)", flush=True)

            applied, failed, failed_jobs = write_job_titles_to_file(page, job_ids, url)
            grand_applied += int(applied or 0)
            grand_failed += int(failed or 0)
            if failed_jobs:
                grand_failed_jobs.extend(failed_jobs)

            print("\n========== APPLICATION SUMMARY ==========", flush=True)
            print(f"Jobs successfully applied: {applied}", flush=True)
            print(f"Jobs failed: {failed}", flush=True)
            if failed_jobs:
                print("Failed jobs:", flush=True)
                for job in failed_jobs:
                    print("-", job, flush=True)
            print("========================================\n", flush=True)
        # Grand totals across all job titles
        print("\n========== GRAND SUMMARY ==========", flush=True)
        print(f"Total applied: {grand_applied}", flush=True)
        print(f"Total failed: {grand_failed}", flush=True)
        if grand_failed_jobs:
            print("All failed jobs:", flush=True)
            for job in grand_failed_jobs:
                print("-", job, flush=True)
        print("===================================\n", flush=True)

        logout_and_close(page, browser)

if __name__ == "__main__":
    main()