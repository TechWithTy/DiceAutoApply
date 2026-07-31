"""
Handles job application actions for Dice automation.
"""
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
import time
from typing import List, Optional, Set
import os
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from _data_.Profiles.main_profile import user_profile

next_in_application_button = 'button.seds-button-primary.btn-next'

import csv

CSV_FIELDNAMES = ["job_id", "job_title", "job_url", "datetime", "status", "error_message"]
APPLIED_STATUSES = {"success", "already_applied"}


def _slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower() or "job"


def _extract_job_id_from_url(value: str) -> str:
    try:
        path = urlparse(value).path
    except Exception:
        path = value.split("?", 1)[0]
    marker = "/job-detail/"
    if marker not in path:
        return ""
    return path.split(marker, 1)[1].strip("/").split("/", 1)[0]


def _looks_like_header(row: List[str]) -> bool:
    normalized = {cell.strip().lower() for cell in row}
    return "job_url" in normalized and "status" in normalized


def _ensure_results_csv(csv_file: str) -> None:
    output_dir = os.path.dirname(csv_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    path = Path(csv_file)
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDNAMES).writeheader()
        return

    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if not rows:
        with path.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDNAMES).writeheader()
        return

    first_row = rows[0]
    if _looks_like_header(first_row) and first_row == CSV_FIELDNAMES:
        return

    migrated_rows = []
    if _looks_like_header(first_row):
        old_fieldnames = first_row
        data_rows = rows[1:]
        for row in data_rows:
            record = dict(zip(old_fieldnames, row))
            job_url = record.get("job_url", "")
            migrated_rows.append({
                "job_id": record.get("job_id") or _extract_job_id_from_url(job_url),
                "job_title": record.get("job_title", ""),
                "job_url": job_url,
                "datetime": record.get("datetime", ""),
                "status": record.get("status", ""),
                "error_message": record.get("error_message", ""),
            })
    else:
        for row in rows:
            padded = row + [""] * max(0, 5 - len(row))
            job_title, job_url, dt_str, status, error_message = padded[:5]
            migrated_rows.append({
                "job_id": _extract_job_id_from_url(job_url),
                "job_title": job_title,
                "job_url": job_url,
                "datetime": dt_str,
                "status": status,
                "error_message": error_message,
            })

    backup_path = path.with_suffix(path.suffix + ".bak")
    if not backup_path.exists():
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(migrated_rows)


def _dry_run_enabled() -> bool:
    return os.getenv("DICE_DRY_RUN", "").strip().lower() in {"1", "true", "yes", "on"}


def _allowed_location_tokens(profile=user_profile) -> tuple[set[str], bool]:
    raw_locations = getattr(profile, "cities", None) or [getattr(profile, "city", "")]
    normalized = [
        str(value).strip().lower()
        for value in raw_locations
        if str(value).strip()
    ]
    allow_remote = "remote" in normalized
    allowed_cities = {value for value in normalized if value != "remote"}
    return allowed_cities, allow_remote


def _job_matches_allowed_locations(job_title: str, profile=user_profile) -> bool:
    title = (job_title or "").strip().lower()
    allowed_cities, allow_remote = _allowed_location_tokens(profile)

    if allow_remote and "remote" in title:
        return True
    if any(city in title for city in allowed_cities):
        return True
    return False


def load_applied_job_ids(csv_file: str = "output/job_application_results.csv") -> Set[str]:
    """Load Dice job IDs that should not be applied to again."""
    path = Path(csv_file)
    if not path.exists():
        return set()
    _ensure_results_csv(csv_file)
    applied_job_ids: Set[str] = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            status = (row.get("status") or "").strip().lower()
            if status not in APPLIED_STATUSES:
                continue
            job_id = (row.get("job_id") or "").strip()
            if not job_id:
                job_id = _extract_job_id_from_url(row.get("job_url", ""))
            if job_id:
                applied_job_ids.add(job_id)
    return applied_job_ids


