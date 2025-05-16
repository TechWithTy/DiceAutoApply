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
        # * Updated Easy Apply button selector to target <apply-button-wc> inside #applyButton (pierce shadow DOM)
        # ! Use Playwright shadow selector, filter for text in code
        "easy_apply_wc_button": 'div#applyButton apply-button-wc >> shadow=button',
        "submit_button": '//button/span[text()="Submit"]/..',
        "application_submitted": 'div.post-apply-header-text > h1:has-text("Application submitted")',
        "application_submitted_any_h1": 'h1:has-text("Application submitted")',
        "profile_visible_application_submitted":   'div.banner-message.sc-dhi-candidates-modal-2:has-text("Your Application is on its way.")'
    }
    # ! Removed all page refreshes when waiting for Easy Apply button (per user request)
    # * Extended wait time and improved logs
    # * Selector is now robust to match <div id="applyButton"><apply-button-wc ...></apply-button-wc></div>

    # * Wait up to 20 seconds for Easy Apply button, no refreshes (!)
    EASY_APPLY_WAIT_SECONDS = 20
    print(f"[Easy Apply] Waiting up to {EASY_APPLY_WAIT_SECONDS}s for Easy Apply button to appear in <apply-button-wc>...")
    found = False
    # Wait specifically for a button with text 'Easy apply' (case-insensitive) in the shadow DOM using JS polling
    found = False
    start_time = time.time()
    while time.time() - start_time < EASY_APPLY_WAIT_SECONDS:
        returned_value = page.evaluate('''
            (function() {
                const wc = document.querySelector('div#applyButton apply-button-wc');
                if (wc && wc.shadowRoot) {
                    const btns = wc.shadowRoot.querySelectorAll('button');
                    for (const btn of btns) {
                        if (btn.innerText.trim().toLowerCase() === "easy apply") {
                            btn.scrollIntoView({behavior: "smooth", block: "center"});
                            btn.focus();
                            btn.click();
                            return 1;
                        }
                    }
                }
                return 0;
            })();
        ''')
        if returned_value == 1:
            print("[Easy Apply] Clicked Easy Apply button via JS polling.")
            found = True
            break
        time.sleep(0.5)

    if not found:
        print(f"[Easy Apply] No Easy Apply button found in shadow DOM after waiting {EASY_APPLY_WAIT_SECONDS}s. Skipping this job.")
        # Debug: print all button texts in shadow DOM to help diagnose selector issues
        try:
            wc = page.evaluate_handle("document.querySelector('div#applyButton apply-button-wc')")
            if wc:
                shadow_buttons = wc.evaluate('el => el.shadowRoot ? Array.from(el.shadowRoot.querySelectorAll(\'button\')).map(b => b.innerText) : []')
                print("[DEBUG] Button texts in <apply-button-wc> shadow root:")
                for text in shadow_buttons:
                    print("-", text)
            else:
                print("[DEBUG] <apply-button-wc> not found.")
        except Exception:
            print("[DEBUG] Could not enumerate shadow DOM buttons.")
        return False

        js_script = '''
            (function() {
                const applyButtonWc = document.querySelector('div#applyButton apply-button-wc');
                if (applyButtonWc && applyButtonWc.shadowRoot) {
                    const btns = Array.from(applyButtonWc.shadowRoot.querySelectorAll('button'));
                    for (const btn of btns) {
                        const txt = btn.innerText.trim().toLowerCase();
                        if (txt === "easy apply" || txt === "apply") {
                            btn.click();
                            return 1;
                        }
                    }
                }
                return 0;
            })();
        '''
        returned_value = page.evaluate(js_script)
        if returned_value == 1:
            print("[Easy Apply] Clicked Easy Apply button via JS fallback.")
            found = True
        else:
            print("[Easy Apply] Could not find Easy Apply button even via JS fallback. Skipping this job.")
            # Debug: print all button texts in shadow DOM to help diagnose selector issues
            try:
                wc = page.query_selector('div#applyButton apply-button-wc')
                if wc:
                    shadow_buttons = wc.query_selector_all('button')
                    print("[DEBUG] Button texts in <apply-button-wc> shadow root:")
                    for b in shadow_buttons:
                        try:
                            print("-", b.inner_text())
                        except Exception:
                            pass
                else:
                    print("[DEBUG] <apply-button-wc> not found.")
            except Exception:
                print("[DEBUG] Could not enumerate shadow DOM buttons.")
            return False
    # * End of Easy Apply wait logic

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
                # After submit, robustly wait for confirmation selectors
                try:
                    page.wait_for_selector(selectors["application_submitted"], timeout=15000)
                    if page.is_visible(selectors["application_submitted"]):
                        print("[CONFIRMATION] Application submitted!")
                        return True
                except PlaywrightTimeoutError:
                    pass
                try:
                    page.wait_for_selector(selectors["profile_visible_application_submitted"], timeout=15000)
                    if page.is_visible(selectors["profile_visible_application_submitted"]):
                        print("[CONFIRMATION] Application submitted (profile visible)!")
                        return True
                except PlaywrightTimeoutError:
                    pass
                print("[FAILURE] Clicked Easy Apply but did not reach confirmation.")
                return False
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
                print(f"[FAILURE] Failed to navigate to the expected URL after {max_attempts} attempts. Last URL: {current_url}")
                return False
            next_button = page.wait_for_selector(
                next_in_application_button, timeout=10000)
            next_button.click()
            submit_button = page.wait_for_selector(
                selectors["submit_button"], timeout=10000)
            submit_button.click()
            last_page = page.context.pages[-1]
            # * Robust polling loop for confirmation selectors after submit
            confirmation_selectors = [
                ("application_submitted", selectors["application_submitted"]),
                ("application_submitted_any_h1", selectors["application_submitted_any_h1"]),
                ("profile_visible_application_submitted", selectors["profile_visible_application_submitted"])
            ]
            confirmation_found = False
            confirmation_text = ""
            max_wait_seconds = 30
            poll_interval = 0.5
            start_time = time.time()

            while time.time() - start_time < max_wait_seconds:
                for name, selector in confirmation_selectors:
                    try:
                        if page.is_visible(selector):
                            header_text = page.locator(selector).text_content()
                            print(f"[CONFIRMATION] Application submitted! ({name}): {header_text}")
                            confirmation_found = True
                            confirmation_text = header_text
                            break
                    except Exception:
                        continue
                if confirmation_found:
                    break
                time.sleep(poll_interval)

            if confirmation_found:
                last_page.close()
                return True
            else:
                print("[FAILURE] Confirmation banner did not appear after waiting.")
                last_page.close()
                return False
        except PlaywrightTimeoutError as e:
            print(f"Timeout during the application process: {e}")
            return False
        except Exception as e:
            print(f"Error during the application process: {e}")
            return False
    else:
        last_page = page.context.pages[-1]
        last_page.close()
        print("[FAILURE] Easy Apply button clicked but application was not confirmed submitted.")
        return False
