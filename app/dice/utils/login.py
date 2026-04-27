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
    LOGIN_URL = "https://www.dice.com/dashboard/login"
    print(f"[LOGIN] Navigating to {LOGIN_URL}", flush=True)
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    # Accept possible cookie banner to avoid overlay issues
    try:
        cookie_btn = page.query_selector('button:has-text("Accept")')
        if cookie_btn:
            cookie_btn.click()
            time.sleep(0.5)
    except Exception:
        pass

    # Check if already logged in by looking at the URL
    if "login" not in page.url.lower():
        print(f"[LOGIN] Redirected to {page.url}. Assuming already logged in.", flush=True)
        return

    # Step 1: Email
    email_selectors = [
        'input[name="email"]',
        'input[type="email"]',
        'input#email'
    ]
    email_sel_found = None
    for sel in email_selectors:
        try:
            if page.wait_for_selector(sel, timeout=10000):
                email_sel_found = sel
                break
        except Exception:
            continue
    if not email_sel_found:
        if "login" not in page.url.lower():
            print(f"[LOGIN] Redirected to {page.url} while waiting. Assuming already logged in.", flush=True)
            return
        raise RuntimeError(f"[LOGIN] Could not locate email input field. Current URL: {page.url}")
    page.fill(email_sel_found, email)
    print("[LOGIN] Filled email", flush=True)

    # Click continue/sign-in (first step)
    first_step_buttons = [
        'button[data-testid="sign-in-button"]',
        'button:has-text("Continue")',
        'button:has-text("Sign in")',
        'button[type="submit"]'
    ]
    clicked = False
    for sel in first_step_buttons:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_enabled():
                btn.click()
                clicked = True
                break
        except Exception:
            continue
    if not clicked:
        # Some flows show password without a first click
        print("[LOGIN] No first-step button found; continuing to password.", flush=True)
    try:
        page.wait_for_load_state("domcontentloaded", timeout=10000)
    except Exception:
        pass

    # Step 2: Password
    password_selectors = [
        'input[name="password"]',
        'input[type="password"]',
        'input#password'
    ]
    pwd_sel_found = None
    for sel in password_selectors:
        try:
            if page.wait_for_selector(sel, timeout=20000):
                pwd_sel_found = sel
                break
        except Exception:
            continue
    if not pwd_sel_found:
        # Some flows open a new page/modal for password; try a brief delay and re-check once
        time.sleep(2)
        for sel in password_selectors:
            try:
                if page.wait_for_selector(sel, timeout=8000):
                    pwd_sel_found = sel
                    break
            except Exception:
                continue
    if not pwd_sel_found:
        raise RuntimeError("[LOGIN] Could not locate password input field after email step.")
    page.fill(pwd_sel_found, password)
    print("[LOGIN] Filled password", flush=True)

    # Final submit
    submit_buttons = [
        'button:has-text("Sign in")',
        'button[type="submit"]',
        'button[data-testid="sign-in-button"]'
    ]
    submitted = False
    for sel in submit_buttons:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_enabled():
                btn.click()
                submitted = True
                break
        except Exception:
            continue
    if not submitted:
        # Fallback: press Enter in password field
        page.press(pwd_sel_found, "Enter")

    # Post-login wait/verification
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    time.sleep(1.5)
    print(f"[LOGIN] Current URL after login attempt: {page.url}", flush=True)
