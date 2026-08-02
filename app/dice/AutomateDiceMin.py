"""
Main entrypoint for Dice automation using refactored modular utilities.
"""
import sys
import argparse
print(sys.path)

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv, find_dotenv, dotenv_values
import os
from pathlib import Path
from _data_.Profiles.main_profile import user_profile, display_profile
# from _data_.Filters.diceFilterSettings import dice_job_filter, JobFilter  # Removed unused imports
from app.dice.utils.login import login
from app.dice.utils.extract import extract_job_ids
from app.dice.utils.apply import load_applied_job_ids, write_job_titles_to_file
from app.dice.utils.utils import close_extra_tabs, logout_and_close
from typing import List, Optional, Set
import time
from datetime import datetime
from app.dice.utils.profile_to_url import userprofile_locations, userprofile_to_search_urls

# Load environment variables from .env file (robust search)
# 1) Prefer loading relative to the project root derived from this file's location
# 2) Fallback to find_dotenv (search up the tree)
# 3) Fallback to a plain load_dotenv() which uses CWD
project_root = Path(__file__).resolve().parents[2]  # .../DiceAutoApply
print(f"[dotenv] Project root resolved to: {project_root}")
candidate_envs = [
    project_root / ".env",
    project_root / ".env.local",
    Path.cwd() / ".env",
]
for p in candidate_envs:
    try:
        print(f"[dotenv] Candidate: {p} | exists: {p.is_file()}")
    except Exception as e:
        print(f"[dotenv] Candidate check error for {p}: {e}")
loaded_from = None
for env_path in candidate_envs:
    if env_path.is_file():
        if load_dotenv(dotenv_path=str(env_path)):
            loaded_from = str(env_path)
            break

if not loaded_from:
    # Search upwards from CWD and also try default
    found = find_dotenv(usecwd=True)
    if found:
        if load_dotenv(dotenv_path=found):
            loaded_from = found
    if not loaded_from:
        if load_dotenv():
            loaded_from = "CWD/.env"

print(f"[dotenv] Loaded from: {loaded_from if loaded_from else 'None found'}")

def _slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower() or "untitled"


def _save_debug_html(page, debug_dir: Path, job_title: str) -> Optional[Path]:
    try:
        debug_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = debug_dir / f"{stamp}_{_slugify(job_title)}.html"
        file_path.write_text(page.content(), encoding="utf-8")
        print(f"[DEBUG] Saved HTML snapshot: {file_path}")
        return file_path
    except Exception as e:
        print(f"[DEBUG] Failed to save HTML snapshot: {e}")
        return None


def _sync_visible_search_fields(page, search_keyword: str, location: str) -> None:
    """Keep only the keyword field aligned without disturbing URL-selected city."""
    field_pairs = [
        (
            search_keyword,
            [
                'input[name="q"]',
                'input[placeholder*="job title" i]',
                'input[placeholder*="search jobs" i]',
                '#typeaheadInput',
            ],
            "keyword",
        ),
    ]

    # Dice's location control is an autocomplete. Refilling it after navigation
    # can clear the committed URL location when the exact display string differs
    # from Dice's suggestion text. The URL generated for this queue already holds
    # the intended city, so leave that field untouched.
    if location:
        print(f"[SEARCH UI] Preserving URL-selected location: {location}")

    for target_value, selectors, label in field_pairs:
        if not target_value:
            continue
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                locator.wait_for(state="visible", timeout=1500)
                current_value = (locator.input_value() or "").strip()
                if current_value == target_value:
                    break
                locator.click()
                locator.fill("")
                locator.fill(target_value)
                locator.dispatch_event("input")
                locator.dispatch_event("change")
                print(f"[SEARCH UI] Synced visible {label} field to: {target_value}")
                break
            except Exception:
                continue


