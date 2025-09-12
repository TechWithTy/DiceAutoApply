from playwright.sync_api import Page
import csv
from datetime import datetime
import os
from typing import List
from .apply import evaluate_and_apply

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
    # Updated fieldnames for Excel-friendly CSV (as requested)
    fieldnames = ["Job title", "URL", "Timestamp", "Status", "Message", "Date", "Status"]
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
                                    "Job title": job_title,
                                    "URL": job_id_url,
                                    "Timestamp": dt_str.split()[1] if ' ' in dt_str else dt_str,  # Time part
                                    "Status": status,
                                    "Message": error_message,
                                    "Date": dt_str.split()[0] if ' ' in dt_str else dt_str,      # Date part
                                    "Status": status
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
                "Job title": job_title,
                "URL": job_id_url,
                "Timestamp": dt_str.split()[1] if ' ' in dt_str else dt_str,  # Time part
                "Status": status,
                "Message": error_message,
                "Date": dt_str.split()[0] if ' ' in dt_str else dt_str,      # Date part
                "Status": status
            })
    return applied, failed, failed_jobs