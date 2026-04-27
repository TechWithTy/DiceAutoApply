"""
Main entrypoint for Dice automation using refactored modular utilities.
"""
import sys
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
from app.dice.utils.profile_to_url import userprofile_to_search_url

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
            login_links = page.locator('a[href*="/dashboard/login"], a[href*="/register"], a[href*="/employers/login"]').count()
            login_register_text = page.locator("button:has-text('Login/Register'), a:has-text('Login'), a:has-text('Register')").count()
            if login_links > 0 or login_register_text > 0:
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
    """
    Main workflow for automating Dice job applications.
    """
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
                            print(f"Applying to {len(filtered_rec_job_ids)} Recommended Easy Apply Jobs...")
                            processed_job_ids.update(filtered_rec_job_ids)
                            (
                                app, fail, fail_jobs, skip, alr, no_btn, succ
                            ) = write_job_titles_to_file(page, filtered_rec_job_ids, page.url, known_applied_job_ids=applied_job_ids)
                            
                            print(f"Recommended Jobs successfully applied: {app}")
                            total_jobs_processed += len(filtered_rec_job_ids)
                    else:
                        print("No new Easy Apply recommended jobs found to apply for.")
                else:
                    print("No recommended jobs list found on dashboard.")
            except Exception as e:
                print(f"Error processing recommended jobs: {e}")
            print("======================================\n")

        job_titles_to_process = [] if only_recommended else user_profile.job_titles
        for job_title in job_titles_to_process:
            if max_jobs is not None and total_jobs_processed >= max_jobs:
                print(f"[LIMIT] Reached max jobs for run ({max_jobs}). Stopping.")
                break
            # Session can expire during long runs; re-auth before each title.
            if not _session_is_valid(page):
                print("[SESSION] Detected logged-out state before title search. Re-authenticating.")
                login(page, secret_email, secret_password)
                if reuse_session and session_file:
                    try:
                        context.storage_state(path=str(session_file))
                        print(f"[SESSION] Saved refreshed storage state: {session_file}")
                    except Exception as e:
                        print(f"[SESSION] Failed to save refreshed storage state: {e}")
            search_keyword = job_title.title
            print('Processing job title:', search_keyword)
            search_url = userprofile_to_search_url(search_keyword)
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
                    # Skip this job title and continue to the next to keep the run alive
                    continue
            # Wait a bit more for network to settle before scraping
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                # Not fatal; proceed with a short sleep buffer
                pass
            time.sleep(2)
            if debug_dir:
                _save_debug_html(page, debug_dir, search_keyword)
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

            if max_jobs_per_title is not None:
                job_ids = job_ids[:max_jobs_per_title]
                print(f"[LIMIT] Per-title cap applied ({max_jobs_per_title}). Jobs queued: {len(job_ids)}")
            if max_jobs is not None:
                remaining = max_jobs - total_jobs_processed
                if remaining <= 0:
                    print(f"[LIMIT] Reached max jobs for run ({max_jobs}).")
                    break
                if len(job_ids) > remaining:
                    job_ids = job_ids[:remaining]
                    print(f"[LIMIT] Run cap remaining {remaining}. Trimming current queue to {len(job_ids)}.")

            if not job_ids:
                print("[SKIP] No jobs queued for this title after filters/limits.")
                continue
            processed_job_ids.update(job_ids)

            (
                applied,
                failed,
                failed_jobs,
                skipped,
                already_applied_count,
                no_apply_button_count,
                success_count,
            ) = write_job_titles_to_file(page, job_ids, url, known_applied_job_ids=applied_job_ids)
            print("\n========== APPLICATION SUMMARY ==========")
            print(f"Jobs successfully applied: {applied}")
            print(f"Jobs failed: {failed}")
            print(f"Jobs skipped: {skipped}")
            print(
                "Breakdown - already_applied: "
                f"{already_applied_count}, no_apply_button: {no_apply_button_count}, success: {success_count}"
            )
            total_jobs_processed += len(job_ids)
            print(f"[TOTAL] Jobs processed so far: {total_jobs_processed}")
            if failed_jobs:
                print("Failed jobs:")
                for job in failed_jobs:
                    print("-", job)
            print("========================================\n")
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
