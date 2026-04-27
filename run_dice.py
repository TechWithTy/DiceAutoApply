import argparse

from app.dice.AutomateDiceMin import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Dice auto-apply workflow.")
    parser.add_argument("--max-jobs", type=int, default=None, help="Maximum number of jobs to process for this run.")
    parser.add_argument("--max-jobs-per-title", type=int, default=None, help="Maximum jobs to process per job title.")
    parser.add_argument("--debug-html-dir", type=str, default="app/dice/_experimental_/debug", help="Directory to save search HTML snapshots.")
    parser.add_argument("--session-state", type=str, default="storage/dice_session_state.json", help="Path to Playwright storage state file.")
    parser.add_argument("--no-session-reuse", action="store_true", help="Disable reusing saved login session.")
    parser.add_argument("--logout-on-exit", action="store_true", help="Explicitly log out at the end of the run.")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode.")
    parser.add_argument("--no-recommended", action="store_true", help="Disable processing of recommended jobs.")
    parser.add_argument("--only-recommended", action="store_true", help="Only process recommended jobs and skip custom job titles.")
    args = parser.parse_args()

    main(
        max_jobs=args.max_jobs,
        max_jobs_per_title=args.max_jobs_per_title,
        debug_html_dir=args.debug_html_dir,
        session_state_path=args.session_state,
        reuse_session=not args.no_session_reuse,
        logout_on_exit=args.logout_on_exit,
        headless=args.headless,
        process_recommended=not args.no_recommended,
        only_recommended=args.only_recommended,
    )
