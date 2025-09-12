"""
Utility functions for Dice automation.
"""
from playwright.sync_api import Browser, Page
import time
from typing import Any

def close_extra_tabs(context: Any) -> None:
    pages = context.pages
    for i in range(1, len(pages)):
        pages[i].close()

def logout_and_close(page: Page, browser: Browser) -> None:
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
                const logoutLink = shadowRoot.querySelector('a[href=\"https://www.dice.com/dashboard/logout\"]');
                if (logoutLink) {
                    logoutLink.click();
                }
            }
        }
    """
    #! Interactive prompt removed for automation
    page.evaluate(js_code)
    page.wait_for_load_state("load")
    time.sleep(3)
    print("logged out")
    page.context.clear_cookies()
    page.close()
    browser.close()
