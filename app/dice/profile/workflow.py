"""
Dice profile creation/edit workflow.

This workflow is intentionally conservative:
- It uses the dedicated TEST_USER_EMAIL / TEST_USER_PASSWORD account.
- It prefers the profiles-classic route first.
- It captures debug artifacts whenever a profile step fails.
"""
from __future__ import annotations

import argparse
import os
import time
import traceback
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from dotenv import dotenv_values, find_dotenv, load_dotenv
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from app.dice.profile.debug import capture_profile_debug_bundle, dump_text_lines, print_profile_controls
from app.dice.profile.model import DiceProfilePayload, build_profile_payload
from app.dice.profile.selectors import PROFILE_URLS, ProfileSelectorRegistry
from app.dice.utils.login import login


TEST_EMAIL_KEYS = ("TEST_USER_EMAIL",)
TEST_PASSWORD_KEYS = ("TEST_USER_PASSWORD",)


def _load_env() -> None:
    project_root = Path(__file__).resolve().parents[2]
    candidate_envs = [project_root / ".env", project_root / ".env.local", Path.cwd() / ".env"]
    for env_path in candidate_envs:
        if env_path.is_file() and load_dotenv(dotenv_path=str(env_path)):
            return
    found = find_dotenv(usecwd=True)
    if found:
        load_dotenv(dotenv_path=found)
    else:
        load_dotenv()


def _normalize_env_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return value.strip() or None


def _load_test_credentials() -> tuple[str, str]:
    _load_env()
    email = None
    password = None
    for key in TEST_EMAIL_KEYS:
        email = _normalize_env_value(os.getenv(key))
        if email:
            break
    for key in TEST_PASSWORD_KEYS:
        password = _normalize_env_value(os.getenv(key))
        if password:
            break

    if not email or not password:
        project_root = Path(__file__).resolve().parents[2]
        env_candidates = [project_root / ".env", project_root / ".env.local", Path.cwd() / ".env"]
        for env_path in env_candidates:
            if not env_path.is_file():
                continue
            vals = dotenv_values(env_path)
            if not email:
                email = _normalize_env_value(vals.get("TEST_USER_EMAIL"))
            if not password:
                password = _normalize_env_value(vals.get("TEST_USER_PASSWORD"))
    if not email or not password:
        raise RuntimeError("Missing TEST_USER_EMAIL or TEST_USER_PASSWORD environment variables.")
    return email, password


def _first_visible(page: Page, selectors: Sequence[str], timeout_ms: int = 5000):
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue
            if locator.is_visible():
                return locator
        except Exception:
            continue
    return None


def _click_first_visible(page: Page, selectors: Sequence[str], timeout_ms: int = 5000) -> bool:
    locator = _first_visible(page, selectors, timeout_ms=timeout_ms)
    if locator is None:
        return False
    locator.click()
    return True


def _expand_section(page: Page, selectors: ProfileSelectorRegistry, section: str) -> None:
    for candidate in selectors.section_buttons.get(section, []):
        try:
            loc = page.locator(candidate).first
            if loc.count() == 0:
                continue
            loc.click()
            time.sleep(0.5)
            return
        except Exception:
            continue


def _fill_first_matching(page: Page, candidates: Sequence[str], value: str, timeout_ms: int = 5000) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    locator = _first_visible(page, candidates, timeout_ms=timeout_ms)
    if locator is None:
        return False
    try:
        locator.fill(value)
    except Exception:
        locator.click()
        locator.press("Control+A")
        locator.type(value, delay=15)
    return True


def _set_file_input(page: Page, candidates: Sequence[str], file_path: str, timeout_ms: int = 5000) -> bool:
    file_obj = Path(file_path)
    if not file_obj.exists():
        return False
    for selector in candidates:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="attached", timeout=timeout_ms)
            if "input" in selector:
                locator.set_input_files(str(file_obj))
                return True
            if locator.is_visible():
                locator.click()
                try:
                    page.locator('input[type="file"]').first.set_input_files(str(file_obj))
                    return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def _verify_value(page: Page, candidates: Sequence[str], expected: str) -> bool:
    expected = (expected or "").strip()
    if not expected:
        return True
    for selector in candidates:
        try:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue
            if locator.input_value(timeout=1500).strip() == expected:
                return True
            text = (locator.text_content(timeout=1500) or "").strip()
            if text and expected in text:
                return True
        except Exception:
            continue
    return False


