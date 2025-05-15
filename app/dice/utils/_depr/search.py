"""
Handles job search and filter application for Dice automation.
"""
from playwright.sync_api import Page
import time
from _data_.Filters.diceFilterSettings import dice_job_filter, JobFilter
from typing import Any

# todo: Move selectors to a shared constants module if reused
selectors = {

    "location_input": "input[name='location']",

    "submit_search_button": "button[data-testid='job-search-search-bar-search-button']",
  
    # Robust selector for 'All filters' sidebar button (2025-05-15)
    # Uses visible text, not dynamic id, for reliability
    "all_filters_sidebar_button": "button:has-text('All filters')",

    "third_party_button": '//button[@aria-label="Filter Search Results by Third Party"]',
    "easy_apply_filter": '//button[@aria-label="Filter Search Results by Easy Apply"]',
    "remote_filter_group": '//button[@aria-label="Filter Search Results by Remote"]',
    "work_settings_on_site": '//button[@aria-label="Filter Search Results by On-Site"]',
    "work_settings_hybrid": '//button[@aria-label="Filter Search Results by Hybrid"]',
    "posted_date_any_date": '//button[@role="radio" and text()=" Any Date "]',
    "posted_date_today": '//button[@role="radio" and text()=" Today "]',
    "posted_date_last_3_days": '//button[@role="radio" and text()=" Last 3 Days "]',
    "posted_date_last_7_days": '//button[@role="radio" and text()=" Last 7 Days "]',
    "employment_type_full_time": '//button[@aria-label="Filter Search Results by Full-time"]',
    "employment_type_contract": '//button[@aria-label="Filter Search Results by Contract"]',
    "work_authorization_willing_to_sponsor": '//button[@aria-label="Filter Search Results by Work Authorization"]',
    "employer_type_direct_hire": '//button[@aria-label="Filter Search Results by Direct Hire"]',
    "employer_type_recruiter": '//button[@aria-label="Filter Search Results by Recruiter"]',
    "easy_apply_clicked": '//button[@aria-label="Filter Search Results by Easy Apply" and @aria-checked="true"]'
}

def perform_job_search(page: Page, search_keywords: str, first_run: bool) -> None:
    """
    Performs a job search and applies filters according to JobFilter settings.
    Args:
        page (Page): Playwright page instance.
        search_keywords (str): Keywords for job search.
        first_run (bool): Whether this is the first search (to apply filters).
    """
    def click_filter(selector: str) -> None:
        try:
            page.wait_for_selector(selector, timeout=5000)
            page.click(selector)
            page.wait_for_load_state("load")
            time.sleep(2)
        except Exception as e:
            print(f"Failed to apply filter with selector {selector}: {e}")

    # * Open filters sidebar before applying filters (required for new Dice UI)
    try:
        page.wait_for_selector(selectors["all_filters_sidebar_button"], timeout=5000)
        page.click(selectors["all_filters_sidebar_button"])
        page.wait_for_load_state("load")
        time.sleep(1)
        print("Opened All Filters sidebar.")
    except Exception as e:
        print(f"Could not open All Filters sidebar: {e}")

    page.goto("https://www.dice.com/jobs")
    page.wait_for_load_state("load")
    time.sleep(3)
    page.fill(selectors["search_input"], search_keywords)
    page.click(selectors["submit_search_button"])
    page.wait_for_load_state("load")
    time.sleep(3)

    if first_run:
        match dice_job_filter.work_setting:
            case JobFilter.WorkSetting.REMOTE:
                click_filter(selectors["remote_filter_group"])
            case JobFilter.WorkSetting.ONSITE:
                click_filter(selectors["work_settings_on_site"])
            case JobFilter.WorkSetting.HYBRID:
                click_filter(selectors["work_settings_hybrid"])

        match dice_job_filter.posted_date:
            case "Any Date":
                click_filter(selectors["posted_date_any_date"])
            case "Today":
                click_filter(selectors["posted_date_today"])
            case "Last 3 Days":
                click_filter(selectors["posted_date_last_3_days"])
            case "Last 7 Days":
                click_filter(selectors["posted_date_last_7_days"])

        for employment_type in dice_job_filter.employment_types:
            match employment_type:
                case JobFilter.EmploymentType.FULL_TIME:
                    click_filter(selectors["employment_type_full_time"])
                case JobFilter.EmploymentType.CONTRACT:
                    click_filter(selectors["employment_type_contract"])
                case JobFilter.EmploymentType.THIRD_PARTY:
                    click_filter(selectors["third_party_button"])

        for employer_type in dice_job_filter.employer_types:
            match employer_type:
                case JobFilter.EmployerType.DIRECT_HIRE:
                    click_filter(selectors["employer_type_direct_hire"])
                case JobFilter.EmployerType.RECRUITER:
                    click_filter(selectors["employer_type_recruiter"])

        if dice_job_filter.willing_to_sponsor:
            click_filter(selectors["work_authorization_willing_to_sponsor"])
        if dice_job_filter.easy_apply:
            click_filter(selectors["easy_apply_filter"])
        print("Filters applied successfully based on JobFilter settings.")
    else:
        print("Filters have already been applied, proceeding with search.")