def _dump_no_apply_debug(page: Page, job_title: str, job_url: str) -> None:
    debug_dir = Path(os.getenv("DICE_APPLY_DEBUG_DIR", "app/dice/_experimental_/debug"))
    debug_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{stamp}_{_slugify(job_title)}"
    html_path = debug_dir / f"{base}_job_detail_no_apply.html"
    txt_path = debug_dir / f"{base}_button_targets.txt"
    png_path = debug_dir / f"{base}_job_detail_no_apply.png"
    try:
        html_path.write_text(page.content(), encoding="utf-8")
    except Exception as e:
        print(f"[DEBUG] Could not save detail HTML: {e}")
    try:
        page.screenshot(path=str(png_path), full_page=True)
    except Exception as e:
        print(f"[DEBUG] Could not save detail screenshot: {e}")
    try:
        targets = page.evaluate('''
            () => {
                const rows = [];
                const els = Array.from(document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"], apply-button-wc, [data-testid], [data-cy]'));
                for (const el of els) {
                    const text = (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
                    const attr = (name) => el.getAttribute && el.getAttribute(name) ? el.getAttribute(name) : '';
                    if (!text && !attr('data-testid') && !attr('data-cy') && !attr('aria-label')) continue;
                    const row = {
                        tag: el.tagName,
                        id: el.id || '',
                        cls: (el.className || '').toString().slice(0, 120),
                        text: text.slice(0, 160),
                        testid: attr('data-testid'),
                        cy: attr('data-cy'),
                        aria: attr('aria-label'),
                        href: attr('href'),
                    };
                    rows.push(row);
                }
                return rows;
            }
        ''')
        lines = [f"URL: {job_url}", ""]
        for r in targets:
            lines.append(
                f"{r['tag']} id={r['id']} data-testid={r['testid']} data-cy={r['cy']} aria={r['aria']} href={r['href']} class={r['cls']} text={r['text']}"
            )
        txt_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"[DEBUG] Saved no-apply debug bundle: {html_path}, {png_path}, {txt_path}")
    except Exception as e:
        print(f"[DEBUG] Could not enumerate button targets: {e}")