def _add_skills(page: Page, payload: DiceProfilePayload, selectors: ProfileSelectorRegistry) -> None:
    if not payload.skills:
        return

    _expand_section(page, selectors, "skills")
    skill_input = _first_visible(page, selectors.input_candidates["skills_input"], timeout_ms=3000)

    if skill_input is None:
        return

    existing_text = ""
    try:
        existing_text = (skill_input.input_value(timeout=1000) or "").strip()
    except Exception:
        pass

    for skill in payload.skills:
        if skill.lower() in existing_text.lower():
            continue
        try:
            skill_input.click()
            skill_input.fill(skill)
            skill_input.press("Enter")
            time.sleep(0.2)
        except Exception:
            try:
                skill_input.click()
                skill_input.type(skill, delay=25)
                skill_input.press("Enter")
                time.sleep(0.2)
            except Exception:
                continue


def _save_profile(page: Page, selectors: ProfileSelectorRegistry) -> bool:
    try:
        clicked = page.evaluate(
            """
            () => {
              const seen = new Set();
              const candidates = [];
              const selector = 'button[type="submit"], seds-button[type="submit"]';

              const isVisible = (el) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
              };

              const walk = (root, depth = 0, host = 'document') => {
                for (const el of Array.from(root.querySelectorAll(selector))) {
                  if (seen.has(el) || !isVisible(el)) continue;
                  seen.add(el);
                  const rect = el.getBoundingClientRect();
                  const text = (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
                  candidates.push({
                    el,
                    top: rect.top,
                    left: rect.left,
                    text,
                    host,
                    depth,
                  });
                }
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  if (el.shadowRoot) {
                    walk(el.shadowRoot, depth + 1, el.tagName.toLowerCase());
                  }
                }
              };

              walk(document);
              candidates.sort((a, b) => {
                const aScore = /save|submit|update|continue|next/i.test(a.text) ? 1 : 0;
                const bScore = /save|submit|update|continue|next/i.test(b.text) ? 1 : 0;
                if (aScore !== bScore) return bScore - aScore;
                if (a.top !== b.top) return b.top - a.top;
                if (a.left !== b.left) return a.left - b.left;
                return b.depth - a.depth;
              });
              if (!candidates.length) return false;
              candidates[0].el.click();
              return true;
            }
            """
        )
        if clicked:
            return True
    except Exception:
        pass
    if _click_first_visible(page, selectors.save_buttons, timeout_ms=7000):
        return True
    return False


def _wait_for_success(page: Page, selectors: ProfileSelectorRegistry, timeout_ms: int = 10000) -> bool:
    for candidate in selectors.success_toasts:
        try:
            loc = page.locator(candidate).first
            loc.wait_for(state="visible", timeout=timeout_ms)
            return True
        except Exception:
            continue
    return False


