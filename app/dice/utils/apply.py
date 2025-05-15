"""
Handles job application actions for Dice automation.
"""
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
import time
from typing import List
import os

next_in_application_button = 'button.seds-button-primary.btn-next'

import csv
from datetime import datetime

def write_job_titles_to_file(page: Page, job_ids: List[str], url: str, csv_file: str = 'output/job_application_results.csv'):
    """
    Writes job application results to
    a CSV file, including job title, URL, date/time, status, and error message.
    Returns (applied_count, failed_count, failed_jobs)
    """
    print("number of All job IDs:" + str(len(job_ids)))
    selectors = {
        "apply_button": 'apply-button-wc',
    }
    applied = 0
    failed = 0
    failed_jobs = []
    parts = url.split('?')
    fieldnames = ["job_title", "job_url", "datetime", "status", "error_message"]
    # Create output directory if it does not exist
    output_dir = os.path.dirname(csv_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Write header if file does not exist
    try:
        with open(csv_file, 'x', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    except FileExistsError:
        pass  # File already exists
    for job_id in job_ids:
        job_id_url = "https://www.dice.com/job-detail/" + job_id + "?" + parts[1]
        dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        job_title = job_id_url  # fallback
        status = "failed"
        error_message = ""
        try:
            try:
                new_page = page.context.new_page()
                try:
                    new_page.goto(job_id_url)
                    new_page.wait_for_load_state("load")
                    job_title = new_page.evaluate("document.title")
                    # Check for 'already applied' state
                    try:
                        # If <apply-button-wc> does NOT exist, or 'Application submitted' text is present, treat as already applied
                        apply_button_present = new_page.query_selector('apply-button-wc')
                        button_text = ""
                        if apply_button_present is not None:
                            try:
                                button_text = apply_button_present.inner_text().strip()
                            except Exception:
                                button_text = ""
                        app_submitted_text = new_page.locator(':text("Application submitted")').count() > 0
                        if (button_text == "Applied") or app_submitted_text:
                            status = "already_applied"
                            error_message = "Job already applied (button text) or application submitted text found."
                            print(f"[ALREADY APPLIED] {job_title} ({job_id_url})")
                            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writerow({
                                    "job_title": job_title,
                                    "job_url": job_id_url,
                                    "datetime": dt_str,
                                    "status": status,
                                    "error_message": error_message
                                })
                            new_page.close()
                            continue
                    except Exception as e:
                        # If check fails, proceed as normal
                        pass
                except Exception as e:
                    status = "page_error"
                    error_message = f"Page navigation/load error: {e}"
                    print(f"[PAGE ERROR] {job_id_url} - {error_message}")
                    failed += 1
                    failed_jobs.append(job_title)
                    raise  # Will be caught by outer except to write CSV
                # Simulate skip logic (customize as needed)
                if False:  # e.g., if already_applied(job_title):
                    status = "skipped"
                    error_message = "Already applied (simulated)"
                    print(f"[SKIPPED] {job_title} ({job_id_url})")
                else:
                    try:
                        new_page.wait_for_selector(selectors["apply_button"], timeout=5000)
                    except Exception as e:
                        status = "no_apply_button"
                        error_message = f"No apply button: {e}"
                        print(f"[NO APPLY BUTTON] {job_title} ({job_id_url})")
                        failed += 1
                        failed_jobs.append(job_title)
                    else:
                        try:
                            success = evaluate_and_apply(new_page, applied + 1)
                            if success:
                                status = "success"
                                applied += 1
                                print(f"[APPLY SUCCESS] {job_title} ({job_id_url})")
                                error_message = ""
                            else:
                                status = "failed"
                                failed += 1
                                failed_jobs.append(job_title)
                                error_message = "evaluate_and_apply returned False"
                                print(f"[APPLY FAILED] {job_title} ({job_id_url}) - {error_message}")
                        except Exception as e:
                            status = "exception"
                            error_message = f"Exception during apply: {e}"
                            failed += 1
                            failed_jobs.append(job_title)
                            print(f"[EXCEPTION] {job_title} ({job_id_url}) - {error_message}")
                new_page.close()
            except Exception as e:
                if status not in ("page_error", "no_apply_button", "skipped", "exception"):
                    status = "exception"
                    error_message = f"Outer exception: {e}"
                    failed += 1
                    failed_jobs.append(job_title)
        except Exception as e:
            # Network or catastrophic error
            if "network" in str(e).lower():
                status = "network_error"
            error_message = str(e)
            print(f"[NETWORK/CRITICAL ERROR] {job_id_url} - {error_message}")
            failed += 1
            failed_jobs.append(job_title)
        # Write result to CSV
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow({
                "job_title": job_title,
                "job_url": job_id_url,
                "datetime": dt_str,
                "status": status,
                "error_message": error_message
            })
    return applied, failed, failed_jobs

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
