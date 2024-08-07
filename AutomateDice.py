from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

next_in_application_button = 'button.seds-button-primary.btn-next'


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

    page.wait_for_url("https://www.dice.com/home/home-feed")
    page.goto("https://www.dice.com/jobs")
    page.wait_for_load_state("load")
    time.sleep(3)

    page.fill("#typeaheadInput", search_keywords)
    page.wait_for_load_state("load")
    time.sleep(5)

    page.click("#submitSearch-button")
    page.wait_for_load_state("load")
    time.sleep(3)

    # page.wait_for_selector(
    #     '//button[@aria-label="Filter Search Results by Third Party"]')
    # page.click('//button[@aria-label="Filter Search Results by Third Party"]')
    # page.wait_for_load_state("load")
    # time.sleep(3)
    page.wait_for_selector(selectors["easy_apply_filter"])
    page.click(selectors["easy_apply_filter"])
    page.wait_for_load_state("load")
    time.sleep(3)

    page.wait_for_selector(selectors["remote_filter_group"])
    remote_only_button = page.locator(selectors["remote_filter_group"])
    remote_only_button.click()
    page.wait_for_load_state("load")
    time.sleep(3)


def extract_job_ids(page, job_ids):

    selectors = {
        "card_title": 'a.card-title-link',
        "list_pagination_next": 'li.pagination-next.page-item.ng-star-inserted',

    }
    while True:
        page.wait_for_load_state("load")
        time.sleep(5)

        page.wait_for_selector(selectors["card_title"])
        job_links = page.query_selector_all(selectors["card_title"])

        if not job_links:
            break

        for job_link in job_links:
            job_ids.append(job_link.get_attribute('id'))

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

    with open('job_titles.txt', 'w') as file:
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
                        print(f"Attempt {attempt} failed. Expected: {expected_url_pattern}, but got: {current_url}")
                        time.sleep(3)  # Sleep before retrying

            if attempt == max_attempts:
                    raise Exception(f"Failed to navigate to the expected URL after {max_attempts} attempts. Last URL: {current_url}")

            # Wait for the "Next" button and click it
            next_button = page.wait_for_selector(
                next_in_application_button, timeout=10000)
            next_button.click()

            # Wait for the "Submit" button and click it
            submit_button = page.wait_for_selector(
                selectors["submit_button"], timeout=10000)
            submit_button.click()

            # Wait for the "Application Submitted" confirmation by text content
            page.wait_for_selector(
                'h1:has-text("Application submitted. We\'re rooting for you.")', timeout=10000)

            # Check if the application submission was successful
            header_text = page.locator(
                'h1:has-text("Application submitted. We\'re rooting for you.")').text_content()

            if header_text:
                val = 0  # Successful application submission
            else:
                val = 1  # Unsuccessful application submission
        except PlaywrightTimeoutError as e:
            print(f"Timeout during the application process: {e}")
            val = 1
        except Exception as e:
            print(f"Error during the application process: {e}")
            val = 1

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
            page.wait_for_load_state("load")
            time.sleep(3)
            page.wait_for_selector(selectors["unk_primary_button"])
            button = page.query_selector(
                selectors["unk_primary_button"])
            page.wait_for_selector(selectors["submit_button"])
            submit_button = page.query_selector(selectors["submit_button"])

            submit_button.click()
            if button.text_content() == "Apply":
                button.click()
                print(val)
                page.close()
    else:
        print("Next button not found.")


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


def main():
    print("started")

    # Load environment variables
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')
    search_keywords = os.getenv('SEARCH_KEYWORDS')

    custom_user_agent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.288 Mobile Safari/537.36"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=custom_user_agent)
        context.clear_cookies()

        page = context.new_page()
        login(page, email, password)
        perform_job_search(page, search_keywords)

        job_ids = []
        url = page.url

        extract_job_ids(page, job_ids)
        write_job_titles_to_file(page, job_ids, url)
        logout_and_close(page, browser)


if __name__ == "__main__":
    main()
