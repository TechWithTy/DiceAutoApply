"""
Handles extraction of job IDs from search results.
"""
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
import time
from typing import List

def extract_job_ids(page: Page, job_ids: List[str]) -> None:
    selectors = {
        # Updated selector for job card links (2025-05-15)
        "card_title": 'a[data-testid="job-search-job-detail-link"]',
        # Updated selector for next page button
        "list_pagination_next": 'span[aria-label="Next"][role="link"]',
    }
    while True:
        page.wait_for_load_state("load")
        time.sleep(5)
        try:
            page.wait_for_selector(selectors["card_title"], timeout=15000)
            job_links = page.query_selector_all(selectors["card_title"])
            if not job_links:
                print("No job results found.")
                break
            for job_link in job_links:
                # Extract job ID from href for robustness
                href = job_link.get_attribute('href')
                if href:
                    job_id = href.split('/')[-1].split('?')[0]
                    job_ids.append(job_id)
            # Only check for the next button, do NOT wait for it
            next_button = page.query_selector(selectors["list_pagination_next"])
            if next_button and next_button.is_visible():
                print("Navigating to next page...")
                next_button.click()
                time.sleep(3)
            else:
                print("No more pages or next button not available.")
                break
        except PlaywrightTimeoutError:
            print("Timeout or no more job results.")
            break

        except PlaywrightTimeoutError:
            print("Timeout exceeded while waiting for job results. No job results found.")
            break
        page.wait_for_load_state("load")
        page.wait_for_selector(selectors["list_pagination_next"])
        next_button = page.query_selector(selectors["list_pagination_next"])
        if next_button:
            page.wait_for_load_state("load")
            is_disabled = next_button.evaluate(
                '(element) => element.classList.contains("disabled")')
            if not is_disabled:
                next_button.click()
            else:
                break
        else:
            break