def write_job_titles_to_file(
    page: Page,
    job_ids: List[str],
    url: str,
    csv_file: str = 'output/job_application_results.csv',
    known_applied_job_ids: Optional[Set[str]] = None,
):
    """
    Writes job application results to
    a CSV file, including job title, URL, date/time, status, and error message.
    Returns (applied_count, failed_count, failed_jobs)
    """
    print("number of All job IDs:" + str(len(job_ids)))
    applied = 0
    failed = 0
    skipped = 0  # already applied, etc.
    # Detailed counters for GRAND SUMMARY
    already_applied_count = 0
    no_apply_button_count = 0
    success_count = 0
    failed_jobs = []
    parts = url.split('?', 1)
    query_string = parts[1] if len(parts) > 1 else ""
    known_applied_job_ids = known_applied_job_ids if known_applied_job_ids is not None else set()
    _ensure_results_csv(csv_file)
    for job_id in job_ids:
        job_id_url = "https://www.dice.com/job-detail/" + job_id
        if query_string:
            job_id_url = job_id_url + "?" + query_string
        dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        job_title = job_id_url  # fallback
        status = "failed"
        error_message = ""
        if job_id in known_applied_job_ids:
            skipped += 1
            already_applied_count += 1
            print(f"[SKIP/TRACKED] Already applied according to local history: {job_id}")
            continue
        try:
            try:
                new_page = page.context.new_page()
                try:
                    new_page.goto(job_id_url)
                    new_page.wait_for_load_state("load")
                    job_title = new_page.evaluate("document.title")
                    if not _job_matches_allowed_locations(job_title):
                        status = "location_filtered"
                        error_message = "Job location is outside allowed profile cities."
                        skipped += 1
                        print(f"[SKIP/LOCATION] {job_title} ({job_id_url})")
                        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
                            writer.writerow({
                                "job_id": job_id,
                                "job_title": job_title,
                                "job_url": job_id_url,
                                "datetime": dt_str,
                                "status": status,
                                "error_message": error_message
                            })
                        new_page.close()
                        continue
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
                            skipped += 1
                            already_applied_count += 1
                            known_applied_job_ids.add(job_id)
                            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                                writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
                                writer.writerow({
                                    "job_id": job_id,
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
                try:
                    apply_result = evaluate_and_apply(new_page, applied + 1)
                    if apply_result == "success":
                        status = "success"
                        applied += 1
                        success_count += 1
                        known_applied_job_ids.add(job_id)
                        print(f"[APPLY SUCCESS] {job_title} ({job_id_url})")
                        error_message = ""
                    elif apply_result == "already_applied":
                        status = "already_applied"
                        skipped += 1
                        already_applied_count += 1
                        known_applied_job_ids.add(job_id)
                        error_message = "Application already submitted."
                        print(f"[ALREADY APPLIED] {job_title} ({job_id_url})")
                    elif apply_result == "no_easy_apply":
                        status = "no_apply_button"
                        skipped += 1
                        no_apply_button_count += 1
                        error_message = "Easy Apply button not found on job detail page."
                        print(f"[NO APPLY BUTTON] {job_title} ({job_id_url})")
                        _dump_no_apply_debug(new_page, job_title, job_id_url)
                    elif apply_result == "dry_run":
                        status = "dry_run"
                        skipped += 1
                        error_message = "Dry run: Easy Apply control found, application was not submitted."
                        print(f"[DRY RUN] {job_title} ({job_id_url})")
                    else:
                        status = "failed"
                        failed += 1
                        failed_jobs.append(job_title)
                        error_message = "evaluate_and_apply returned failed"
                        print(f"[APPLY FAILED] {job_title} ({job_id_url}) - {error_message}")
                        _dump_no_apply_debug(new_page, job_title, job_id_url)
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
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writerow({
                "job_id": job_id,
                "job_title": job_title,
                "job_url": job_id_url,
                "datetime": dt_str,
                "status": status,
                "error_message": error_message
            })
    return applied, failed, failed_jobs, skipped, already_applied_count, no_apply_button_count, success_count

def evaluate_and_apply(page: Page, val: int) -> str:
    selectors = {
        # * Updated Easy Apply button selector to target <apply-button-wc> inside #applyButton (pierce shadow DOM)
        # ! Use Playwright shadow selector, filter for text in code
        "easy_apply_wc_button": 'div#applyButton apply-button-wc >> shadow=button',
        "submit_button": '//button/span[text()="Submit"]/..',
        "application_submitted": 'div.post-apply-header-text > h1:has-text("Application submitted")',
        "application_submitted_any_h1": 'h1:has-text("Application submitted")',
        "profile_visible_application_submitted":   'div.banner-message.sc-dhi-candidates-modal-2:has-text("Your Application is on its way.")',
        "application_success_card": '[data-testid="job-application-success-card"]',
    }

    def _first_visible(selectors_list, timeout_ms=2500):
        for sel in selectors_list:
            try:
                loc = page.locator(sel).first
                loc.wait_for(state="visible", timeout=timeout_ms)
                return loc
            except Exception:
                continue
        return None

    def _is_apply_flow_url(url: str) -> bool:
        return (
            "/apply" in url
            or "/job-detail/" in url
            or "/job-applications/" in url
        )
    # Check common already-applied cues in both modern and legacy layouts.
    try:
        direct_apply_btn = page.query_selector('button[data-testid="apply-button"], [data-testid="apply-button"]')
        if direct_apply_btn is not None:
            txt = (direct_apply_btn.inner_text() or "").strip().lower()
            if "applied" in txt or "application submitted" in txt:
                print("[ALREADY APPLIED] apply-button indicates already applied.")
                return "already_applied"
    except Exception:
        pass

    # * Check if already applied by looking for <application-submitted> with 'Application Submitted' text in shadow DOM of <apply-button-wc>
    already_applied_elem = page.query_selector('div#applyButton apply-button-wc')
    if already_applied_elem is not None:
        is_submitted = page.evaluate('''
            (el) => {
                if (!el.shadowRoot) return false;
                const submitted = el.shadowRoot.querySelector("application-submitted .app-text");
                return submitted && submitted.textContent.includes("Application Submitted");
            }
        ''', already_applied_elem)
        if is_submitted:
            print("[ALREADY APPLIED] Application Submitted found in <apply-button-wc> shadow DOM. Skipping job as already applied.")
            return "already_applied"

    if _dry_run_enabled():
        try:
            direct_apply_btn = page.query_selector('button[data-testid="apply-button"], [data-testid="apply-button"]')
            if direct_apply_btn is not None and direct_apply_btn.is_visible():
                button_text = (direct_apply_btn.inner_text() or "").strip().lower()
                if "applied" in button_text or "application submitted" in button_text:
                    return "already_applied"
                if "apply" in button_text:
                    print("[DRY RUN] Easy Apply control found; skipping click/submit.")
                    return "dry_run"
        except Exception:
            pass
        try:
            found_shadow_or_dom_apply = page.evaluate('''
                (function() {
                    const wc = document.querySelector('div#applyButton apply-button-wc');
                    if (wc && wc.shadowRoot) {
                        const btns = wc.shadowRoot.querySelectorAll('button');
                        for (const btn of btns) {
                            const txt = btn.innerText.trim().toLowerCase();
                            if (txt === "easy apply" || txt === "apply now" || txt === "apply") {
                                return 1;
                            }
                        }
                    }
                    const candidates = Array.from(
                        document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]')
                    );
                    for (const el of candidates) {
                        const txt = ((el.innerText || el.textContent || el.value || '') + '').trim().toLowerCase();
                        if (txt.includes('easy apply') || txt.includes('apply now') || txt === 'apply') {
                            return 1;
                        }
                    }
                    return 0;
                })();
            ''')
            if found_shadow_or_dom_apply == 1:
                print("[DRY RUN] Easy Apply control found; skipping click/submit.")
                return "dry_run"
        except Exception:
            pass
        print("[DRY RUN] Easy Apply control not found.")
        return "no_easy_apply"
    # ! Removed all page refreshes when waiting for Easy Apply button (per user request)
    # * Extended wait time and improved logs
    # * Selector is now robust to match <div id="applyButton"><apply-button-wc ...></apply-button-wc></div>

    # Prefer current Dice target discovered from captured HTML.
    try:
        direct_apply_btn = page.query_selector('button[data-testid="apply-button"], [data-testid="apply-button"]')
        if direct_apply_btn is not None and direct_apply_btn.is_visible():
            button_text = (direct_apply_btn.inner_text() or "").strip()
            print(f"[Easy Apply] Clicking direct apply target data-testid=apply-button (text='{button_text}')")
            direct_apply_btn.click()
            found = True
        else:
            found = False
    except Exception:
        found = False

    # Keep this bounded so one slow card does not stall the whole run.
    EASY_APPLY_WAIT_SECONDS = int(os.getenv("DICE_EASY_APPLY_WAIT_SECONDS", "8"))
    if not found:
        print(f"[Easy Apply] Waiting up to {EASY_APPLY_WAIT_SECONDS}s for Easy Apply button to appear in <apply-button-wc>...")
        start_time = time.time()
        while time.time() - start_time < EASY_APPLY_WAIT_SECONDS:
            returned_value = page.evaluate('''
                (function() {
                    const wc = document.querySelector('div#applyButton apply-button-wc');
                    if (wc && wc.shadowRoot) {
                        const btns = wc.shadowRoot.querySelectorAll('button');
                        for (const btn of btns) {
                            const txt = btn.innerText.trim().toLowerCase();
                            if (txt === "easy apply" || txt === "apply now" || txt === "apply") {
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
            time.sleep(0.4)

    if not found:
        # Fallback: try regular DOM buttons/links that mention Easy Apply.
        returned_value = page.evaluate('''
            (function() {
                const candidates = Array.from(
                    document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]')
                );
                for (const el of candidates) {
                    const txt = ((el.innerText || el.textContent || el.value || '') + '').trim().toLowerCase();
                    if (txt.includes('easy apply') || txt.includes('apply now') || txt === 'apply') {
                        try { el.scrollIntoView({behavior: 'instant', block: 'center'}); } catch (_) {}
                        try { el.click(); return 1; } catch (_) {}
                    }
                }
                return 0;
            })();
        ''')
        if returned_value == 1:
            print("[Easy Apply] Clicked Easy Apply button via DOM fallback.")
            found = True
        else:
            print(f"[Easy Apply] No Easy Apply button found after {EASY_APPLY_WAIT_SECONDS}s + DOM fallback. Skipping this job.")
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
            return "no_easy_apply"
    # * End of Easy Apply wait logic: proceed from the first successful click.
    page.wait_for_load_state("load")
    try:
        time.sleep(2)
        # Detect login block after clicking apply.
        try:
            if page.locator('a[href*="/dashboard/login"], a[href*="/register"]').count() > 0:
                print("[APPLY BLOCKED] Login/register prompt detected after apply click.")
                return "failed"
        except Exception:
            pass

        max_attempts = 3
        attempt = 0
        current_url = page.url

        next_candidates = [
            next_in_application_button,
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'button[data-testid*="next"]',
        ]
        submit_candidates = [
            selectors["submit_button"],
            'button:has-text("Submit")',
            'button[data-testid*="submit"]',
            'button:has-text("Apply")',
        ]

        if _is_apply_flow_url(current_url):
            print(f"Already on the correct URL: {current_url}")
            # Some Dice flows land directly on success without intermediate controls.
            try:
                if page.is_visible(selectors["application_success_card"]):
                    print("[CONFIRMATION] Application submitted (success card)!")
                    return "success"
            except Exception:
                pass
            next_button = _first_visible(next_candidates, timeout_ms=3000)
            if next_button is not None:
                next_button.click()
                time.sleep(1)
            submit_button = _first_visible(submit_candidates, timeout_ms=3000)
            if submit_button is not None:
                submit_button.click()
            else:
                print("[APPLY FLOW] No submit/next controls found after apply click.")
            # After submit, robustly wait for confirmation selectors
            try:
                page.wait_for_selector(selectors["application_submitted"], timeout=15000)
                if page.is_visible(selectors["application_submitted"]):
                    print("[CONFIRMATION] Application submitted!")
                    return "success"
            except PlaywrightTimeoutError:
                pass
            try:
                page.wait_for_selector(selectors["profile_visible_application_submitted"], timeout=15000)
                if page.is_visible(selectors["profile_visible_application_submitted"]):
                    print("[CONFIRMATION] Application submitted (profile visible)!")
                    return "success"
            except PlaywrightTimeoutError:
                pass
            try:
                page.wait_for_selector(selectors["application_success_card"], timeout=10000)
                if page.is_visible(selectors["application_success_card"]):
                    print("[CONFIRMATION] Application submitted (success card)!")
                    return "success"
            except PlaywrightTimeoutError:
                pass
            print("[FAILURE] Clicked Easy Apply but did not reach confirmation.")
            return "failed"
        while attempt < max_attempts:
            current_url = page.url
            if _is_apply_flow_url(current_url):
                print(f"Successfully navigated to apply flow URL: {current_url}")
                break
            attempt += 1
            print(f"Attempt {attempt} failed. Waiting for apply flow URL, got: {current_url}")
            time.sleep(2)
        if attempt == max_attempts:
            print(f"[FAILURE] Failed to navigate to apply flow URL after {max_attempts} attempts. Last URL: {current_url}")
            return "failed"
        next_button = _first_visible(next_candidates, timeout_ms=5000)
        if next_button is not None:
            next_button.click()
            time.sleep(1)
        submit_button = _first_visible(submit_candidates, timeout_ms=5000)
        if submit_button is not None:
            submit_button.click()
        else:
            print("[APPLY FLOW] Submit control not found after navigation.")
        # Robust polling loop for confirmation selectors after submit
        confirmation_selectors = [
            ("application_submitted", selectors["application_submitted"]),
            ("application_submitted_any_h1", selectors["application_submitted_any_h1"]),
            ("profile_visible_application_submitted", selectors["profile_visible_application_submitted"]),
            ("application_success_card", selectors["application_success_card"]),
        ]
        confirmation_found = False
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
                        break
                except Exception:
                    continue
            if confirmation_found:
                break
            time.sleep(poll_interval)

        if confirmation_found:
            return "success"
        print("[FAILURE] Confirmation banner did not appear after waiting.")
        return "failed"
    except PlaywrightTimeoutError as e:
        print(f"Timeout during the application process: {e}")
        return "failed"
    except Exception as e:
        print(f"Error during the application process: {e}")
        return "failed"