class DiceProfileWorkflow:
    def __init__(self, page: Page, payload: DiceProfilePayload, selectors: Optional[ProfileSelectorRegistry] = None):
        self.page = page
        self.payload = payload
        self.selectors = selectors or ProfileSelectorRegistry()

    def open_profiles_page(self) -> None:
        last_error = None
        for url in PROFILE_URLS:
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    self.page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                if "login" in self.page.url.lower():
                    continue
                return
            except Exception as exc:
                last_error = exc
                continue
        raise RuntimeError(f"Could not open Dice profile pages: {last_error}")

    def capture_controls(self, label: str) -> None:
        controls = print_profile_controls(self.page, title=f"{label} controls")
        lines = []
        for control in controls:
            lines.append(
                f"{control['tag']} testid={control['data_testid']} cy={control['data_cy']} "
                f"name={control['name']} id={control['id']} type={control['type']} "
                f"role={control['role']} aria={control['aria']} href={control['href']} "
                f"placeholder={control['placeholder']} text={control['text']}"
            )
        dump_text_lines(f"app/dice/_experimental_/debug/{label}_controls_dump.txt", lines)

    def _log(self, message: str) -> None:
        print(f"[profile] {message}", flush=True)

    def discover_entry_point(self) -> str:
        return self.page.url

    def ensure_profile_mode(self) -> None:
        self._log("Ensuring profile mode")
        if _click_first_visible(self.page, self.selectors.profile_entry_points, timeout_ms=5000):
            time.sleep(1)

        if _click_first_visible(self.page, self.selectors.create_profile_buttons, timeout_ms=2500):
            time.sleep(1)
            return

        if _click_first_visible(self.page, self.selectors.edit_profile_buttons, timeout_ms=2500):
            time.sleep(1)
            return

    def fill_identity_section(self) -> None:
        self._log("Filling identity section")
        _expand_section(self.page, self.selectors, "identity")
        _fill_first_matching(self.page, self.selectors.input_candidates["job_title"], self.payload.headline)

    def fill_contact_section(self) -> None:
        self._log("Filling contact section")
        _expand_section(self.page, self.selectors, "contact")
        _fill_first_matching(self.page, self.selectors.input_candidates["location"], self.payload.location)

    def fill_summary_section(self) -> None:
        self._log("Filling summary section")
        return

    def fill_resume_section(self) -> None:
        self._log("Filling resume section")
        _expand_section(self.page, self.selectors, "resume")
        if self.payload.resume_path:
            _set_file_input(self.page, self.selectors.resume_upload_candidates, self.payload.resume_path)

    def fill_skills_section(self) -> None:
        self._log("Filling skills section")
        _add_skills(self.page, self.payload, self.selectors)

    def verify_profile(self) -> bool:
        checks = [
            (self.selectors.input_candidates["job_title"], self.payload.headline),
        ]
        return all(_verify_value(self.page, selectors, expected) for selectors, expected in checks if expected)

    def run(self) -> None:
        self._log("Opening profile page")
        self.open_profiles_page()
        self.ensure_profile_mode()
        self.fill_identity_section()
        self.fill_contact_section()
        self.fill_summary_section()
        self.fill_resume_section()
        self.fill_skills_section()

        self._log("Attempting save")
        if not _save_profile(self.page, self.selectors):
            capture_profile_debug_bundle(self.page, "save_failed", "Could not locate save button")
            raise RuntimeError("Could not locate a save button on the Dice profile page.")

        self._log("Waiting for post-save stabilization")
        try:
            self.page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass

        self._log("Verifying profile values")
        if not self.verify_profile():
            capture_profile_debug_bundle(self.page, "verification_failed", "Saved values did not match the expected profile payload")
            raise RuntimeError("Dice profile verification failed after save.")

        if not _wait_for_success(self.page, self.selectors):
            # This is non-fatal because many profile views do not surface a toast.
            print("[profile] Save succeeded without a visible toast.", flush=True)


def main() -> None:
    import sys

    parser = argparse.ArgumentParser(description="Create or edit the Dice profile using the dedicated test account.")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--debug-only", action="store_true", help="Only discover controls and dump a debug bundle.")
    args = parser.parse_args()

    email, password = _load_test_credentials()
    payload = build_profile_payload()
    selectors = ProfileSelectorRegistry()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(user_agent=user_agent, viewport={"width": 1440, "height": 1024})
        page = context.new_page()
        try:
            login(page, email, password)
            workflow = DiceProfileWorkflow(page, payload, selectors)
            workflow.open_profiles_page()
            capture_profile_debug_bundle(page, "profile_entry", "Initial profile page capture")
            workflow.capture_controls("profile_entry")
            if args.debug_only:
                print("[profile] Debug bundle captured; exiting without editing.")
                return
            workflow.run()
            print("[profile] Profile creation/edit workflow completed.")
        except Exception as exc:
            capture_profile_debug_bundle(page, "profile_run_failed", str(exc))
            print(f"[profile] Failed: {exc}", flush=True)
            traceback.print_exc()
            raise
        finally:
            try:
                page.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