def _session_is_valid(page) -> bool:
    """Check if current browser context is already authenticated on Dice."""
    try:
        page.goto("https://www.dice.com/jobs", wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        lower_url = page.url.lower()
        if "dashboard/login" in lower_url or "/login" in lower_url:
            return False
        # Dice can still render jobs while anonymous; detect login/register prompts.
        try:
            login_prompt_selectors = [
                'a[href*="/dashboard/login"]',
                'a[href*="/register"]',
                'a[href*="/employers/login"]',
                "button:has-text('Login/Register')",
                "a:has-text('Login')",
                "a:has-text('Register')",
            ]
            for selector in login_prompt_selectors:
                locator = page.locator(selector)
                for index in range(min(locator.count(), 3)):
                    if locator.nth(index).is_visible():
                        return False
        except Exception:
            pass
        return True
    except Exception:
        return False


def main(
    max_jobs: Optional[int] = None,
    max_jobs_per_title: Optional[int] = None,
    debug_html_dir: Optional[str] = "app/dice/_experimental_/debug",
    session_state_path: Optional[str] = "storage/dice_session_state.json",
    reuse_session: bool = True,
    logout_on_exit: bool = False,
    headless: bool = False,
    process_recommended: bool = True,
    only_recommended: bool = False,
) -> None:
    # Parse CLI args when invoked via the console entry point (apply-dice).
    # Only parse if main() was called with all defaults (i.e. from the entry point,
    # not from run_dice.py which already parsed args and passes them explicitly).
    import inspect
    frame = inspect.currentframe()
    caller_locals = frame.f_back.f_locals if frame and frame.f_back else {}
    _called_from_entry_point = (
        max_jobs is None
        and max_jobs_per_title is None
        and headless is False
        and reuse_session is True
    )
    if _called_from_entry_point and len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Run Dice auto-apply workflow.")
        parser.add_argument("--max-jobs", type=int, default=None)
        parser.add_argument("--max-jobs-per-title", type=int, default=None)
        parser.add_argument("--debug-html-dir", type=str, default="app/dice/_experimental_/debug")
        parser.add_argument("--session-state", type=str, default="storage/dice_session_state.json")
        parser.add_argument("--no-session-reuse", action="store_true")
        parser.add_argument("--logout-on-exit", action="store_true")
        parser.add_argument("--headless", action="store_true")
        parser.add_argument("--no-recommended", action="store_true")
        parser.add_argument("--only-recommended", action="store_true")
        args = parser.parse_args()
        max_jobs = args.max_jobs
        max_jobs_per_title = args.max_jobs_per_title
        debug_html_dir = args.debug_html_dir
        session_state_path = args.session_state
        reuse_session = not args.no_session_reuse
        logout_on_exit = args.logout_on_exit
        headless = args.headless
        process_recommended = not args.no_recommended
        only_recommended = args.only_recommended
        print(f"[CLI] headless={headless}, max_jobs={max_jobs}, only_recommended={only_recommended}")
    print("started")
    display_profile(user_profile)
    if max_jobs is not None and max_jobs <= 0:
        print(f"[LIMIT] Ignoring non-positive max_jobs value: {max_jobs}")
        max_jobs = None
    if max_jobs_per_title is not None and max_jobs_per_title <= 0:
        print(f"[LIMIT] Ignoring non-positive max_jobs_per_title value: {max_jobs_per_title}")
        max_jobs_per_title = None

    # Support alternate variable names as fallback
    secret_email = os.getenv('EMAIL') or os.getenv('DICE_EMAIL')
    secret_password = os.getenv('PASSWORD') or os.getenv('DICE_PASSWORD')

    # If still missing, directly parse .env and inject
    if not secret_email or not secret_password:
        direct_env_path = None
        for p in [project_root / ".env", Path.cwd() / ".env", project_root / ".env.local"]:
            if p.is_file():
                direct_env_path = p
                break
        if direct_env_path:
            print(f"[dotenv] Directly parsing: {direct_env_path}")
            vals = dotenv_values(direct_env_path)
            # Normalize keys and trim quotes/whitespace
            def norm(v):
                if v is None:
                    return None
                v = v.strip()
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                return v.strip()
            e = norm(vals.get('EMAIL') or vals.get('DICE_EMAIL'))
            pw = norm(vals.get('PASSWORD') or vals.get('DICE_PASSWORD'))
            if e and not secret_email:
                os.environ['EMAIL'] = e
                secret_email = e
            if pw and not secret_password:
                os.environ['PASSWORD'] = pw
                secret_password = pw
        else:
            print("[dotenv] No .env file found for direct parse fallback.")
    masked_email = (secret_email[:2] + "***" + secret_email[-2:]) if secret_email else None
    print(f"[dotenv] EMAIL present: {'yes' if secret_email else 'no'} ({masked_email if secret_email else ''})")
    print(f"[dotenv] PASSWORD present: {'yes' if bool(secret_password) else 'no'}")
    # Validate credentials early to avoid Playwright fill() receiving a missing value
    if not secret_email or not secret_password:
        raise RuntimeError(
            "Missing EMAIL or PASSWORD environment variables. Ensure your .env contains EMAIL=... and PASSWORD=... and that it is discoverable."
        )
    custom_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    debug_dir = Path(debug_html_dir) if debug_html_dir else None
    session_file = Path(session_state_path) if session_state_path else None
    if session_file:
        session_file.parent.mkdir(parents=True, exist_ok=True)
    total_jobs_processed = 0
    # Grand-total accumulators across all job titles and recommended jobs
    grand_applied = 0
    grand_failed = 0
    grand_skipped = 0
    grand_already_applied = 0
    grand_no_btn = 0
    grand_success = 0
    applied_job_ids = load_applied_job_ids()
    processed_job_ids: Set[str] = set()
    if applied_job_ids:
        print(f"[TRACKING] Loaded {len(applied_job_ids)} previously applied Dice job IDs.")
    first_run = True

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        context_kwargs = {"user_agent": custom_user_agent}
        if reuse_session and session_file and session_file.is_file():
            context_kwargs["storage_state"] = str(session_file)
            print(f"[SESSION] Using existing storage state: {session_file}")
        context = browser.new_context(**context_kwargs)
        try:
            context.set_default_navigation_timeout(60000)
            context.set_default_timeout(45000)
        except Exception as e:
            print(f"[timeouts] Could not set default timeouts: {e}")

        page = context.new_page()

        authenticated = _session_is_valid(page) if reuse_session else False
        if authenticated:
            print("[SESSION] Existing Dice session is valid. Skipping login.")
        else:
            print("[SESSION] Session invalid or reuse disabled. Performing login.")
            login(page, secret_email, secret_password)
            if reuse_session and session_file:
                try:
                    context.storage_state(path=str(session_file))
                    print(f"[SESSION] Saved refreshed storage state: {session_file}")
                except Exception as e:
                    print(f"[SESSION] Failed to save storage state: {e}")

        if process_recommended:
            print("\n========== RECOMMENDED JOBS ==========")
            print("Navigating to recommended jobs page...")
            try:
                page.goto("https://www.dice.com/recommended-jobs", wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_load_state("networkidle", timeout=20000)
                except Exception:
                    pass
                
                if page.locator('[data-testid="recommended-jobs-list"]').count() > 0:
                    print("Found Recommended Jobs list!")
                    rec_job_ids: List[str] = []
                    extract_job_ids(page, rec_job_ids, only_easy_apply=True)
                    
                    filtered_rec_job_ids: List[str] = []
                    for job_id in rec_job_ids:
                        if job_id in processed_job_ids or job_id in applied_job_ids:
                            continue
                        filtered_rec_job_ids.append(job_id)
                    
                    if filtered_rec_job_ids:
                        if max_jobs is not None:
                            remaining = max_jobs - total_jobs_processed
                            if remaining > 0 and len(filtered_rec_job_ids) > remaining:
                                filtered_rec_job_ids = filtered_rec_job_ids[:remaining]
                                print(f"[LIMIT] Trimming recommended jobs queue to {len(filtered_rec_job_ids)}.")
                        
                        if filtered_rec_job_ids and (max_jobs is None or total_jobs_processed < max_jobs):
                            remaining = None if max_jobs is None else max_jobs - total_jobs_processed
                            print(f"Applying to {len(filtered_rec_job_ids)} Recommended Easy Apply Jobs...")
                            processed_job_ids.update(filtered_rec_job_ids)
                            (
                                app, fail, fail_jobs, skip, alr, no_btn, succ, processed_count
                            ) = write_job_titles_to_file(
                                page,
                                filtered_rec_job_ids,
                                page.url,
                                known_applied_job_ids=applied_job_ids,
                                max_jobs_to_process=remaining,
                            )
                            grand_applied += app
                            grand_failed += fail
                            grand_skipped += skip
                            grand_already_applied += alr
                            grand_no_btn += no_btn
                            grand_success += succ
                            print(f"Recommended Jobs successfully applied: {app}")
                            total_jobs_processed += processed_count
                    else:
                        print("No new Easy Apply recommended jobs found to apply for.")
                else:
                    print("No recommended jobs list found on dashboard.")
            except Exception as e:
                print(f"Error processing recommended jobs: {e}")
            print("======================================\n")

        job_titles_to_process = [] if only_recommended else user_profile.job_titles
        locations = userprofile_locations(user_profile)
        for job_title in job_titles_to_process:
            search_keyword = job_title.title
            for location in locations:
                workplace_settings = (
                    getattr(job_title, "remote_work_settings", None)
                    if location.casefold() == "remote"
                    else getattr(job_title, "work_settings", None)
                )
                search_url = userprofile_to_search_urls(
                    search_keyword,
                    workplace_settings=workplace_settings,
                )[locations.index(location)]
                if max_jobs is not None and total_jobs_processed >= max_jobs:
                    print(f"[LIMIT] Reached max jobs for run ({max_jobs}). Stopping.")
                    break
                # Session can expire during long runs; re-auth before each title/location search.
                if not _session_is_valid(page):
                    print("[SESSION] Detected logged-out state before title search. Re-authenticating.")
                    login(page, secret_email, secret_password)
                    if reuse_session and session_file:
                        try:
                            context.storage_state(path=str(session_file))
                            print(f"[SESSION] Saved refreshed storage state: {session_file}")
                        except Exception as e:
                            print(f"[SESSION] Failed to save refreshed storage state: {e}")
                print(f"Processing job title: {search_keyword} | Location: {location}")
                print(f"Navigating to search URL: {search_url}")
                if not first_run:
                    close_extra_tabs(context)
                    page = context.new_page()  # Always create a new page after closing tabs
                else:
                    first_run = False
                    # Use the original page created before the loop
                # More robust navigation with retry and longer timeouts
                try:
                    page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                except Exception as e:
                    print(f"[NAVIGATE] First attempt failed ({e}). Retrying once...")
                    try:
                        page.close()
                    except Exception:
                        pass
                    page = context.new_page()
                    try:
                        page.goto(search_url, wait_until="domcontentloaded", timeout=90000)
                    except Exception as e2:
                        print(f"[NAVIGATE] Second attempt failed: {e2}")
                        # Skip this job title/location and continue to keep the run alive
                        continue
                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                except Exception:
                    pass
                time.sleep(2)
                _sync_visible_search_fields(page, search_keyword, location)
                if debug_dir:
                    _save_debug_html(page, debug_dir, f"{search_keyword}_{location}")
                job_ids: List[str] = []
                url = page.url
                extract_job_ids(page, job_ids)

                filtered_job_ids: List[str] = []
                for job_id in job_ids:
                    if job_id in processed_job_ids:
                        print(f"[SKIP/RUN DUPLICATE] Already processed in this run: {job_id}")
                        continue
                    if job_id in applied_job_ids:
                        print(f"[SKIP/TRACKED] Already applied from local history: {job_id}")
                        continue
                    filtered_job_ids.append(job_id)
                if len(filtered_job_ids) != len(job_ids):
                    print(
                        f"[TRACKING] Queued {len(filtered_job_ids)} new IDs "
                        f"after removing {len(job_ids) - len(filtered_job_ids)} tracked/duplicate IDs."
                    )
                job_ids = filtered_job_ids

                if max_jobs is not None:
                    remaining = max_jobs - total_jobs_processed
                    if remaining <= 0:
                        print(f"[LIMIT] Reached max jobs for run ({max_jobs}).")
                        break

                if not job_ids:
                    print("[SKIP] No jobs queued for this title/location after filters/limits.")
                    continue
                processed_job_ids.update(job_ids)

                queue_limit = max_jobs_per_title
                if max_jobs is not None:
                    remaining = max_jobs - total_jobs_processed
                    queue_limit = remaining if queue_limit is None else min(queue_limit, remaining)
                if queue_limit is not None:
                    print(f"[LIMIT] Eligible-job cap for this queue: {queue_limit}")

                (
                    applied,
                    failed,
                    failed_jobs,
                    skipped,
                    already_applied_count,
                    no_apply_button_count,
                    success_count,
                    processed_count,
                ) = write_job_titles_to_file(
                    page,
                    job_ids,
                    url,
                    known_applied_job_ids=applied_job_ids,
                    target_job=job_title,
                    max_jobs_to_process=queue_limit,
                )
                grand_applied += applied
                grand_failed += failed
                grand_skipped += skipped
                grand_already_applied += already_applied_count
                grand_no_btn += no_apply_button_count
                grand_success += success_count
                total_jobs_processed += processed_count
                print(f"\n---------- [{search_keyword} | {location}] Summary ----------")
                print(f"  Applied:       {applied}")
                print(f"  Skipped:       {skipped} (already_applied={already_applied_count}, no_button={no_apply_button_count})")
                print(f"  Failed:        {failed}")
                print(f"  Processed so far (run total): {total_jobs_processed}")
                if failed_jobs:
                    print("  Failed jobs:")
                    for job in failed_jobs:
                        print("    -", job)
                print("-" * 50)
            if max_jobs is not None and total_jobs_processed >= max_jobs:
                break
        # ========== GRAND TOTAL SUMMARY ==========
        print("\n" + "=" * 50)
        print("          GRAND TOTAL SUMMARY FOR RUN")
        print("=" * 50)
        print(f"  Total jobs successfully applied: {grand_applied}")
        print(f"  Total jobs skipped:              {grand_skipped}")
        print(f"    - Already applied (history):   {grand_already_applied}")
        print(f"    - No Easy Apply button:         {grand_no_btn}")
        print(f"  Total jobs failed:               {grand_failed}")
        print(f"  Total jobs processed this run:   {total_jobs_processed}")
        print("=" * 50 + "\n")

        if reuse_session and session_file:
            try:
                context.storage_state(path=str(session_file))
                print(f"[SESSION] Persisted storage state: {session_file}")
            except Exception as e:
                print(f"[SESSION] Failed to persist storage state at shutdown: {e}")

        if logout_on_exit:
            logout_and_close(page, browser)
        else:
            print("[SESSION] Keeping session active (no logout) to reduce repeated logins.")
            try:
                page.close()
            except Exception:
                pass
            browser.close()

if __name__ == "__main__":
    main()
