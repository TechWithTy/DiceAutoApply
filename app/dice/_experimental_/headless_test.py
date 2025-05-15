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
import concurrent.futures

import os
# Load environment variables from .env file
load_dotenv()

MIN_WORKERS = 4
MAX_WORKERS = 8

def process_job_title(job_title_obj, email, password):
    """Process a single job title in its own Playwright context (thread-safe)."""

    results = {
        'job_title': job_title_obj.title,
        'applied': 0,
        'failed': 0,
        'failed_jobs': []
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.clear_cookies()
        page = context.new_page()
        try:
            login(page, email, password)
            search_keyword = job_title_obj.title
            print(f'[headless-thread] Processing job title: {search_keyword}')
            search_url = userprofile_to_search_url(search_keyword)
            print(f"[headless-thread] Navigating to search URL: {search_url}")
            page.goto(search_url)
            page.wait_for_load_state("load")
            time.sleep(3)
            close_extra_tabs(context)
            job_ids: List[str] = []
            url = page.url
            extract_job_ids(page, job_ids)
            if not job_ids:
                print(f"[headless-thread] No jobs found for {search_keyword}.")
            else:
                print(f"[headless-thread] Found {len(job_ids)} job IDs for {search_keyword}. Applying...")
                applied, failed, failed_jobs = write_job_titles_to_file(page, job_ids, url)
                results['applied'] = applied
                results['failed'] = failed
                results['failed_jobs'] = failed_jobs
        except Exception as e:
            print(f"[headless-thread] Error processing {job_title_obj.title}: {e}")
        finally:
            logout_and_close(page, browser)
    return results

def main_headless() -> None:
    print("[headless-async] started")
    secret_email = os.getenv('EMAIL')
    secret_password = os.getenv('PASSWORD')
    if not secret_email or not secret_password:
        raise ValueError("EMAIL and PASSWORD environment variables must be set.")
    job_titles = user_profile.job_titles
    results = []
    # Determine number of workers for ThreadPoolExecutor
    num_workers = min(max(MIN_WORKERS, len(job_titles)), MAX_WORKERS)
    # Use ThreadPoolExecutor to process job titles in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_job = {
            executor.submit(process_job_title, job_title, secret_email, secret_password): job_title.title
            for job_title in job_titles
        }
        for future in concurrent.futures.as_completed(future_to_job):
            job_title = future_to_job[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f'[headless-async] {job_title} generated an exception: {exc}')
    # Print summary
    print("\n[headless-async] All threads complete. Summary:")
    for r in results:
        print(f"Job Title: {r['job_title']} | Applied: {r['applied']} | Failed: {r['failed']}")
        if r['failed_jobs']:
            print(f"  Failed Jobs: {r['failed_jobs']}")
    print("[headless-async] Run complete.")

if __name__ == "__main__":
    main_headless()