"""
Main entrypoint for Dice automation using refactored modular utilities.
"""
import sys
print(sys.path)

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
from _data_.Profiles.main_profile import user_profile, display_profile
# from _data_.Filters.diceFilterSettings import dice_job_filter, JobFilter  # Removed unused imports
from app.dice.utils.login import login
from app.dice.utils.extract import extract_job_ids
from app.dice.utils.apply import write_job_titles_to_file
from app.dice.utils.utils import close_extra_tabs, logout_and_close
from typing import List
import time
from app.dice.utils.profile_to_url import userprofile_to_search_url

# Load environment variables from .env file
load_dotenv()

def main() -> None:
    """
    Main workflow for automating Dice job applications.
    """
    print("started")
    display_profile(user_profile)

    secret_email = os.getenv('EMAIL')
    secret_password = os.getenv('PASSWORD')
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
            write_job_titles_to_file(page, job_ids, url)
        logout_and_close(page, browser)

if __name__ == "__main__":
    main()
