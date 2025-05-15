"""
Handles job application actions for Dice automation.
"""
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
import time
from typing import List

next_in_application_button = 'button.seds-button-primary.btn-next'

def write_job_titles_to_file(page: Page, job_ids: List[str], url: str) -> None:
    print("number of All job IDs:" + str(len(job_ids)))
    selectors = {
        "apply_button": 'apply-button-wc',
    }
    with open('output/job_titles.txt', 'w') as file:
        val = 0
        parts = url.split('?')
        for job_id in job_ids:
            job_id_url = "https://www.dice.com/job-detail/" + job_id + "?" + parts[1]
            try:
                new_page = page.context.new_page()
                new_page.goto(job_id_url)
                new_page.wait_for_load_state("load")
                time.sleep(3)
                job_title = new_page.evaluate("document.title")
                file.write(job_title + '\n')
                try:
                    new_page.wait_for_selector(selectors["apply_button"])
                    val += 1
                    success = evaluate_and_apply(new_page, val)
                    if success:
                        print(f"[APPLY SUCCESS] {job_title} ({job_id_url})")
                        new_page.close()  # Only close on success
                    else:
                        print(f"[APPLY FAILED] {job_title} ({job_id_url})")
                        # Leave tab open for debugging
                except Exception as e:
                    print(f"[APPLY FAILED] {job_title} ({job_id_url}) - Error: {str(e)}")
                    # Leave tab open for debugging
            except Exception as e:
                print(f"Error processing job id: {job_id_url}")
                print(f"Error details: {str(e)}")
                try:
                    new_page.close()
                except Exception:
                    pass
                continue

def evaluate_and_apply(page: Page, val: int) -> bool:
    selectors = {
        # Updated robust Easy Apply button selector (2025-05-15)
        "easy_apply_button": 'a[href*="job-detail"][class*="bg-interaction"]:has-text("Easy Apply")',
        "submit_button": '//button/span[text()="Submit"]/..',
        "application_submitted": 'h1:has-text("Application submitted. We\'re rooting for you.")',
        "profile_visible_application_submitted":   'div.banner-message.sc-dhi-candidates-modal-2:has-text("Your Application is on its way.")'
    }
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"[Easy Apply] Attempt {attempt+1} waiting for button...")
            page.wait_for_selector(selectors["easy_apply_button"], timeout=5000)
            print("[Easy Apply] Button found!")
            break
        except Exception:
            if attempt < max_attempts - 1:
                print(f"[Easy Apply] Button not found, refreshing page (attempt {attempt+2})...")
                page.reload()
                page.wait_for_load_state("load")
                time.sleep(2)
            else:
                print("[Easy Apply] Button not found after 3 attempts, skipping this job.")
                return False
    # ... rest of your logic for clicking/applying goes here ...
    # After a successful submit, return True
    # If submit fails, return False
    js_script = """
        (function() {
            const applyButtonWc = document.querySelector('apply-button-wc');
            let value = 0;
            if (applyButtonWc) {
                const shadowRoot = applyButtonWc.shadowRoot;
                const easyApplyButton = shadowRoot.querySelector('button.btn.btn-primary');
                if (easyApplyButton) {
                    easyApplyButton.click();
                    return 1;
                }
            }
            return 0;
        })();
    """
    returned_value = page.evaluate(js_script)
    if returned_value == 1:
        page.wait_for_load_state("load")
        try:
            time.sleep(3)
            max_attempts = 3
            attempt = 0
            expected_url_pattern = "https://www.dice.com/**/{apply,job-detail}**"
            current_url = page.url
            if "apply" in current_url or "job-detail" in current_url:
                print(f"Already on the correct URL: {current_url}")
                next_button = page.wait_for_selector(
                    next_in_application_button, timeout=10000)
                next_button.click()
                submit_button = page.wait_for_selector(
                    selectors["submit_button"], timeout=10000)
                submit_button.click()
                return
            while attempt < max_attempts:
                try:
                    page.wait_for_url(expected_url_pattern, timeout=10000)
                    print(f"Successfully navigated to URL: {page.url}")
                    break
                except PlaywrightTimeoutError:
                    attempt += 1
                    current_url = page.url
                    print(f"Attempt {attempt} failed. Expected: {expected_url_pattern}, but got: {current_url}")
                    time.sleep(3)
            if attempt == max_attempts:
                raise Exception(f"Failed to navigate to the expected URL after {max_attempts} attempts. Last URL: {current_url}")
            next_button = page.wait_for_selector(
                next_in_application_button, timeout=10000)
            next_button.click()
            submit_button = page.wait_for_selector(
                selectors["submit_button"], timeout=10000)
            submit_button.click()
            last_page = page.context.pages[-1]
            last_page.close()
            if page.is_visible(selectors["application_submitted"]):
                header_text = page.locator(
                    selectors["application_submitted"]).text_content()
                last_page = page.context.pages[-1]
                last_page.close()
            elif page.is_visible(selectors["profile_visible_application_submitted"]):
                header_text = page.locator(
                    selectors["profile_visible_application_submitted"]).text_content()
                last_page = page.context.pages[-1]
                last_page.close()
        except PlaywrightTimeoutError as e:
            print(f"Timeout during the application process: {e}")
            val = 1
        except Exception as e:
            print(f"Error during the application process: {e}")
            val = 1
    else:
        last_page = page.context.pages[-1]
        last_page.close()
