"""
Handles extraction of job IDs from search results.
"""
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
import time
from typing import List, Set

def extract_job_ids(page: Page, job_ids: List[str]) -> None:
    """Populate job_ids with unique IDs found on the results list.

    Adds robust selectors, dedupe, and safer pagination to reduce zero-result scenarios.
    """
    selectors = {
        # Primary and fallback selectors for job links/cards
        "card_title_primary": 'a[data-testid="job-search-job-detail-link"]',
        "card_title_alt": 'a[data-cy="search-card-title"], a[data-testid="search-card-title"]',
        # Pagination next variants
        "next_span_link": 'span[aria-label="Next"][role="link"]',
        "next_button": 'button[aria-label="Next"], a[aria-label="Next"], [data-testid="pagination-next"]',
    }

    seen: Set[str] = set(job_ids)
    page_max = 10  # safety guard to prevent infinite loops
    page_index = 1

    while True:
        page.wait_for_load_state("domcontentloaded")
        try:
            # Wait for either primary or alt cards
            try:
                page.wait_for_selector(selectors["card_title_primary"], timeout=12000)
                card_selector = selectors["card_title_primary"]
            except PlaywrightTimeoutError:
                page.wait_for_selector(selectors["card_title_alt"], timeout=12000)
                card_selector = selectors["card_title_alt"]

            time.sleep(1.5)  # allow late paints
            job_links = page.query_selector_all(card_selector)
            if not job_links:
                print("[RESULTS] No job cards on this page.")
            added_this_page = 0
            for job_link in job_links:
                href = job_link.get_attribute('href') or ''
                if not href:
                    continue
                job_id = href.split("/")[-1]
                if not job_id or job_id in seen:
                    continue
                # Check for cues on the card for already applied / easy apply
                applied = False
                easy_apply = False
                try:
                    card_container = job_link.query_selector('xpath=ancestor::div[contains(@data-job-guid, "")]') or job_link
                    # Detect badges/buttons inside the card
                    badge_text = (card_container.inner_text() or '').lower()
                    if 'applied' in badge_text:
                        applied = True
                    if 'easy apply' in badge_text or 'easy apply' in (job_link.inner_text() or '').lower():
                        easy_apply = True
                except Exception:
                    pass

                if applied:
                    print(f"[SKIP] Already applied for job_id={job_id}")
                    continue
                if not easy_apply:
                    print(f"[SKIP] No Easy Apply for job_id={job_id}")
                    continue

                job_ids.append(job_id)
                seen.add(job_id)
                added_this_page += 1
                print(f"[EXTRACTED] Job ID: {job_id}")

            print(f"[RESULTS] Page {page_index}: added {added_this_page} new IDs (total unique so far: {len(seen)})")

            # Try pagination
            next_btn = page.query_selector(selectors["next_span_link"]) or page.query_selector(selectors["next_button"])
            if next_btn and next_btn.is_visible():
                aria_disabled = next_btn.get_attribute("aria-disabled")
                data_disabled = next_btn.get_attribute("data-disabled")
                if aria_disabled == "true" or data_disabled == "true":
                    print("[PAGING] Next is disabled. End of results.")
                    break
                page_index += 1
                if page_index > page_max:
                    print(f"[PAGING] Reached page safety limit ({page_max}). Stopping.")
                    break
                print("[PAGING] Going to next page...")
                next_btn.click()
                time.sleep(2)
                continue
            else:
                print("[PAGING] No next button visible. End of results.")
                break

        except PlaywrightTimeoutError:
            print("[TIMEOUT] Waiting for job cards timed out. Likely no results.")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected exception while extracting: {e}")
            break
