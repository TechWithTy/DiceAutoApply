from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from _data_.Profiles.main_profile import user_profile
from app.dice.utils.login import login
from app.dice.utils.extract import extract_job_ids
from app.dice.utils.apply import write_job_titles_to_file
from app.dice.utils.utils import close_extra_tabs, logout_and_close
from app.dice.utils.profile_to_url import userprofile_to_search_url
import time
from typing import List
import os
# Load environment variables from .env file
load_dotenv()

def main_headless() -> None:
    print("[headless] started")
   
    secret_email = os.getenv('EMAIL')
    secret_password = os.getenv('PASSWORD')
    if not secret_email or not secret_password:
        raise ValueError("EMAIL and PASSWORD environment variables must be set.")
    first_run = True
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.clear_cookies()
        page = context.new_page()
        login(page, secret_email, secret_password)
        for job_title in user_profile.job_titles:
            search_keyword = job_title.title
            print('[headless] Processing job title:', search_keyword)
            search_url = userprofile_to_search_url(search_keyword)
            print(f"[headless] Navigating to search URL: {search_url}")
            page.goto(search_url)
            page.wait_for_load_state("load")
            time.sleep(3)
            if not first_run:
                close_extra_tabs(context)
            else:
                first_run = False
            job_ids: List[str] = []
            url = page.url
            extract_job_ids(page, job_ids)
            if not job_ids:
                print("[headless] No jobs found.")
            else:
                print(f"[headless] Found {len(job_ids)} job IDs. Applying...")
                write_job_titles_to_file(page, job_ids, url)
        logout_and_close(page, browser)
        print("[headless] Run complete.")

if __name__ == "__main__":
    main_headless()