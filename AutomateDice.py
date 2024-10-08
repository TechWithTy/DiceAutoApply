# Import the JobFilter class
from _data_.Filters.diceFilterSettings import dice_job_filter, JobFilter
from _data_.Profiles.main_profile import UserProfile, user_profile, display_profile
import time

from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


first_run = True

next_in_application_button = 'button.seds-button-primary.btn-next'
search_keyword = "Machine learning engineer"


def login(page, email, password):
    page.goto("https://www.dice.com/dashboard/login")
    page.wait_for_load_state("load")
    time.sleep(3)

    # Fill the email input field
    page.fill('input[name="email"]', email)
    page.wait_for_load_state("load")
    time.sleep(3)

    # Click the "Sign In" button
    page.click('button[data-testid="sign-in-button"]')
    page.wait_for_load_state("load")
    time.sleep(3)

    # Fill the password input field using the name attribute
    page.fill('input[name="password"]', password)
    page.press('input[name="password"]', "Enter")
    page.wait_for_load_state("load")
    time.sleep(3)


def perform_job_search(page, search_keywords):
    global first_run  # Ensure we're referencing the global variable

    selectors = {
        "search_input": "#typeaheadInput",
        "submit_search_button": "#submitSearch-button",
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

    # Helper function to click a filter based on a selector
    def click_filter(selector):
        try:
            page.wait_for_selector(selector, timeout=5000)
            page.click(selector)
            page.wait_for_load_state("load")
            time.sleep(2)  # Allow time for the filter to apply
        except Exception as e:
            print(f"Failed to apply filter with selector {selector}: {e}")

    # Start by navigating to the job search page
    page.goto("https://www.dice.com/jobs")
    page.wait_for_load_state("load")
    time.sleep(3)

    # Fill in the search keywords and perform search
    page.fill(selectors["search_input"], search_keywords)
    page.click(selectors["submit_search_button"])
    page.wait_for_load_state("load")
    time.sleep(3)

    # Apply filters based on JobFilter settings
    if first_run:
        # Work setting filter
        if dice_job_filter.work_setting == JobFilter.WorkSetting.REMOTE:
            click_filter(selectors["remote_filter_group"])
        elif dice_job_filter.work_setting == JobFilter.WorkSetting.ONSITE:
            click_filter(selectors["work_settings_on_site"])
        elif dice_job_filter.work_setting == JobFilter.WorkSetting.HYBRID:
            click_filter(selectors["work_settings_hybrid"])

        # Posted date filter
        if dice_job_filter.posted_date == "Any Date":
            click_filter(selectors["posted_date_any_date"])
        elif dice_job_filter.posted_date == "Today":
            click_filter(selectors["posted_date_today"])
        elif dice_job_filter.posted_date == "Last 3 Days":
            click_filter(selectors["posted_date_last_3_days"])
        elif dice_job_filter.posted_date == "Last 7 Days":
            click_filter(selectors["posted_date_last_7_days"])

        # Employment types filter
        for employment_type in dice_job_filter.employment_types:  # Access the instance attribute
            if employment_type == JobFilter.EmploymentType.FULL_TIME:
                click_filter(selectors["employment_type_full_time"])
            elif employment_type == JobFilter.EmploymentType.CONTRACT:
                click_filter(selectors["employment_type_contract"])
            elif employment_type == JobFilter.EmploymentType.THIRD_PARTY:
                click_filter(selectors["third_party_button"])

        # Employer types filter
        for employer_type in dice_job_filter.employer_types:  # Access the instance attribute
            if employer_type == JobFilter.EmployerType.DIRECT_HIRE:
                click_filter(selectors["employer_type_direct_hire"])
            elif employer_type == JobFilter.EmployerType.RECRUITER:
                click_filter(selectors["employer_type_recruiter"])

        # Work authorization filter
        if dice_job_filter.willing_to_sponsor:
            click_filter(selectors["work_authorization_willing_to_sponsor"])

        # Easy apply filter
        if dice_job_filter.easy_apply:
            click_filter(selectors["easy_apply_filter"])

        print("Filters applied successfully based on JobFilter settings.")
    else:
        print("Filters have already been applied, proceeding with search.")


def extract_job_ids(page, job_ids):

    selectors = {
        "card_title": 'a.card-title-link',
        "list_pagination_next": 'li.pagination-next.page-item.ng-star-inserted',

    }
    while True:
        page.wait_for_load_state("load")
        time.sleep(5)

        try:
                # Try to wait for the job card titles to appear
                page.wait_for_selector(selectors["card_title"], timeout=30000)
                job_links = page.query_selector_all(selectors["card_title"])

                if not job_links:
                    print("No job results found.")
                    break

                for job_link in job_links:
                    job_ids.append(job_link.get_attribute('id'))

        except PlaywrightTimeoutError:
                print("Timeout exceeded while waiting for job results. No job results found.")
                break

        page.wait_for_load_state("load")

        page.wait_for_selector(selectors["list_pagination_next"])
        next_button = page.query_selector(selectors["list_pagination_next"])

        if next_button:
            page.wait_for_load_state("load")
            is_disabled = next_button.evaluate(
                '(element) => element.classList.contains("disabled")')
            if not is_disabled:
                next_button.click()
            else:
                break
        else:
            break


def write_job_titles_to_file(page, job_ids, url):
    print("number of All job IDs:" + str(len(job_ids)))

    selectors = {
        "apply_button": 'apply-button-wc',
    }

    with open('output/job_titles.txt', 'w') as file:
        val = 0

        parts = url.split('?')

        for job_id in job_ids:
            job_id = "https://www.dice.com/job-detail/" + \
                job_id + "?" + parts[1]
            try:
                new_page = page.context.new_page()
                new_page.goto(job_id)
                new_page.wait_for_load_state("load")
                time.sleep(3)

                job_title = new_page.evaluate("document.title")
                file.write(job_title + '\n')

                new_page.wait_for_selector(selectors["apply_button"])

                val += 1
                evaluate_and_apply(new_page, val)

            except Exception as e:
                print("Error processing job id:", job_id)
                print("Error details:", str(e))
                continue


def evaluate_and_apply(page, val):
    # JavaScript code to interact with the DOM

    selectors = {
        "submit_button": '//button/span[text()="Submit"]/..',
        "application_submitted": 'h1:has-text("Application submitted. We\'re rooting for you.")',
        "profile_visible_application_submitted":   'div.banner-message.sc-dhi-candidates-modal-2:has-text("Your Application is on its way.")'
    }

    js_script = """
        (function() {
            const applyButtonWc = document.querySelector('apply-button-wc');
            let value = 0;  // Default value

            if (applyButtonWc) {
                const shadowRoot = applyButtonWc.shadowRoot;
                const easyApplyButton = shadowRoot.querySelector('button.btn.btn-primary');

                if (easyApplyButton) {
                    easyApplyButton.click();
                    return 1;  // Proceed to next steps
                }
            }
            return 0;  // Easy Apply button not found
        })();
    """

    # Execute the JavaScript and get the returned value
    returned_value = page.evaluate(js_script)

    if returned_value == 1:
        page.wait_for_load_state("load")

        try:
            # Wait for the URL to contain the expected path
            # Timeout after 30 seconds
            time.sleep(3)

            # Retry logic for waiting for the URL
            max_attempts = 3
            attempt = 0

            # Define the expected URL pattern
            expected_url_pattern = "https://www.dice.com/**/{apply,job-detail}**"

            # Get the current page URL
            current_url = page.url

            # Check if we are already on the correct URL
            if "apply" in current_url or "job-detail" in current_url:
                print(f"Already on the correct URL: {current_url}")
                # Wait for the "Next" button and click it
                next_button = page.wait_for_selector(
                    next_in_application_button, timeout=10000)
                next_button.click()

                # Wait for the "Submit" button and click it
                submit_button = page.wait_for_selector(
                    selectors["submit_button"], timeout=10000)
                submit_button.click()
                return

            while attempt < max_attempts:
                try:
                    # Wait for the URL to contain the expected path
                    page.wait_for_url(expected_url_pattern, timeout=10000)
                    print(f"Successfully navigated to URL: {page.url}")
                    break  # Break out of the loop if successful
                except PlaywrightTimeoutError:
                    attempt += 1
                    current_url = page.url
                    print(f"Attempt {attempt} failed. Expected: {
                          expected_url_pattern}, but got: {current_url}")
                    time.sleep(3)  # Sleep before retrying

            if attempt == max_attempts:
                raise Exception(f"Failed to navigate to the expected URL after {
                                max_attempts} attempts. Last URL: {current_url}")

            # Wait for the "Next" button and click it
            next_button = page.wait_for_selector(
                next_in_application_button, timeout=10000)
            next_button.click()

            # Wait for the "Submit" button and click it
            submit_button = page.wait_for_selector(
                selectors["submit_button"], timeout=10000)
            submit_button.click()
            #?Temp
            last_page = page.context.pages[-1]
            last_page.close()
            # Wait for the "Application Submitted" confirmation by text content
            if page.is_visible(selectors["application_submitted"]):
                header_text = page.locator(
                    selectors["application_submitted"]).text_content()
                # Close the current tab
                last_page = page.context.pages[-1]
                last_page.close()
            elif page.is_visible(selectors["profile_visible_application_submitted"]):
                header_text = page.locator(
                    selectors["profile_visible_application_submitted"]).text_content()
                # Close the current tab
                last_page = page.context.pages[-1]
                last_page.close()
            #! if header_text:
            #!     returned_value = 0  # Successful application submission
            #! else:
            #!     returned_value  = 1  # Unsuccessful application submission
        except PlaywrightTimeoutError as e:
            print(f"Timeout during the application process: {e}")
            val = 1
        except Exception as e:
            print(f"Error during the application process: {e}")
            val = 1
    else:
        # Close the last opened tab if the easy apply button was not found
        last_page = page.context.pages[-1]
        last_page.close()
    # Call the apply_and_upload_resume function if the application wasn't submitted
    # if returned_value == 1 and val == 1:
    #     apply_and_upload_resume(page, val)


def apply_and_upload_resume(page, val):
    selectors = {
        "upload_button": 'button[data-v-746be088]',
        "input_file": 'input[type="file"]',
        "span_upload_button": 'span[data-e2e="upload"]',
        "unk_primary_button": next_in_application_button,
        "submit_button": '//button/span[text()="Submit"]/..',

    }
    page.wait_for_load_state("load")
    time.sleep(3)
    page.wait_for_selector(next_in_application_button)
    next_button = page.query_selector(next_in_application_button)

    if next_button:
        next_button.click()
        page.wait_for_load_state("load")
        time.sleep(3)
        resume_upload_error = "A resume is required to proceed"
        page_content = page.evaluate("document.body.textContent")

        if resume_upload_error in page_content:
            print("A resume is required to proceed.")
            print("Resume is missing. Uploading resume...")

            page.wait_for_load_state("load")
            time.sleep(3)
            page.wait_for_selector(selectors["upload_button"])
            upload_button = page.query_selector(selectors["upload_button"])

            if upload_button:
                upload_button.click()
                file_path = 'PATH_TO_RESUME'

                page.wait_for_load_state("load")
                time.sleep(3)
                page.wait_for_selector(selectors["input_file"])
                input_file = page.query_selector(selectors["input_file"])

                if input_file:
                    input_file.set_input_files(file_path)
                    page.wait_for_load_state("load")
                    time.sleep(3)
                    page.wait_for_selector(selectors["span_upload_button"])
                    upload_button = page.query_selector(
                        selectors["span_upload_button"])

                    if upload_button:
                        upload_button.click()
                        page.wait_for_load_state("load")
                        time.sleep(3)
                        page.wait_for_selector(
                            next_in_application_button)
                        next_button = page.query_selector(
                            next_in_application_button)

                        if next_button:
                            next_button.click()
                            page.wait_for_load_state("load")
                            time.sleep(3)
                            page.wait_for_selector(
                                selectors["span_upload_button"])
                            apply_button = page.query_selector(
                                selectors["span_upload_button"])

                            if apply_button:
                                apply_button.click()
                                print(val)
                                time.sleep(3)
                        else:
                            print("Next button not found.")
                    else:
                        print("File input element not found.")
                else:
                    print("Upload button not found.")
            else:
                print("Upload button not found.")
        else:
            submit_clicked = False

            page.wait_for_load_state("load")
            time.sleep(3)
            page.wait_for_selector(selectors["unk_primary_button"])
            button = page.query_selector(
                selectors["unk_primary_button"])
            page.wait_for_selector(selectors["submit_button"])
            submit_button = page.query_selector(selectors["submit_button"])

            submit_button.click()
            submit_clicked = True

            if submit_clicked:
                # Wait 1 second after clicking the submit button
                time.sleep(1)
                # Close the last tab opened
                last_page = page.context.pages[-1]
                last_page.close()
    else:
        print("Next button not found.")


def close_extra_tabs(context):
    # Get the list of all pages (tabs) in the context
    pages = context.pages

    # Keep the first page open, close all others
    for i in range(1, len(pages)):
        pages[i].close()


def logout_and_close(page, browser):

    selectors = {
        "nav_header": 'dhi-seds-nav-header-display',


    }
    page.wait_for_load_state("load")
    time.sleep(3)
    page.wait_for_selector(selectors["nav_header"])

    js_code = """
        const headerDisplay = document.querySelector('dhi-seds-nav-header-display');

        if (headerDisplay) {
            const shadowRoot = headerDisplay.shadowRoot;
            const dropdownButton = shadowRoot.querySelector('button.dropdown-button');

            if (dropdownButton) {
                dropdownButton.click();

                const logoutLink = shadowRoot.querySelector('a[href="https://www.dice.com/dashboard/logout"]');
                if (logoutLink) {
                    logoutLink.click();
                }
            }
        }
    """
    if input("Do you want to logout & close? (y/n): ") == 'y':
        page.evaluate(js_code)
        page.wait_for_load_state("load")
        time.sleep(3)
        print("logged out")
        page.context.clear_cookies()
        page.close()
        browser.close()
    else:
        print("click y to logout & close once done")
        if input("Do you want to logout & close? (y/n): ") == 'y':
            page.evaluate(js_code)
            page.wait_for_load_state("load")
            time.sleep(3)
            print("logged out")
            page.context.clear_cookies()
            page.close()
            browser.close()
        else:
            print("once done, log out & close manually")


# ?When moving to next job filters arent being applied
def main():
    global first_run  # Declare first_run as global to use the global variable

    print("started")
    display_profile(user_profile)

    # Load environment variables
    secret_email = os.getenv('EMAIL')
    secret_password = os.getenv('PASSWORD')
    custom_user_agent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.288 Mobile Safari/537.36"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=custom_user_agent)
        context.clear_cookies()

        page = context.new_page()
        login(page, secret_email, secret_password)

        # Loop over each job title in the user profile
        for job_title in user_profile.job_titles:
            # Extract the job title's name or any relevant attribute to use as a search keyword
            search_keyword = job_title.title
            print('Processing job title:', search_keyword)

            perform_job_search(page, search_keyword)  # Call the function

            if not first_run:
                # Close all tabs except the first one after the first run
                close_extra_tabs(context)
            else:
                first_run = False  # Set flag to False after the first iteration

            job_ids = []
            url = page.url

            extract_job_ids(page, job_ids)
            write_job_titles_to_file(page, job_ids, url)

        logout_and_close(page, browser)


if __name__ == "__main__":
    main()
