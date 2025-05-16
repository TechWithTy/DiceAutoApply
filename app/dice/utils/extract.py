"""
Handles extraction of job IDs from search results.
"""
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
import time
from typing import List

def extract_job_ids(page: Page, job_ids: List[str]) -> None:
    selectors = {
        # * Updated selector for job card links (2025-05-15)
        "card_title": 'a[data-testid="job-search-job-detail-link"]',
        # * Updated selector for next page button
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
                href = job_link.get_attribute('href')
                if not href:
                    continue
                job_id = href.split("/")[-1]
                applied = False
                easy_apply = False
                try:
                    # Use XPath to get ancestor card as ElementHandle (never use evaluate_handle)
                    card_container = job_link.query_selector('xpath=ancestor::div[contains(@data-job-guid, "")]')
                    if card_container is None:
                        print(f"[DEBUG] No card container found for href={href}, using job_link as fallback")
                        card_container = job_link
                    action_elements = card_container.query_selector_all('a,button')
                    for elem in action_elements:
                        spans = elem.query_selector_all('span')
                        elem_href = elem.get_attribute('href') or ''
                        for span in spans:
                            text = span.inner_text().strip().lower()
                            if text == 'applied' and job_id in elem_href:
                                applied = True
                            if text == 'easy apply' and job_id in elem_href:
                                easy_apply = True
                        if applied:
                            break
                    if applied:
                        print(f"[SKIP] Already applied for job_id={job_id}")
                        continue  # Skip this job
                    elif easy_apply:
                        print(f"[QUEUE] Easy Apply available for job_id={job_id}")
                        job_ids.append(job_id)
                    else:
                        print(f"[SKIP] No Easy Apply or already applied for job_id={job_id}")
                        continue  # Optionally skip or log as not applicable

                        if not applied:
                            elem_text = elem.inner_text().strip().lower()
                            if elem_text == 'applied':
                                applied = True
                                print(f"[SKIP] Found <a>/<button> with text 'Applied' for job_id={job_id}: {elem.evaluate('node => node.outerHTML')}")
                                break
                        if applied:
                            break
                except Exception as e:
                    print(f"[DEBUG][APPLIED_CHECK] Exception during applied check for job_id={job_id}: {e}")
                    applied = False
                    job_ids.append(job_id)
                    print(f"[EXTRACTED] Job ID: {job_id}")
                else:
                    if not applied:
                        job_ids.append(job_id)
                        print(f"[EXTRACTED] Job ID: {job_id}")
                    else:
                        print(f"[SKIP] Job already applied (found 'Applied' button in card): {job_id}")
            next_button = page.query_selector(selectors["list_pagination_next"])
            if next_button and next_button.is_visible():
                # Check for disabled state via aria-disabled or data-disabled attribute
                aria_disabled = next_button.get_attribute("aria-disabled")
                data_disabled = next_button.get_attribute("data-disabled")
                if aria_disabled == "true" or data_disabled == "true":
                    print("Next button is disabled. No more pages.")
                    break
                print("Navigating to next page...")
                next_button.click()
                time.sleep(3)
            else:
                print("No more pages or next button not available.")
                break
        except PlaywrightTimeoutError:
            print("Timeout or no more job results.")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected exception: {e}")
            break
