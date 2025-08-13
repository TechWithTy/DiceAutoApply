"""
Main entrypoint for Dice automation using refactored modular utilities.
"""
import sys
print(sys.path)

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv, find_dotenv, dotenv_values
import os
from pathlib import Path
from _data_.Profiles.main_profile import user_profile, display_profile
# from _data_.Filters.diceFilterSettings import dice_job_filter, JobFilter  # Removed unused imports
from app.dice.utils.login import login
from app.dice.utils.extract import extract_job_ids
from app.dice.utils.apply import write_job_titles_to_file
from app.dice.utils.utils import close_extra_tabs, logout_and_close
from typing import List
import time
from app.dice.utils.profile_to_url import userprofile_to_search_url

# Load environment variables from .env file (robust search)
# 1) Prefer loading relative to the project root derived from this file's location
# 2) Fallback to find_dotenv (search up the tree)
# 3) Fallback to a plain load_dotenv() which uses CWD
project_root = Path(__file__).resolve().parents[2]  # .../DiceAutoApply
print(f"[dotenv] Project root resolved to: {project_root}")
candidate_envs = [
    project_root / ".env",
    project_root / ".env.local",
    Path.cwd() / ".env",
]
for p in candidate_envs:
    try:
        print(f"[dotenv] Candidate: {p} | exists: {p.is_file()}")
    except Exception as e:
        print(f"[dotenv] Candidate check error for {p}: {e}")
loaded_from = None
for env_path in candidate_envs:
    if env_path.is_file():
        if load_dotenv(dotenv_path=str(env_path)):
            loaded_from = str(env_path)
            break

if not loaded_from:
    # Search upwards from CWD and also try default
    found = find_dotenv(usecwd=True)
    if found:
        if load_dotenv(dotenv_path=found):
            loaded_from = found
    if not loaded_from:
        if load_dotenv():
            loaded_from = "CWD/.env"

print(f"[dotenv] Loaded from: {loaded_from if loaded_from else 'None found'}")

def main() -> None:
    """
    Main workflow for automating Dice job applications.
    """
    print("started")
    display_profile(user_profile)

    # Support alternate variable names as fallback
    secret_email = os.getenv('EMAIL') or os.getenv('DICE_EMAIL')
    secret_password = os.getenv('PASSWORD') or os.getenv('DICE_PASSWORD')

    # If still missing, directly parse .env and inject
    if not secret_email or not secret_password:
        direct_env_path = None
        for p in [project_root / ".env", Path.cwd() / ".env", project_root / ".env.local"]:
            if p.is_file():
                direct_env_path = p
                break
        if direct_env_path:
            print(f"[dotenv] Directly parsing: {direct_env_path}")
            vals = dotenv_values(direct_env_path)
            # Normalize keys and trim quotes/whitespace
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
        else:
            print("[dotenv] No .env file found for direct parse fallback.")
    masked_email = (secret_email[:2] + "***" + secret_email[-2:]) if secret_email else None
    print(f"[dotenv] EMAIL present: {'yes' if secret_email else 'no'} ({masked_email if secret_email else ''})")
    print(f"[dotenv] PASSWORD present: {'yes' if bool(secret_password) else 'no'}")
    # Validate credentials early to avoid Playwright fill() receiving a missing value
    if not secret_email or not secret_password:
        raise RuntimeError(
            "Missing EMAIL or PASSWORD environment variables. Ensure your .env contains EMAIL=... and PASSWORD=... and that it is discoverable."
        )
    custom_user_agent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.288 Mobile Safari/537.36"

    first_run = True

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=custom_user_agent)
        context.clear_cookies()
        page = context.new_page()
        login(page, secret_email, secret_password)

        for job_title in user_profile.job_titles:
            search_keyword = job_title.title
            print('Processing job title:', search_keyword)
            search_url = userprofile_to_search_url(search_keyword)
            print(f"Navigating to search URL: {search_url}")
            if not first_run:
                close_extra_tabs(context)
                page = context.new_page()  # Always create a new page after closing tabs
            else:
                first_run = False
                # Use the original page created before the loop
            page.goto(search_url)
            page.wait_for_load_state("load")
            time.sleep(3)
            job_ids: List[str] = []
            url = page.url
            extract_job_ids(page, job_ids)
            applied, failed, failed_jobs = write_job_titles_to_file(page, job_ids, url)
            print("\n========== APPLICATION SUMMARY ==========")
            print(f"Jobs successfully applied: {applied}")
            print(f"Jobs failed: {failed}")
            if failed_jobs:
                print("Failed jobs:")
                for job in failed_jobs:
                    print("-", job)
            print("========================================\n")
        logout_and_close(page, browser)

if __name__ == "__main__":
    main()
