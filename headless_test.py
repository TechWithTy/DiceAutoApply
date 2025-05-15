"""
Headless test runner for Dice automation. No FastAPI, just headless browser automation.
"""
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from _data_.Profiles.main_profile import user_profile
from app.dice.utils.login import login
from app.dice.utils.extract import extract_job_ids
from app.dice.utils.apply import write_job_titles_to_file
from app.dice.utils.profile_to_url import userprofile_to_search_url

load_dotenv()

def main_headless(job_title="Full Stack Developer", location="Remote"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        login(page)
        search_url = userprofile_to_search_url(user_profile, job_title=job_title, location=location)
        page.goto(search_url)
        job_ids = []
        extract_job_ids(page, job_ids)
        if not job_ids:
            print("No jobs found.")
        else:
            output_file = f"applied_jobs_{job_title.replace(' ', '_')}.txt"
            applied, failed, failed_jobs = write_job_titles_to_file(page, job_ids, output_file)
            print(f"Applied to {applied} jobs, {failed} failed.")
        context.close()
        browser.close()
        print("Headless run complete.")

if __name__ == "__main__":
    main_headless()
