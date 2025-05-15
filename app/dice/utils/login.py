"""
Handles login functionality for Dice automation.
"""
from playwright.sync_api import Page
import time
from typing import Any

def login(page: Page, email: str, password: str) -> None:
    """
    Logs into Dice using the provided credentials.
    Args:
        page (Page): Playwright page instance.
        email (str): User email.
        password (str): User password.
    """
    page.goto("https://www.dice.com/dashboard/login")
    page.wait_for_load_state("load")
    time.sleep(3)
    page.fill('input[name="email"]', email)
    page.wait_for_load_state("load")
    time.sleep(3)
    page.click('button[data-testid="sign-in-button"]')
    page.wait_for_load_state("load")
    time.sleep(3)
    page.fill('input[name="password"]', password)
    page.press('input[name="password"]', "Enter")
    page.wait_for_load_state("load")
    time.sleep(3)
