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
from dataclasses import replace
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from dotenv import dotenv_values, find_dotenv, load_dotenv
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from app.dice.profile.debug import capture_profile_debug_bundle, dump_text_lines, print_profile_controls
from app.dice.profile.model import DiceProfilePayload, EducationPayload, WorkExperiencePayload, build_profile_payload
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


def _click_any(page: Page, selectors: Sequence[str], timeout_ms: int = 3000) -> bool:
    return _click_first_visible(page, selectors, timeout_ms=timeout_ms)


def _dom_click_first_visible(page: Page, selectors: Sequence[str], timeout_ms: int = 3000) -> bool:
    locator = _first_visible(page, selectors, timeout_ms=timeout_ms)
    if locator is None:
        return False
    try:
        locator.evaluate("(el) => el.click()")
        return True
    except Exception:
        return False


def _dom_click_card_action(page: Page, heading: str, action_patterns: Sequence[str]) -> bool:
    return bool(page.evaluate(
        """
        ({ heading, actionPatterns }) => {
          const patterns = actionPatterns.map((pattern) => new RegExp(pattern, 'i'));
          const visible = (el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
          };
          const textOf = (el) => (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
          const cards = [];
          const walk = (root) => {
            for (const el of Array.from(root.querySelectorAll('*'))) {
              const text = textOf(el);
              if (text && text.toLowerCase().includes(heading.toLowerCase())) {
                let card = el;
                for (let i = 0; i < 8 && card; i += 1) {
                  const cardText = textOf(card);
                  const cardActions = card.querySelectorAll('button,seds-button,a,[role="button"]');
                  if (cardText.toLowerCase().includes(heading.toLowerCase()) && cardActions.length) {
                    const rect = card.getBoundingClientRect();
                    cards.push({el: card, area: rect.width * rect.height});
                    break;
                  }
                  card = card.parentElement;
                }
              }
              if (el.shadowRoot) walk(el.shadowRoot);
            }
          };
          walk(document);
          cards.sort((a, b) => a.area - b.area);
          for (const card of cards) {
            const actions = Array.from(card.el.querySelectorAll('button,seds-button,a,[role="button"]')).filter(visible);
            const match = actions.find((el) => patterns.some((pattern) => pattern.test(textOf(el))));
            const fallback = actions[actions.length - 1];
            const target = match || fallback;
            if (target) {
              target.click();
              return true;
            }
          }
          return false;
        }
        """,
        {"heading": heading, "actionPatterns": list(action_patterns)},
    ))


def _click_text_button(page: Page, patterns: Sequence[str], timeout_ms: int = 3000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        try:
            clicked = page.evaluate(
                """
                (patterns) => {
                  const regexes = patterns.map((pattern) => new RegExp(pattern, 'i'));
                  const visible = (el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                  };
                  const textOf = (el) => (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
                  const walk = (root) => {
                    const selectors = 'button,seds-button,label,[role="button"],[role="menuitem"]';
                    for (const el of Array.from(root.querySelectorAll(selectors))) {
                      if (!visible(el)) continue;
                      const text = textOf(el);
                      if (!text || !regexes.some((regex) => regex.test(text))) continue;
                      const internal = el.shadowRoot?.querySelector('button,[role="button"]');
                      (internal || el).click();
                      return true;
                    }
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (el.shadowRoot && walk(el.shadowRoot)) return true;
                    }
                    return false;
                  };
                  return walk(document);
                }
                """,
                list(patterns),
            )
            if clicked:
                return True
        except Exception:
            pass
        time.sleep(0.25)
    return False


def _scroll_to_text(page: Page, text: str) -> None:
    for _ in range(6):
        try:
            found = page.evaluate(
                """
                (needle) => {
                  const lowerNeedle = needle.toLowerCase();
                  const textOf = (el) => (el.innerText || el.textContent || '').trim();
                  const walk = (root) => {
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (textOf(el).toLowerCase().includes(lowerNeedle)) {
                        el.scrollIntoView({block: 'center', inline: 'nearest'});
                        return true;
                      }
                      if (el.shadowRoot && walk(el.shadowRoot)) return true;
                    }
                    return false;
                  };
                  return walk(document);
                }
                """,
                text,
            )
            if found:
                time.sleep(0.75)
                return
        except Exception:
            pass
        try:
            page.mouse.wheel(0, 900)
            time.sleep(0.5)
        except Exception:
            pass


def _scroll_profile_page(page: Page) -> None:
    for position in [0, 700, 1400, 2200, 3000]:
        try:
            page.evaluate("(y) => window.scrollTo(0, y)", position)
            time.sleep(0.2)
        except Exception:
            pass
        try:
            page.mouse.wheel(0, 700)
            time.sleep(0.2)
        except Exception:
            pass


def _fill_first_matching(page: Page, candidates: Sequence[str], value: str, timeout_ms: int = 5000) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    locator = _first_visible(page, candidates, timeout_ms=timeout_ms)
    if locator is None:
        return False
    try:
        locator.fill(value)
        return True
    except Exception:
        try:
            locator.evaluate(
                """
                (el, value) => {
                  el.value = value;
                  el.dispatchEvent(new Event('input', { bubbles: true }));
                  el.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                value,
            )
            return True
        except Exception:
            try:
                locator.click(timeout=timeout_ms)
                locator.press("Control+A", timeout=timeout_ms)
                locator.type(value, delay=15, timeout=timeout_ms)
                return True
            except Exception:
                return False


def _set_first_matching_dom(page: Page, candidates: Sequence[str], value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    for selector in candidates:
        try:
            changed = page.evaluate(
                """
                ({ selector, value }) => {
                  const isVisible = (el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                  };
                  const setValue = (el) => {
                    el.focus();
                    const descriptor = Object.getOwnPropertyDescriptor(el.constructor.prototype, 'value')
                      || Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
                      || Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');
                    if (descriptor && descriptor.set) {
                      descriptor.set.call(el, value);
                    } else {
                      el.value = value;
                    }
                    el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, composed: true, key: value[0] || ' ' }));
                    el.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, inputType: 'insertText', data: value }));
                    el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, composed: true, key: value[0] || ' ' }));
                    el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
                    el.blur();
                    return true;
                  };
                  const walk = (root) => {
                    for (const el of Array.from(root.querySelectorAll(selector))) {
                      if (isVisible(el)) return setValue(el);
                    }
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (el.shadowRoot) {
                        const result = walk(el.shadowRoot);
                        if (result) return result;
                      }
                    }
                    return false;
                  };
                  return walk(document);
                }
                """,
                {"selector": selector, "value": value},
            )
            if changed:
                return True
        except Exception:
            continue
    return False


def _set_first_matching_dom_any(page: Page, candidates: Sequence[str], value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    for selector in candidates:
        try:
            changed = page.evaluate(
                """
                ({ selector, value }) => {
                  const setValue = (el) => {
                    el.focus();
                    const descriptor = Object.getOwnPropertyDescriptor(el.constructor.prototype, 'value')
                      || Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
                      || Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');
                    if (descriptor && descriptor.set) {
                      descriptor.set.call(el, value);
                    } else {
                      el.value = value;
                    }
                    el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, composed: true, key: value[0] || ' ' }));
                    el.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, inputType: 'insertText', data: value }));
                    el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, composed: true, key: value[0] || ' ' }));
                    el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
                    el.blur();
                    return true;
                  };
                  const walk = (root) => {
                    for (const el of Array.from(root.querySelectorAll(selector))) {
                      return setValue(el);
                    }
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (el.shadowRoot) {
                        const result = walk(el.shadowRoot);
                        if (result) return result;
                      }
                    }
                    return false;
                  };
                  return walk(document);
                }
                """,
                {"selector": selector, "value": value},
            )
            if changed:
                return True
        except Exception:
            continue
    return False


def _set_first_matching_profile_dom(page: Page, candidates: Sequence[str], value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    for selector in candidates:
        try:
            changed = page.evaluate(
                """
                ({ selector, value }) => {
                  const isVisible = (el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                  };
                  const setValue = (el) => {
                    el.focus();
                    const descriptor = Object.getOwnPropertyDescriptor(el.constructor.prototype, 'value')
                      || Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
                      || Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');
                    if (descriptor && descriptor.set) {
                      descriptor.set.call(el, value);
                    } else {
                      el.value = value;
                    }
                    el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, composed: true, key: value[0] || ' ' }));
                    el.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, inputType: 'insertText', data: value }));
                    el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, composed: true, key: value[0] || ' ' }));
                    el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
                    el.blur();
                    return true;
                  };
                  const walk = (root, profileOnly) => {
                    for (const el of Array.from(root.querySelectorAll(selector))) {
                      const host = el.getRootNode().host;
                      const inProfile = host && host.tagName && host.tagName.toLowerCase() === 'dhi-candidates-wired-candidate-profile';
                      if (isVisible(el) && (!profileOnly || inProfile)) return setValue(el);
                    }
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (el.shadowRoot) {
                        const result = walk(el.shadowRoot, profileOnly);
                        if (result) return result;
                      }
                    }
                    return false;
                  };
                  return walk(document, true) || walk(document, false);
                }
                """,
                {"selector": selector, "value": value},
            )
            if changed:
                return True
        except Exception:
            continue
    return False


def _check_first_matching_dom_any(page: Page, candidates: Sequence[str], checked: bool = True) -> bool:
    for selector in candidates:
        try:
            changed = page.evaluate(
                """
                ({ selector, checked }) => {
                  const walk = (root) => {
                    for (const el of Array.from(root.querySelectorAll(selector))) {
                      el.checked = checked;
                      el.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
                      el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
                      return true;
                    }
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (el.shadowRoot) {
                        const result = walk(el.shadowRoot);
                        if (result) return result;
                      }
                    }
                    return false;
                  };
                  return walk(document);
                }
                """,
                {"selector": selector, "checked": checked},
            )
            if changed:
                return True
        except Exception:
            continue
    return False


def _select_first_matching_dom_any(page: Page, candidates: Sequence[str], value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    for selector in candidates:
        try:
            changed = page.evaluate(
                """
                ({ selector, value }) => {
                  const wanted = value.toLowerCase();
                  const walk = (root) => {
                    for (const select of Array.from(root.querySelectorAll(selector))) {
                      const options = Array.from(select.options || []);
                      const match = options.find((option) => (
                        (option.label || '').toLowerCase() === wanted ||
                        (option.textContent || '').trim().toLowerCase() === wanted ||
                        (option.value || '').toLowerCase() === wanted
                      )) || options.find((option) => (
                        (option.label || option.textContent || option.value || '').toLowerCase().includes(wanted)
                      ));
                      if (!match) continue;
                      select.value = match.value;
                      select.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
                      select.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
                      return true;
                    }
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (el.shadowRoot) {
                        const result = walk(el.shadowRoot);
                        if (result) return result;
                      }
                    }
                    return false;
                  };
                  return walk(document);
                }
                """,
                {"selector": selector, "value": value},
            )
            if changed:
                return True
        except Exception:
            continue
    return False


def _select_first_matching_profile_dom(page: Page, candidates: Sequence[str], value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    for selector in candidates:
        try:
            changed = page.evaluate(
                """
                ({ selector, value }) => {
                  const wanted = value.toLowerCase();
                  const isVisible = (el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                  };
                  const choose = (select) => {
                    const options = Array.from(select.options || []);
                    const match = options.find((option) => (
                      (option.label || '').toLowerCase() === wanted ||
                      (option.textContent || '').trim().toLowerCase() === wanted ||
                      (option.value || '').toLowerCase() === wanted
                    )) || options.find((option) => (
                      (option.label || option.textContent || option.value || '').toLowerCase().includes(wanted)
                    ));
                    if (!match) return false;
                    select.value = match.value;
                    select.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
                    select.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
                    return true;
                  };
                  const walk = (root, profileOnly) => {
                    for (const select of Array.from(root.querySelectorAll(selector))) {
                      const host = select.getRootNode().host;
                      const inProfile = host && host.tagName && host.tagName.toLowerCase() === 'dhi-candidates-wired-candidate-profile';
                      if (isVisible(select) && (!profileOnly || inProfile) && choose(select)) return true;
                    }
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (el.shadowRoot) {
                        const result = walk(el.shadowRoot, profileOnly);
                        if (result) return result;
                      }
                    }
                    return false;
                  };
                  return walk(document, true) || walk(document, false);
                }
                """,
                {"selector": selector, "value": value},
            )
            if changed:
                return True
        except Exception:
            continue
    return False


def _type_first_matching(page: Page, candidates: Sequence[str], value: str, timeout_ms: int = 3000) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    locator = _first_visible(page, candidates, timeout_ms=timeout_ms)
    if locator is None:
        return False
    try:
        locator.click(timeout=timeout_ms, force=True)
        locator.press("Control+A", timeout=timeout_ms)
        locator.press("Backspace", timeout=timeout_ms)
        locator.type(value, delay=25, timeout=timeout_ms * 2)
        locator.press("Tab", timeout=timeout_ms)
        return True
    except Exception:
        try:
            locator.evaluate("(el) => el.focus()")
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type(value, delay=25)
            page.keyboard.press("Tab")
            return True
        except Exception:
            return False


def _get_first_matching_value(page: Page, candidates: Sequence[str]) -> str:
    for selector in candidates:
        try:
            value = page.evaluate(
                """
                (selector) => {
                  const isVisible = (el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                  };
                  const walk = (root) => {
                    for (const el of Array.from(root.querySelectorAll(selector))) {
                      if (isVisible(el)) return el.value || el.textContent || '';
                    }
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (el.shadowRoot) {
                        const result = walk(el.shadowRoot);
                        if (result !== null && result !== undefined) return result;
                      }
                    }
                    return null;
                  };
                  return walk(document);
                }
                """,
                selector,
            )
            if value:
                return str(value).strip()
        except Exception:
            continue
    return ""


def _check_first_matching(page: Page, candidates: Sequence[str], checked: bool = True) -> bool:
    locator = _first_visible(page, candidates, timeout_ms=3000)
    if locator is None:
        return False
    try:
        locator.set_checked(checked)
        return True
    except Exception:
        try:
            if locator.is_checked() != checked:
                locator.evaluate("(el) => el.click()")
            return True
        except Exception:
            return False


def _select_first_matching(page: Page, candidates: Sequence[str], value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    locator = _first_visible(page, candidates, timeout_ms=3000)
    if locator is None:
        return False
    for option in [value, value[:3], value.lower(), value.upper()]:
        try:
            locator.select_option(label=option)
            return True
        except Exception:
            try:
                locator.select_option(value=option)
                return True
            except Exception:
                continue
    return False


def _select_first_matching_dom(page: Page, candidates: Sequence[str], value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    for selector in candidates:
        try:
            changed = page.evaluate(
                """
                ({ selector, value }) => {
                  const wanted = value.toLowerCase();
                  const isVisible = (el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                  };
                  const walk = (root) => {
                    for (const select of Array.from(root.querySelectorAll(selector))) {
                      if (!isVisible(select)) continue;
                      const options = Array.from(select.options || []);
                      const match = options.find((option) => (
                        (option.label || '').toLowerCase() === wanted ||
                        (option.textContent || '').trim().toLowerCase() === wanted ||
                        (option.value || '').toLowerCase() === wanted
                      )) || options.find((option) => (
                        (option.label || option.textContent || option.value || '').toLowerCase().includes(wanted)
                      ));
                      if (!match) continue;
                      select.value = match.value;
                      select.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
                      select.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
                      return true;
                    }
                    for (const el of Array.from(root.querySelectorAll('*'))) {
                      if (el.shadowRoot) {
                        const result = walk(el.shadowRoot);
                        if (result) return result;
                      }
                    }
                    return false;
                  };
                  return walk(document);
                }
                """,
                {"selector": selector, "value": value},
            )
            if changed:
                return True
        except Exception:
            continue
    return False


def _choose_autocomplete_option(page: Page, candidates: Sequence[str], value: str) -> None:
    locator = _first_visible(page, candidates, timeout_ms=1500)
    if locator is None:
        return
    try:
        locator.click(timeout=1000)
        locator.press("ArrowDown", timeout=1000)
        locator.press("Enter", timeout=1000)
        time.sleep(0.3)
    except Exception:
        try:
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            time.sleep(0.3)
        except Exception:
            pass
    current = _get_first_matching_value(page, candidates)
    if value and not current:
        _set_first_matching_dom(page, candidates, value)


def _fill_autocomplete_interactive(page: Page, candidates: Sequence[str], value: str, timeout_ms: int = 4000) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    locator = _first_visible(page, candidates, timeout_ms=timeout_ms)
    if locator is None:
        return False
    try:
        locator.click(timeout=timeout_ms, force=True)
        locator.press("Control+A", timeout=timeout_ms)
        locator.press("Backspace", timeout=timeout_ms)
        locator.type(value, delay=35, timeout=timeout_ms * 3)
        time.sleep(0.8)
        locator.press("ArrowDown", timeout=timeout_ms)
        locator.press("Enter", timeout=timeout_ms)
        locator.press("Tab", timeout=timeout_ms)
        return True
    except Exception:
        try:
            locator.fill(value, timeout=timeout_ms)
            time.sleep(0.8)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            page.keyboard.press("Tab")
            return True
        except Exception:
            return False


def _dismiss_open_modal(page: Page) -> None:
    for candidate in ['button:has-text("Cancel")', 'button[title="Close"]', 'button:has-text("Close")']:
        if _dom_click_first_visible(page, [candidate], timeout_ms=1000):
            time.sleep(0.5)
            return
    try:
        page.keyboard.press("Escape")
        time.sleep(0.5)
    except Exception:
        pass


def _profile_text_with_control_values(page: Page, timeout_ms: int = 3000) -> str:
    text_parts: list[str] = []
    try:
        text_parts.append(page.locator("body").inner_text(timeout=timeout_ms) or "")
    except Exception:
        pass
    try:
        control_values = page.evaluate(
            """
            () => {
              const values = [];
              const walk = (root) => {
                for (const el of Array.from(root.querySelectorAll('input,textarea,select'))) {
                  values.push(el.value || el.innerText || el.textContent || '');
                  values.push(el.name || el.id || el.getAttribute('aria-label') || '');
                }
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  values.push(el.innerText || el.textContent || '');
                  if (el.shadowRoot) walk(el.shadowRoot);
                }
              };
              walk(document);
              return values.join(' ');
            }
            """
        )
        text_parts.append(control_values or "")
    except Exception:
        pass
    return " ".join(text_parts).lower()


def _section_text_by_heading(page: Page, heading: str) -> str:
    try:
        return str(page.evaluate(
            """
            (heading) => {
              const target = heading.toLowerCase();
              const visible = (el) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
              };
              const textOf = (el) => (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
              const cards = [];
              const walk = (root) => {
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  const text = textOf(el);
                  if (visible(el) && text.toLowerCase().includes(target)) {
                    let card = el;
                    for (let i = 0; i < 10 && card; i += 1) {
                      const cardText = textOf(card);
                      if (
                        visible(card) &&
                        cardText.toLowerCase().includes(target) &&
                        /dhi-candidates-card|profile-section|candidate-profile/i.test(card.tagName + ' ' + card.className)
                      ) {
                        const rect = card.getBoundingClientRect();
                        cards.push({ text: cardText, area: rect.width * rect.height });
                        break;
                      }
                      card = card.parentElement || card.getRootNode().host || null;
                    }
                  }
                  if (el.shadowRoot) walk(el.shadowRoot);
                }
              };
              walk(document);
              cards.sort((a, b) => a.area - b.area);
              return cards.length ? cards[0].text : '';
            }
            """,
            heading,
        )).lower()
    except Exception:
        return ""


def _ideal_job_card_complete(page: Page, payload: DiceProfilePayload) -> bool:
    text = _section_text_by_heading(page, "Ideal Job")
    if not text:
        return False
    has_title = payload.headline.lower() in text
    has_employment = "full-time" in text or "full time" in text or "contract" in text
    has_remote = "remote" in text
    has_salary = payload.desired_salary in text or "120,000" in text or "$120" in text
    return has_title and has_employment and has_remote and has_salary


def _ideal_company_card_complete(page: Page, payload: DiceProfilePayload) -> bool:
    text = _section_text_by_heading(page, "Ideal Company").replace("\u2013", "-").replace("\u2014", "-")
    if "company employee size" not in text or "company age" not in text:
        text = _profile_text_with_control_values(page, timeout_ms=3000).replace("\u2013", "-").replace("\u2014", "-")
    if not text:
        return False
    size = payload.ideal_company_size.lower().replace("employees", "").strip()
    age = payload.ideal_company_age.lower().replace("years", "").strip()
    has_size = payload.ideal_company_size.lower() in text or (size and size in text)
    has_age = payload.ideal_company_age.lower() in text or (age and age in text) or "11-19" in text
    return has_size and has_age


def _profile_visibility_state(page: Page) -> Optional[bool]:
    try:
        result = page.evaluate(
            """
            () => {
              const textOf = (el) => (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim();
              const visible = (el) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
              };
              const closestText = (el) => {
                let node = el;
                const parts = [];
                for (let i = 0; i < 8 && node; i += 1) {
                  parts.push(textOf(node));
                  node = node.parentElement || node.getRootNode().host || null;
                }
                return parts.join(' ');
              };
              const walk = (root) => {
                for (const input of Array.from(root.querySelectorAll('input[type="checkbox"][role="switch"], input[role="switch"]'))) {
                  const context = closestText(input).toLowerCase();
                  const aria = (input.getAttribute('aria-label') || '').toLowerCase();
                  if (context.includes('profile visibility') || aria === 'on' || aria === 'off') {
                    if (aria === 'on') return true;
                    if (aria === 'off') return false;
                    return Boolean(input.checked);
                  }
                }
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  if (el.shadowRoot) {
                    const result = walk(el.shadowRoot);
                    if (result !== null) return result;
                  }
                }
                return null;
              };
              return walk(document);
            }
            """
        )
        return result if isinstance(result, bool) else None
    except Exception:
        return None


def _confirm_profile_visibility_prompt(page: Page, desired_visible: bool) -> None:
    if desired_visible:
        patterns = [
            r"yes,?\s*make my profile visible",
            r"make my profile visible",
            r"continue",
            r"save",
        ]
    else:
        patterns = [
            r"yes",
            r"hide",
            r"turn off",
            r"continue",
            r"save",
        ]
    for pattern in patterns:
        try:
            if _click_text_button(page, [pattern], timeout_ms=1500):
                time.sleep(1)
                return
        except Exception:
            continue


def _set_profile_visibility(page: Page, desired_visible: Optional[bool]) -> bool:
    if desired_visible is None:
        return True
    try:
        changed = page.evaluate(
            """
            (desiredVisible) => {
              const textOf = (el) => (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim();
              const visible = (el) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
              };
              const contextOf = (el) => {
                let node = el;
                const parts = [];
                for (let i = 0; i < 8 && node; i += 1) {
                  parts.push(textOf(node));
                  node = node.parentElement || node.getRootNode().host || null;
                }
                return parts.join(' ').toLowerCase();
              };
              const stateOf = (input) => {
                const aria = (input.getAttribute('aria-label') || '').toLowerCase();
                if (aria === 'on') return true;
                if (aria === 'off') return false;
                return Boolean(input.checked);
              };
              const clickTargetFor = (input) => {
                const root = input.getRootNode();
                const id = input.id;
                if (id) {
                  const label = root.querySelector(`label[for="${CSS.escape(id)}"]`) || document.querySelector(`label[for="${CSS.escape(id)}"]`);
                  if (label && visible(label)) return label;
                }
                return input;
              };
              const walk = (root) => {
                for (const input of Array.from(root.querySelectorAll('input[type="checkbox"][role="switch"], input[role="switch"]'))) {
                  const aria = (input.getAttribute('aria-label') || '').toLowerCase();
                  const context = contextOf(input);
                  if (!context.includes('profile visibility') && aria !== 'on' && aria !== 'off') continue;
                  const current = stateOf(input);
                  if (current === desiredVisible) return { found: true, changed: false, state: current };
                  clickTargetFor(input).click();
                  return { found: true, changed: true, state: desiredVisible };
                }
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  if (el.shadowRoot) {
                    const result = walk(el.shadowRoot);
                    if (result && result.found) return result;
                  }
                }
                return { found: false, changed: false, state: null };
              };
              return walk(document);
            }
            """,
            desired_visible,
        )
    except Exception:
        return False
    if not changed or not changed.get("found"):
        return False
    if changed.get("changed"):
        time.sleep(1)
        _confirm_profile_visibility_prompt(page, desired_visible)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        time.sleep(1)
    current = _profile_visibility_state(page)
    return current is desired_visible


def _completion_items_text(page: Page) -> str:
    try:
        return str(page.evaluate(
            """
            () => {
              const items = [];
              const walk = (root) => {
                for (const el of Array.from(root.querySelectorAll('li[role="button"],[role="button"]'))) {
                  const text = (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
                  if (/profile photo|first name|last name|location|resume|desired job title|skills|years experience|work authorization|employment type/i.test(text)) {
                    items.push(text);
                  }
                }
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  if (el.shadowRoot) walk(el.shadowRoot);
                }
              };
              walk(document);
              return items.join('\\n');
            }
            """
        )).lower()
    except Exception:
        return ""


def _completion_item_is_complete(page: Page, label: str) -> bool:
    checklist = _completion_items_text(page)
    pattern = f"+{label}".lower()
    return pattern not in checklist


def _completion_non_photo_complete(page: Page) -> bool:
    return all(
        _completion_item_is_complete(page, label)
        for label in [
            "Location",
            "Desired Job Title",
            "Years Experience",
            "Work Authorization",
            "Employment Type",
        ]
    )


def _completion_required_complete(page: Page) -> bool:
    return all(
        _completion_item_is_complete(page, label)
        for label in [
            "Profile Photo",
            "Location",
            "Desired Job Title",
            "Years Experience",
            "Work Authorization",
            "Employment Type",
        ]
    )


def _click_completion_item(page: Page, label: str) -> bool:
    try:
        return bool(page.evaluate(
            """
            (label) => {
              const wanted = label.toLowerCase();
              const promptMap = {
                'profile photo': [
                  'profile photo',
                  'change profile photo',
                ],
                'desired job title': [
                  'add desired job title',
                  'what do you want for your next job title',
                ],
                'years experience': [
                  'how many years of experience do you have',
                ],
                'location': [
                  'where are you currently located',
                  'location',
                ],
                'work authorization': [
                  'what is your work authorization status',
                  'work authorization',
                ],
                'employment type': [
                  'what is your preferred type of employment',
                  'employment type',
                ],
              };
              const prompts = promptMap[wanted] || [];
              const visible = (el) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
              };
              const textOf = (el) => (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
              const walk = (root, promptOnly = false) => {
                const selector = promptOnly ? 'button,[role="button"]' : 'li[role="button"],[role="button"],button';
                for (const el of Array.from(root.querySelectorAll(selector))) {
                  const text = textOf(el).toLowerCase();
                  const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                  const matchesPrompt = prompts.some((prompt) => text.includes(prompt) || aria.includes(prompt));
                  const matchesLabel = text.includes(wanted) || aria.includes(wanted);
                  if (visible(el) && (matchesPrompt || (!promptOnly && matchesLabel))) {
                    el.click();
                    return true;
                  }
                }
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  if (el.shadowRoot) {
                    const result = walk(el.shadowRoot, promptOnly);
                    if (result) return result;
                  }
                }
                return false;
              };
              return walk(document, true) || walk(document, false);
            }
            """,
            label,
        ))
    except Exception:
        return False


def _fill_completion_fields(page: Page, payload: DiceProfilePayload, target: str = "") -> None:
    target_key = target.lower()
    fill_all = not target_key

    if fill_all or "desired job title" in target_key:
        if not _fill_autocomplete_interactive(page, [
        'input[aria-label="Ideal Job"]',
        'input[placeholder="Preferred Job Title"]',
        'input[name="job_title"]',
        ], payload.headline):
            _set_first_matching_profile_dom(page, [
                'input[aria-label="Ideal Job"]',
                'input[placeholder="Preferred Job Title"]',
                'input[name="job_title"]',
            ], payload.headline)

    if fill_all or "years experience" in target_key:
        if not _set_first_matching_profile_dom(page, [
            'input[name="years_experience"]',
            'input[aria-label="Years Experience"]',
        ], str(payload.years_experience)):
            _fill_first_matching(page, [
                'input[name="years_experience"]',
                'input[aria-label="Years Experience"]',
            ], str(payload.years_experience), timeout_ms=3000)

    if fill_all or "location" in target_key:
        if not _fill_autocomplete_interactive(page, [
            'input[name="city_state"]',
            'input[aria-label*="City" i]',
        ], "Denver, CO"):
            _set_first_matching_profile_dom(page, [
                'input[name="city_state"]',
                'input[aria-label*="City" i]',
            ], "Denver, CO")
        if not _fill_autocomplete_interactive(page, [
            'input[name="location.country"]',
            'input[aria-label="Country"]',
        ], "United States"):
            _set_first_matching_profile_dom(page, [
                'input[name="location.country"]',
                'input[aria-label="Country"]',
            ], "United States")

    if fill_all or "work authorization" in target_key:
        if not _select_first_matching_profile_dom(page, [
            'select[name="work_authorization"]',
            'select[aria-label*="Work Authorization" i]',
        ], "US Citizen"):
            _select_first_matching(page, [
                'select[name="work_authorization"]',
                'select[aria-label*="Work Authorization" i]',
            ], "US Citizen")

    if fill_all or "employment type" in target_key or "desired job title" in target_key:
        _check_first_matching_dom_any(page, [
            'input[name="employment_type"][id*="FULL_TIME"]',
            'dhi-candidates-wired-onboarding-flow-state-controller input[name="employment_type"][id*="FULL_TIME"]',
        ], True)
        _check_first_matching_dom_any(page, [
            'input[name="employment_type"][id*="CONTRACT_W2"]',
            'dhi-candidates-wired-onboarding-flow-state-controller input[name="employment_type"][id*="CONTRACT_W2"]',
        ], True)
        _check_first_matching_dom_any(page, [
            'input[name="remote_preferences"][id*="REMOTE"]',
            'dhi-candidates-wired-onboarding-flow-state-controller input[name="remote_preferences"][id*="REMOTE"]',
        ], True)

    _check_first_matching_dom_any(page, [
        'input[name="security_clearance"][aria-label="false"]',
        'dhi-candidates-wired-onboarding-flow-state-controller input[name="security_clearance"][aria-label="false"]',
    ], True)


def _save_completion_flow(page: Page, selectors: ProfileSelectorRegistry, target: str = "") -> bool:
    target_key = target.lower()
    anchors_by_target = {
        "profile photo": ['input[type="file"]:not(#resume-upload)'],
        "desired job title": ['input[aria-label="Ideal Job"]', 'input[placeholder="Preferred Job Title"]', 'input[name="job_title"]'],
        "years experience": ['input[name="years_experience"]'],
        "location": ['input[name="city_state"]', 'input[name="location.country"]'],
        "work authorization": ['select[name="work_authorization"]'],
        "employment type": ['input[name="employment_type"]'],
    }
    anchors = anchors_by_target.get(target_key, [])
    if not anchors:
        for values in anchors_by_target.values():
            anchors.extend(values)

    for anchor in anchors:
        if _submit_nearest_form_for_selector(page, anchor):
            time.sleep(1)
            return True
        if _save_nearest_editor_for_selector(page, anchor):
            time.sleep(1)
            return True
    if _save_current_editor(page, selectors):
        time.sleep(1)
        return True
    return False


def _profile_has_photo(page: Page) -> bool:
    return _completion_item_is_complete(page, "Profile Photo")


def _upload_profile_photo(page: Page, selectors: ProfileSelectorRegistry, photo_path: str) -> bool:
    if not photo_path:
        return False
    file_obj = Path(photo_path)
    if not file_obj.exists():
        return False
    if _profile_has_photo(page):
        return True

    _click_completion_item(page, "Profile Photo")
    time.sleep(1)
    candidates = [
        'dhi-candidates-wired-candidate-profile input[type="file"]:not(#resume-upload)',
        'input[aria-label*="Profile Photo" i][type="file"]',
        'input[aria-label*="photo" i][type="file"]',
        'input[type="file"]:not(#resume-upload)',
    ]
    uploaded = False
    for selector in candidates:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="attached", timeout=3000)
            locator.set_input_files(str(file_obj))
            uploaded = True
            break
        except Exception:
            continue
    if not uploaded:
        return False

    time.sleep(2)
    for _ in range(4):
        if _dom_click_first_visible(page, [
            'button:has-text("Save")',
            'seds-button:has-text("Save")',
            'button:has-text("Done")',
            'seds-button:has-text("Done")',
            'button:has-text("Apply")',
            'seds-button:has-text("Apply")',
            'button:has-text("Update")',
            'seds-button:has-text("Update")',
        ], timeout_ms=3000) or _save_current_editor(page, selectors, settle_seconds=1.5):
            time.sleep(2)
            if _profile_has_photo(page):
                return True
        else:
            break
    _dismiss_open_modal(page)
    return _profile_has_photo(page)


def _update_about_completion_graphql(page: Page, payload: DiceProfilePayload) -> bool:
    try:
        result = page.evaluate(
            """
            async ({ yearsExperience }) => {
              const candidateId = window.ssdl?.user?.profile?.candidate_id
                || window.ssdl?.user?.candidate_id
                || localStorage.getItem('candidate_id');
              const identity = localStorage.getItem('identity') || '';
              if (!candidateId) {
                return { ok: false, reason: 'missing candidate id' };
              }
              const headers = { 'content-type': 'application/json' };
              if (identity) headers.authorization = `Bearer ${identity}`;

              const contactBody = {
                operationName: 'updateAboutContactInfo',
                variables: {
                  contactInfo: {
                    candidateId,
                    contact: {
                      firstName: window.ssdl?.user?.first_name || 'Tyler',
                      lastName: window.ssdl?.user?.last_name || 'Davis',
                      areaCode: null,
                      phoneNumber: null,
                      location: {
                        municipality: 'Denver',
                        region: 'CO',
                        country: 'United States',
                        postalCode: '80202',
                      },
                    },
                  },
                },
                query: `mutation updateAboutContactInfo($contactInfo: UpdateContactInfoInput) {
                  updateContactInfo(contactInfo: $contactInfo) {
                    firstName
                    lastName
                    areaCode
                    phoneNumber
                    location {
                      municipality
                      region
                      country
                      postalCode
                      __typename
                    }
                    __typename
                  }
                }`,
              };
              const careerBody = {
                operationName: 'updateCareerInfo',
                variables: {
                  candidateId,
                  careerInfo: {
                    workAuthorization: 'US_CITIZEN',
                    yearsExperience,
                    securityClearance: false,
                  },
                },
                query: `mutation updateCareerInfo($candidateId: ID!, $careerInfo: CareerInfoInput!) {
                  updateCareerInfo(candidateId: $candidateId, careerInfo: $careerInfo) {
                    yearsExperience
                    workAuthorization
                    securityClearance
                    __typename
                  }
                }`,
              };
              const contactResponse = await fetch('https://api.prod.candidate-prod.dhiaws.com/graphql', {
                method: 'POST',
                headers,
                credentials: 'include',
                body: JSON.stringify(contactBody),
              });
              const contactJson = await contactResponse.json().catch(() => ({}));
              const careerResponse = await fetch('https://api.prod.candidate-prod.dhiaws.com/graphql', {
                method: 'POST',
                headers,
                credentials: 'include',
                body: JSON.stringify(careerBody),
              });
              const careerJson = await careerResponse.json().catch(() => ({}));
              return {
                ok: contactResponse.ok && careerResponse.ok && !contactJson.errors && !careerJson.errors,
                contactStatus: contactResponse.status,
                careerStatus: careerResponse.status,
                contactJson,
                careerJson,
              };
            }
            """,
            {"yearsExperience": int(payload.years_experience)},
        )
        return bool(result and result.get("ok"))
    except Exception:
        return False


def _profile_has_parsed_skills(page: Page) -> bool:
    text = _profile_text_with_control_values(page, timeout_ms=2000)
    return ("see all" in text and "skills" in text) or "✓skills" in text or "\u2713skills" in text


def _profile_has_resume(page: Page) -> bool:
    text = _profile_text_with_control_values(page, timeout_ms=2000)
    return ("✓resume" in text or "\u2713resume" in text) or (".pdf" in text and ("download" in text or "upload new resume" in text))


def _fill_required_preference_fields(page: Page) -> None:
    _check_first_matching(page, [
        'input[name="employment_type"][id*="FULL_TIME"]',
        'input[name="employment_type"][aria-label="FULL_TIME"]',
    ], True)
    _check_first_matching(page, [
        'input[name="employment_type"][id*="CONTRACT_W2"]',
        'input[name="employment_type"][aria-label="CONTRACT_W2"]',
    ], True)
    _check_first_matching(page, [
        'input[name="remote_preferences"][id*="REMOTE"]',
        'input[name="remote_preferences"][aria-label="REMOTE"]',
    ], True)
    _select_first_matching(page, [
        'select[name="work_authorization"]',
        'select[aria-label*="Work Authorization" i]',
    ], "US Citizen")
    _check_first_matching(page, [
        'input[name="security_clearance"][aria-label="false"]',
        'input[name="security_clearance"][value="false"]',
    ], True)


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

    for skill in payload.skills[:8]:
        if skill.lower() in existing_text.lower():
            continue
        try:
            skill_input.click(timeout=1500)
            skill_input.fill(skill, timeout=1500)
            skill_input.press("Enter", timeout=1500)
            time.sleep(0.2)
        except Exception:
            try:
                skill_input.click(timeout=1500)
                skill_input.type(skill, delay=10, timeout=2000)
                skill_input.press("Enter", timeout=1500)
                time.sleep(0.2)
            except Exception:
                continue


def _split_location(location: str) -> tuple[str, str]:
    parts = [part.strip() for part in (location or "").split(",") if part.strip()]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[-1]


def _upload_resume_and_accept_parse(page: Page, selectors: ProfileSelectorRegistry, resume_path: str) -> None:
    if not resume_path:
        return
    if _profile_has_resume(page):
        return
    _expand_section(page, selectors, "resume")
    if not _set_file_input(page, selectors.resume_upload_candidates, resume_path):
        return
    time.sleep(1)
    if not _dom_click_first_visible(page, ['button:has-text("Yes")', 'seds-button:has-text("Yes")'], timeout_ms=4000):
        _click_any(page, ['button:has-text("Yes")', 'seds-button:has-text("Yes")'], timeout_ms=4000)
    time.sleep(1)
    _dom_click_first_visible(page, ['button:has-text("Close")', 'seds-button:has-text("Close")'], timeout_ms=4000)


def _open_inline_editor(page: Page, button_selectors: Sequence[str]) -> bool:
    return _dom_click_first_visible(page, button_selectors, timeout_ms=4000)


def _save_current_editor(page: Page, selectors: ProfileSelectorRegistry, settle_seconds: float = 1.0) -> bool:
    saved = _save_profile(page, selectors)
    if saved:
        time.sleep(settle_seconds)
    return saved


def _set_month_field(page: Page, selector: str, year: str, month_number: str) -> bool:
    value = f"{year}-{month_number}"
    locator = _first_visible(page, [selector], timeout_ms=2000)
    if locator is None:
        return False
    try:
        locator.evaluate(
            """
            (el, value) => {
              el.value = value;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            """,
            value,
        )
        return True
    except Exception:
        try:
            locator.fill(value, timeout=1500)
            return True
        except Exception:
            return False


def _set_year_field(page: Page, candidates: Sequence[str], year: str) -> bool:
    year = (year or "").strip()
    if not year:
        return False
    return _fill_first_matching(page, candidates, year, timeout_ms=2000)


def _fill_social_profile(page: Page, label: str, url: str) -> bool:
    url = (url or "").strip()
    if not url or "default" in url or url == "https://google.com":
        return False
    candidates = [
        f'input[name*="{label}" i]',
        f'input[id*="{label}" i]',
        f'input[placeholder*="{label}" i]',
        f'input[aria-label*="{label}" i]',
        'input[type="url"]',
        'input[placeholder*="url" i]',
        'input[name*="url" i]',
    ]
    return _fill_first_matching(page, candidates, url, timeout_ms=2000)


def _fill_education(page: Page, education: EducationPayload, selectors: ProfileSelectorRegistry) -> None:
    school_candidates = ['input[name="institution"]', *selectors.input_candidates["school"]]
    _type_first_matching(page, school_candidates, education.institution)
    if education.institution.lower() not in _get_first_matching_value(page, school_candidates).lower():
        _fill_first_matching(page, school_candidates, education.institution)
    if education.institution.lower() not in _get_first_matching_value(page, school_candidates).lower():
        _set_first_matching_dom(page, school_candidates, education.institution)
    if not _select_first_matching(page, selectors.input_candidates["degree"], education.degree):
        if not _select_first_matching_dom(page, selectors.input_candidates["degree"], education.degree):
            _fill_first_matching(page, selectors.input_candidates["degree"], education.degree)
    if not _fill_first_matching(page, selectors.input_candidates["field_of_study"], education.field_of_study):
        _set_first_matching_dom(page, selectors.input_candidates["field_of_study"], education.field_of_study)
    if not _fill_first_matching(page, selectors.input_candidates["education_location"], "Denver, CO"):
        _set_first_matching_dom(page, selectors.input_candidates["education_location"], "Denver, CO")
    _choose_autocomplete_option(page, selectors.input_candidates["education_location"], "Denver, CO")
    _set_year_field(page, [
        'input[name*="start" i][name*="year" i]:not([name="start_month_year"])',
        'input[aria-label*="start" i][aria-label*="year" i]',
        'input[placeholder*="start" i][placeholder*="year" i]',
        'input[name*="from" i]',
    ], education.start_year)
    _set_year_field(page, [
        'input[name*="end" i][name*="year" i]:not([name="end_month_year"])',
        'input[aria-label*="end" i][aria-label*="year" i]',
        'input[placeholder*="end" i][placeholder*="year" i]',
        'input[name*="graduation" i]',
        'input[name*="to" i]',
    ], education.end_year)


def _save_nearest_editor_for_selector(page: Page, anchor_selector: str) -> bool:
    try:
        return bool(page.evaluate(
            """
            (anchorSelector) => {
              const isVisible = (el) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
              };
              const isEnabled = (el) => !el.disabled && el.getAttribute('aria-disabled') !== 'true' && !el.hasAttribute('disabled');
              const textOf = (el) => (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
              const findAnchor = (root) => {
                for (const el of Array.from(root.querySelectorAll(anchorSelector))) {
                  if (isVisible(el)) return el;
                }
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  if (el.shadowRoot) {
                    const found = findAnchor(el.shadowRoot);
                    if (found) return found;
                  }
                }
                return null;
              };
              const anchor = findAnchor(document);
              if (!anchor) return false;
              const actionSelector = 'button[type="submit"],seds-button[type="submit"],button,seds-button';
              const containers = [];
              let current = anchor;
              for (let i = 0; i < 12 && current; i += 1) {
                containers.push(current);
                current = current.parentElement || current.getRootNode().host || null;
              }
              for (const container of containers) {
                const actions = Array.from(container.querySelectorAll(actionSelector)).filter((el) => isVisible(el) && isEnabled(el));
                const preferred = actions.find((el) => /^(save|update|done|add education|add)$/i.test(textOf(el)));
                const submit = actions.find((el) => el.matches('button[type="submit"],seds-button[type="submit"]'));
                const target = preferred || submit || actions[actions.length - 1];
                if (target) {
                  target.click();
                  return true;
                }
              }
              return false;
            }
            """,
            anchor_selector,
        ))
    except Exception:
        return False


def _submit_nearest_form_for_selector(page: Page, anchor_selector: str) -> bool:
    try:
        return bool(page.evaluate(
            """
            (anchorSelector) => {
              const findAnchor = (root) => {
                for (const el of Array.from(root.querySelectorAll(anchorSelector))) {
                  return el;
                }
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  if (el.shadowRoot) {
                    const found = findAnchor(el.shadowRoot);
                    if (found) return found;
                  }
                }
                return null;
              };
              const anchor = findAnchor(document);
              if (!anchor) return false;
              let current = anchor;
              for (let i = 0; i < 12 && current; i += 1) {
                if (current.tagName && current.tagName.toLowerCase() === 'form') {
                  if (current.requestSubmit) current.requestSubmit();
                  else current.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true, composed: true }));
                  return true;
                }
                current = current.parentElement || current.getRootNode().host || null;
              }
              return false;
            }
            """,
            anchor_selector,
        ))
    except Exception:
        return False


def _fill_work_experience(page: Page, experience: WorkExperiencePayload) -> None:
    _fill_first_matching(page, [
        'input[name="job_title"][placeholder="Job Title"]',
        'input[name*="title" i]',
        'input[name*="position" i]',
        'input[aria-label*="title" i]',
        'input[placeholder*="title" i]',
        'input[aria-label*="position" i]',
        'input[placeholder*="position" i]',
    ], experience.title)
    _fill_first_matching(page, [
        'input[name="company"]',
        'input[name*="company" i]',
        'input[name*="employer" i]',
        'input[aria-label*="company" i]',
        'input[placeholder*="company" i]',
        'input[aria-label*="employer" i]',
        'input[placeholder*="employer" i]',
    ], experience.company)
    month_numbers = {
        "january": "01",
        "february": "02",
        "march": "03",
        "april": "04",
        "may": "05",
        "june": "06",
        "july": "07",
        "august": "08",
        "september": "09",
        "october": "10",
        "november": "11",
        "december": "12",
    }
    start_month_number = month_numbers.get(experience.start_month.lower())
    set_combined_start = False
    if start_month_number:
        set_combined_start = _set_month_field(page, 'input[name="start_month_year"]', experience.start_year, start_month_number)
    if not set_combined_start:
        _select_first_matching(page, [
            'select[name*="start" i][name*="month" i]',
            'select[aria-label*="start" i][aria-label*="month" i]',
        ], experience.start_month)
        _fill_first_matching(page, [
            'input[name*="start" i][name*="year" i]:not([name="start_month_year"])',
            'input[aria-label*="start" i][aria-label*="year" i]',
            'input[placeholder*="start" i][placeholder*="year" i]',
        ], experience.start_year)
    if experience.current:
        _check_first_matching(page, [
            'input[name="current_position"]',
            'input[type="checkbox"][name*="current" i]',
            'input[type="checkbox"][aria-label*="current" i]',
            'input[type="checkbox"][name*="present" i]',
            'input[type="checkbox"][aria-label*="present" i]',
        ], True)
    else:
        end_month_number = month_numbers.get(experience.end_month.lower())
        set_combined_end = False
        if end_month_number:
            set_combined_end = _set_month_field(page, 'input[name="end_month_year"]', experience.end_year, end_month_number)
        if not set_combined_end:
            _select_first_matching(page, [
                'select[name*="end" i][name*="month" i]',
                'select[aria-label*="end" i][aria-label*="month" i]',
            ], experience.end_month)
            _fill_first_matching(page, [
                'input[name*="end" i][name*="year" i]:not([name="end_month_year"])',
                'input[aria-label*="end" i][aria-label*="year" i]',
                'input[placeholder*="end" i][placeholder*="year" i]',
            ], experience.end_year)
    _fill_first_matching(page, [
        'textarea[name*="description" i]',
        'textarea[name*="responsibilities" i]',
        'textarea[aria-label*="description" i]',
        'textarea[placeholder*="description" i]',
        '[contenteditable="true"][aria-label*="description" i]',
    ], experience.description)


def _choose_profile_option(page: Page, field_hint: str, patterns: Sequence[str]) -> bool:
    return bool(page.evaluate(
        """
        ({ fieldHint, patterns }) => {
          const regexes = patterns.map((pattern) => new RegExp(pattern, 'i'));
          const hint = fieldHint.toLowerCase();
          const isVisible = (el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
          };
          const labelTextFor = (el) => {
            const parts = [];
            if (el.id) {
              const root = el.getRootNode && el.getRootNode();
              const labelRoot = root && root.querySelectorAll ? root : document;
              const labels = Array.from(labelRoot.querySelectorAll(`label[for="${CSS.escape(el.id)}"]`));
              parts.push(...labels.map((label) => label.innerText || label.textContent || ''));
            }
            const parentLabel = el.closest && el.closest('label');
            if (parentLabel) parts.push(parentLabel.innerText || parentLabel.textContent || '');
            return parts.join(' ');
          };
          const textOf = (el) => {
            return [
              el.innerText,
              el.textContent,
              labelTextFor(el),
              el.value,
              el.name,
              el.id,
              el.getAttribute('aria-label'),
              el.getAttribute('data-related-input'),
            ].filter(Boolean).join(' ').trim().replace(/\\s+/g, ' ');
          };
          const matches = (el) => regexes.some((regex) => regex.test(textOf(el)));
          const hintMatches = (el) => textOf(el).toLowerCase().includes(hint);
          const canUse = (el) => isVisible(el) || el.matches('input[type="checkbox"],input[type="radio"]');
          const clickTargetFor = (el) => {
            const innerControl = (candidate) => {
              if (candidate && candidate.shadowRoot) {
                return candidate.shadowRoot.querySelector('button,[role="button"],input[type="checkbox"],input[type="radio"]');
              }
              return null;
            };
            const chip = el.closest && el.closest('dhi-candidates-selectable-chip,dhi-candidates-chip');
            const chipInner = innerControl(chip);
            if (chipInner) return chipInner;
            const ownInner = innerControl(el);
            if (ownInner) return ownInner;
            if (!el.matches('input[type="checkbox"],input[type="radio"]')) return el;
            if (isVisible(el)) return el;
            if (el.id) {
              const root = el.getRootNode && el.getRootNode();
              const labelRoot = root && root.querySelector ? root : document;
              const label = labelRoot.querySelector(`label[for="${CSS.escape(el.id)}"]`);
              if (label && isVisible(label)) return label;
            }
            const parentLabel = el.closest('label');
            if (parentLabel && isVisible(parentLabel)) return parentLabel;
            return el;
          };
          const clickableSelector = [
            'input[type="checkbox"]',
            'input[type="radio"]',
            'label',
            'button',
            'seds-button',
            '[role="checkbox"]',
            '[role="radio"]',
            '[role="button"]',
            'dhi-candidates-selectable-chip',
            'dhi-candidates-chip',
          ].join(',');
          const allCandidates = [];
          const walk = (root) => {
            for (const el of Array.from(root.querySelectorAll(clickableSelector))) {
              if (!canUse(el)) continue;
              allCandidates.push(el);
            }
            for (const el of Array.from(root.querySelectorAll('*'))) {
              if (el.shadowRoot) walk(el.shadowRoot);
            }
          };
          walk(document);

          const hinted = allCandidates.filter((el) => {
            if (hintMatches(el)) return true;
            let current = el;
            for (let i = 0; i < 6 && current; i += 1) {
              if (hintMatches(current)) return true;
              current = current.parentElement || current.getRootNode().host || null;
            }
            return false;
          });
          const pools = [hinted, allCandidates];
          for (const pool of pools) {
            const target = pool.find(matches);
            if (!target) continue;
            if (target.matches('input[type="checkbox"],input[type="radio"]')) {
              clickTargetFor(target).click();
              target.checked = true;
              target.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
              target.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
            } else {
              clickTargetFor(target).click();
            }
            return true;
          }
          return false;
        }
        """,
        {"fieldHint": field_hint, "patterns": list(patterns)},
    ))


def _open_related_profile_editor(page: Page, related_input: str, prompts: Sequence[str]) -> bool:
    return bool(page.evaluate(
        """
        ({ relatedInput, prompts }) => {
          const promptRegexes = prompts.map((prompt) => new RegExp(prompt, 'i'));
          const isVisible = (el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
          };
          const textOf = (el) => (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
          const selector = 'button,seds-button,[role="button"]';
          const candidates = [];
          const walk = (root) => {
            for (const el of Array.from(root.querySelectorAll(selector))) {
              if (!isVisible(el)) continue;
              const related = el.getAttribute('data-related-input') || '';
              const text = textOf(el);
              if (related === relatedInput || promptRegexes.some((regex) => regex.test(text))) {
                candidates.push(el);
              }
            }
            for (const el of Array.from(root.querySelectorAll('*'))) {
              if (el.shadowRoot) walk(el.shadowRoot);
            }
          };
          walk(document);
          if (!candidates.length) return false;
          candidates[0].click();
          return true;
        }
        """,
        {"relatedInput": related_input, "prompts": list(prompts)},
    ))


def _save_ideal_company_editor(page: Page) -> bool:
    return bool(page.evaluate(
        """
        () => {
          const isVisible = (el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
          };
          const textOf = (el) => (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
          const clickElement = (el) => {
            const inner = el.shadowRoot && el.shadowRoot.querySelector('button,[role="button"]');
            (inner || el).click();
          };
          const walk = (root) => {
            const controls = Array.from(root.querySelectorAll('input[name="ideal_company_size"],input[name="ideal_company_age"],seds-button,button'));
            const firstIdealIndex = controls.findIndex((el) => el.matches && el.matches('input[name="ideal_company_size"],input[name="ideal_company_age"]'));
            if (firstIdealIndex >= 0) {
              const save = controls.slice(firstIdealIndex + 1).find((el) => isVisible(el) && /^save$/i.test(textOf(el)));
              if (save) {
                clickElement(save);
                return true;
              }
            }
            for (const el of Array.from(root.querySelectorAll('*'))) {
              if (el.shadowRoot) {
                const result = walk(el.shadowRoot);
                if (result) return true;
              }
            }
            return false;
          };
          return walk(document);
        }
        """
    ))


def _save_profile(page: Page, selectors: ProfileSelectorRegistry) -> bool:
    try:
        clicked = page.evaluate(
            """
            () => {
              const seen = new Set();
              const candidates = [];
              const selector = [
                'button[type="submit"]',
                'seds-button[type="submit"]',
                'button',
                'seds-button',
              ].join(',');
              const actionText = /^(save|save profile|save changes|update|continue|next|done|close)$/i;
              const submitCandidates = [];

              const isVisible = (el) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
              };

              const isEnabled = (el) => {
                return !el.disabled && el.getAttribute('aria-disabled') !== 'true' && !el.hasAttribute('disabled');
              };

              const walk = (root, depth = 0, host = 'document') => {
                for (const el of Array.from(root.querySelectorAll(selector))) {
                  if (seen.has(el) || !isVisible(el) || !isEnabled(el)) continue;
                  seen.add(el);
                  const rect = el.getBoundingClientRect();
                  const text = (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
                  if (!actionText.test(text)) continue;
                  candidates.push({
                    el,
                    top: rect.top,
                    left: rect.left,
                    text,
                    host,
                    depth,
                  });
                }
                for (const el of Array.from(root.querySelectorAll('button[type="submit"],seds-button[type="submit"]'))) {
                  if (seen.has(el) || !isVisible(el) || !isEnabled(el)) continue;
                  seen.add(el);
                  const rect = el.getBoundingClientRect();
                  submitCandidates.push({el, top: rect.top, left: rect.left, host, depth});
                }
                for (const el of Array.from(root.querySelectorAll('*'))) {
                  if (el.shadowRoot) {
                    walk(el.shadowRoot, depth + 1, el.tagName.toLowerCase());
                  }
                }
              };

              walk(document);
              candidates.sort((a, b) => {
                const aScore = /save|update/i.test(a.text) ? 2 : /continue|next|done|close/i.test(a.text) ? 1 : 0;
                const bScore = /save|update/i.test(b.text) ? 2 : /continue|next|done|close/i.test(b.text) ? 1 : 0;
                if (aScore !== bScore) return bScore - aScore;
                if (a.top !== b.top) return b.top - a.top;
                if (a.left !== b.left) return a.left - b.left;
                return b.depth - a.depth;
              });
              if (candidates.length) {
                candidates[0].el.click();
                return true;
              }
              const profileSubmits = submitCandidates.filter((candidate) => !candidate.host.includes('onboarding'));
              const fallbackSubmits = profileSubmits.length ? profileSubmits : submitCandidates;
              fallbackSubmits.sort((a, b) => {
                if (a.depth !== b.depth) return b.depth - a.depth;
                if (a.top !== b.top) return b.top - a.top;
                return b.left - a.left;
              });
              if (!fallbackSubmits.length) return false;
              fallbackSubmits[0].el.click();
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

    def fill_completion_checklist_section(self) -> None:
        self._log("Filling profile completion checklist")
        _dismiss_open_modal(self.page)
        targets = [
            "Profile Photo",
            "Desired Job Title",
            "Years Experience",
            "Location",
            "Work Authorization",
            "Employment Type",
        ]
        if all(_completion_item_is_complete(self.page, target) for target in targets):
            self._log("Profile completion checklist already has required fields")
            return

        for target in targets:
            if _completion_item_is_complete(self.page, target):
                continue
            self._log(f"Opening completion checklist item: {target}")
            if target == "Profile Photo":
                if _upload_profile_photo(self.page, self.selectors, self.payload.profile_photo_path):
                    self._log("Profile photo uploaded")
                else:
                    self._log("Profile photo upload did not complete")
                status = "complete" if _completion_item_is_complete(self.page, target) else "still incomplete"
                self._log(f"Completion checklist item {target}: {status}")
                continue
            if not _click_completion_item(self.page, target):
                self._log(f"Could not open completion checklist item: {target}")
                continue
            time.sleep(1)
            _fill_completion_fields(self.page, self.payload, target)
            if _save_completion_flow(self.page, self.selectors, target):
                self._log(f"Completion checklist save clicked for {target}")
            else:
                self._log(f"Completion checklist save button not found for {target}")
            time.sleep(2)
            _dismiss_open_modal(self.page)
            status = "complete" if _completion_item_is_complete(self.page, target) else "still incomplete"
            self._log(f"Completion checklist item {target}: {status}")

        if not _completion_non_photo_complete(self.page):
            self._log("Applying GraphQL fallback for about/contact completion fields")
            if _update_about_completion_graphql(self.page, self.payload):
                self._log("GraphQL fallback saved about/contact completion fields")
                self.page.reload(wait_until="domcontentloaded", timeout=60000)
                try:
                    self.page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                time.sleep(2)
            else:
                self._log("GraphQL fallback did not save about/contact completion fields")

    def fill_identity_section(self) -> None:
        self._log("Filling identity section")
        _dismiss_open_modal(self.page)
        _expand_section(self.page, self.selectors, "identity")
        if _open_inline_editor(self.page, [
            'button[data-related-input="job_title"]',
            'button:has-text("What do you want for your next job title?")',
            'button:has-text("Add Desired Job Title")',
        ]):
            _fill_first_matching(self.page, self.selectors.input_candidates["job_title"], self.payload.headline)
            _fill_required_preference_fields(self.page)
            _save_current_editor(self.page, self.selectors)
        if _open_inline_editor(self.page, [
            'button[data-related-input="years_experience"]',
            'button:has-text("How many years of experience do you have?")',
        ]):
            _fill_first_matching(self.page, self.selectors.input_candidates["years_experience"], str(self.payload.years_experience))
            _fill_required_preference_fields(self.page)
            _save_current_editor(self.page, self.selectors)

    def fill_contact_section(self) -> None:
        self._log("Filling contact section")
        _dismiss_open_modal(self.page)
        _expand_section(self.page, self.selectors, "contact")
        if _open_inline_editor(self.page, [
            'button[data-related-input="location.municipality"]',
            'button:has-text("Where are you currently located?")',
            'button:has-text("Location")',
        ]):
            city, country = _split_location(self.payload.location)
            if city:
                city_value = city if "," in city else f"{city}, CO"
                _fill_first_matching(self.page, ['input[name="city_state"]', 'input[aria-label*="City" i]'], city_value)
            if country:
                country_value = "United States" if country.upper() in {"USA", "US"} else country
                _fill_first_matching(self.page, ['input[name="location.country"]', 'input[aria-label*="Country" i]'], country_value)
            _fill_required_preference_fields(self.page)
            _save_current_editor(self.page, self.selectors)

    def fill_summary_section(self) -> None:
        self._log("Filling summary section")
        _dismiss_open_modal(self.page)
        _expand_section(self.page, self.selectors, "summary")
        if _open_inline_editor(self.page, [
            'button:has-text("Edit About Me")',
            'button[data-related-input="about_me"]',
            'button:has-text("About")',
        ]):
            _fill_first_matching(self.page, self.selectors.input_candidates["summary"], self.payload.summary)
            _fill_first_matching(self.page, self.selectors.input_candidates["years_experience"], str(self.payload.years_experience))
            _fill_required_preference_fields(self.page)
            _save_current_editor(self.page, self.selectors)

    def fill_resume_section(self) -> None:
        self._log("Filling resume section")
        _upload_resume_and_accept_parse(self.page, self.selectors, self.payload.resume_path)

    def fill_skills_section(self) -> None:
        self._log("Filling skills section")
        _dismiss_open_modal(self.page)
        if _profile_has_parsed_skills(self.page):
            self._log("Skills already parsed from resume; skipping skills editor")
            return
        if _open_inline_editor(self.page, [
            'button:has-text("Edit Skills")',
            'button:has-text("Add Skills")',
            'button:has-text("Skills")',
        ]):
            _add_skills(self.page, self.payload, self.selectors)
            _save_current_editor(self.page, self.selectors)
            _dismiss_open_modal(self.page)

    def fill_work_experience_section(self) -> None:
        self._log("Filling work experience section")
        _dismiss_open_modal(self.page)
        for experience in self.payload.work_experiences[:1]:
            visible_text = _profile_text_with_control_values(self.page, timeout_ms=3000)
            if experience.company.lower() in visible_text and experience.title.lower() in visible_text:
                self._log("Work experience already present; skipping duplicate add")
                return
            if _open_inline_editor(self.page, [
                'seds-button:has-text("Add work experience")',
                'seds-button:has-text("Add experience")',
                'button:has-text("Add work experience")',
                'button:has-text("Add experience")',
            ]):
                time.sleep(1)
                _fill_work_experience(self.page, experience)
                _save_current_editor(self.page, self.selectors)

    def fill_ideal_job_section(self) -> None:
        self._log("Filling ideal job section")
        _dismiss_open_modal(self.page)
        _scroll_to_text(self.page, "Ideal Job")
        if _ideal_job_card_complete(self.page, self.payload):
            self._log("Ideal job already present; skipping")
            return
        if _dom_click_card_action(self.page, "Ideal Job", ["Edit Ideal Job"]) or _open_inline_editor(self.page, [
            'seds-button:has-text("Edit Ideal Job")',
            'button:has-text("Edit Ideal Job")',
            'button[data-related-input="job_title"]',
            'button:has-text("What do you want for your next job title?")',
        ]):
            time.sleep(1)
            _fill_first_matching(self.page, self.selectors.input_candidates["job_title"], self.payload.headline)
            _fill_required_preference_fields(self.page)
            _fill_first_matching(self.page, self.selectors.input_candidates["salary"], self.payload.desired_salary)
            _check_first_matching(self.page, [
                'input[name="remote_preferences"][id*="REMOTE"]',
                'input[name="remote_preference"][id*="REMOTE"]',
                'input[type="checkbox"][aria-label="REMOTE"]',
                'input[type="checkbox"][aria-label*="remote" i]',
            ], True)
            _check_first_matching(self.page, [
                'input[name="employment_type"][id*="FULL_TIME"]',
                'input[type="checkbox"][aria-label="FULL_TIME"]',
            ], True)
            _check_first_matching(self.page, [
                'input[name="employment_type"][id*="CONTRACT_W2"]',
                'input[type="checkbox"][aria-label="CONTRACT_W2"]',
            ], True)
            _save_current_editor(self.page, self.selectors)

    def fill_ideal_company_section(self) -> None:
        self._log("Filling ideal company section")
        _dismiss_open_modal(self.page)
        _scroll_to_text(self.page, "Ideal Company")
        if _ideal_company_card_complete(self.page, self.payload):
            self._log("Ideal company already present; skipping")
            return

        if _open_related_profile_editor(self.page, "ideal_company_size", [
            r"What size of company",
            r"Company Employee Size",
        ]) or _dom_click_card_action(self.page, "Ideal Company", ["Edit Ideal Company"]):
            time.sleep(1)
            size_selected = _choose_profile_option(self.page, "ideal_company_size", [
                r"51\\s*[-–]\\s*100",
                r"51.*100",
                r"medium",
            ])
            if not size_selected:
                self._log("Ideal company size option not found")
            if _save_ideal_company_editor(self.page) or _save_nearest_editor_for_selector(self.page, 'input[name="ideal_company_size"]') or _save_current_editor(self.page, self.selectors):
                self._log("Ideal company size editor save clicked")
            else:
                self._log("Ideal company size editor save button not found")
            time.sleep(1)
            _dismiss_open_modal(self.page)

        _scroll_to_text(self.page, "Ideal Company")
        if _open_related_profile_editor(self.page, "ideal_company_age", [
            r"What age of company",
            r"Company Age",
        ]):
            time.sleep(1)
            size_selected = _choose_profile_option(self.page, "ideal_company_size", [
                r"51\\s*[-–]\\s*100",
                r"51.*100",
                r"medium",
            ])
            age_selected = _choose_profile_option(self.page, "ideal_company_age", [
                r"11\\s*[-–]\\s*20",
                r"11.*20",
                r"established",
                r"mature",
            ])
            if not size_selected:
                self._log("Ideal company size option not found in age editor")
            if not age_selected:
                self._log("Ideal company age option not found")
                capture_profile_debug_bundle(self.page, "ideal_company_age_options_missing", "Ideal company age editor did not expose a matching option")
            if (
                _save_ideal_company_editor(self.page)
                or _save_nearest_editor_for_selector(self.page, 'input[name="ideal_company_size"]')
                or _save_nearest_editor_for_selector(self.page, 'input[name="ideal_company_age"]')
                or _save_current_editor(self.page, self.selectors)
            ):
                self._log("Ideal company age editor save clicked")
            else:
                self._log("Ideal company age editor save button not found")

    def fill_education_section(self) -> None:
        self._log("Filling education section")
        _dismiss_open_modal(self.page)
        if not self.payload.educations:
            return
        _scroll_to_text(self.page, "Education")
        education = self.payload.educations[0]
        visible_text = _profile_text_with_control_values(self.page, timeout_ms=3000)
        if education.institution.lower() in visible_text and education.field_of_study.lower() in visible_text:
            self._log("Education already present; skipping duplicate add")
            return
        if _dom_click_card_action(self.page, "Education", ["Add Education", "Add education"]) or _open_inline_editor(self.page, [
            'seds-button:has-text("Add Education")',
            'seds-button:has-text("Add education")',
            'button:has-text("Add Education")',
            'button:has-text("Add education")',
        ]):
            time.sleep(1)
            if self.page.locator('input[name="institution"]').first.count() == 0:
                self._log("Education editor did not expose institution input")
                capture_profile_debug_bundle(self.page, "education_editor_missing", "Education editor did not expose institution input")
                return
            self._log("Education editor opened")
            _fill_education(self.page, education, self.selectors)
            time.sleep(0.5)
            school_value = _get_first_matching_value(self.page, self.selectors.input_candidates["school"])
            degree_value = _get_first_matching_value(self.page, self.selectors.input_candidates["degree"])
            location_value = _get_first_matching_value(self.page, self.selectors.input_candidates["education_location"])
            self._log(f"Education editor values: school={school_value!r} degree={degree_value!r} location={location_value!r}")
            if education.institution.lower() not in school_value.lower():
                capture_profile_debug_bundle(self.page, "education_values_missing", "Education values were not set before save")
                return
            if _save_nearest_editor_for_selector(self.page, 'input[name="institution"]') or _save_current_editor(self.page, self.selectors):
                self._log("Education editor save clicked")
            else:
                self._log("Education editor save button not found")

    def fill_social_profiles_section(self) -> None:
        self._log("Filling social profiles section")
        _dismiss_open_modal(self.page)
        _scroll_to_text(self.page, "Social Profiles")
        urls = [
            ("linkedin", self.payload.linkedin_url),
            ("website", self.payload.website_url),
            ("portfolio", self.payload.portfolio_url),
        ]
        expected_urls = [url.lower() for _, url in urls if url and "default" not in url and url != "https://google.com"]
        if not expected_urls:
            return
        visible_text = _profile_text_with_control_values(self.page, timeout_ms=3000)
        if any(url in visible_text for url in expected_urls):
            self._log("Social profile already present; skipping")
            return
        if _dom_click_card_action(self.page, "Social Profiles", ["Edit Social Profiles", "Add Social Profile"]) or _open_inline_editor(self.page, [
            'seds-button:has-text("Edit Social Profiles")',
            'button:has-text("Edit Social Profiles")',
            'seds-button:has-text("Add Social Profile")',
            'button:has-text("Add Social Profile")',
        ]):
            time.sleep(1)
            for label, url in urls:
                if _fill_social_profile(self.page, label, url):
                    break
            _save_current_editor(self.page, self.selectors)

    def fill_profile_visibility_section(self) -> None:
        if self.payload.profile_visible is None:
            return
        desired = "ON" if self.payload.profile_visible else "OFF"
        self._log(f"Setting profile visibility {desired}")
        if _set_profile_visibility(self.page, self.payload.profile_visible):
            self._log(f"Profile visibility verified {desired}")
            return
        capture_profile_debug_bundle(self.page, "visibility_toggle_failed", f"Could not set profile visibility {desired}")
        raise RuntimeError(f"Could not set Dice profile visibility {desired}.")

    def verify_profile(self) -> bool:
        _scroll_profile_page(self.page)
        visible_text = _profile_text_with_control_values(self.page, timeout_ms=5000)
        required = [
            self.payload.work_experiences[0].title if self.payload.work_experiences else "",
            self.payload.work_experiences[0].company if self.payload.work_experiences else "",
            self.payload.headline,
        ]
        has_required_text = all(value.lower() in visible_text for value in required if value)
        expected_social_urls = [
            url.lower()
            for url in [self.payload.linkedin_url, self.payload.website_url, self.payload.portfolio_url]
            if url and "default" not in url and url != "https://google.com"
        ]
        has_social = not expected_social_urls or any(url in visible_text for url in expected_social_urls)
        has_resume = _completion_item_is_complete(self.page, "Resume") or _profile_has_resume(self.page)
        has_skills = _completion_item_is_complete(self.page, "Skills") or _profile_has_parsed_skills(self.page)
        has_completion = _completion_required_complete(self.page)
        has_ideal_company = _ideal_company_card_complete(self.page, self.payload)
        current_visibility = _profile_visibility_state(self.page)
        has_visibility = self.payload.profile_visible is None or current_visibility is self.payload.profile_visible
        self._log(
            "Verification checks: "
            f"required_text={has_required_text} "
            f"social={has_social} "
            f"resume={has_resume} "
            f"skills={has_skills} "
            f"completion={has_completion} "
            f"ideal_company={has_ideal_company} "
            f"visibility={has_visibility}"
        )
        return has_required_text and has_social and has_resume and has_skills and has_completion and has_ideal_company and has_visibility

    def run(self) -> None:
        self._log("Opening profile page")
        self.open_profiles_page()
        self.ensure_profile_mode()
        self.fill_profile_visibility_section()
        if self.verify_profile():
            self._log("Required profile fields already verified; skipping edits")
            return
        self.fill_completion_checklist_section()
        self.fill_identity_section()
        self.fill_contact_section()
        self.fill_summary_section()
        self.fill_resume_section()
        self.fill_skills_section()
        self.fill_work_experience_section()
        self.fill_ideal_job_section()
        self.fill_ideal_company_section()
        self.fill_education_section()
        self.fill_social_profiles_section()
        self.fill_profile_visibility_section()

        time.sleep(3)
        self._log("Attempting final save if an editor is still open")
        if not self.verify_profile():
            saved = _save_profile(self.page, self.selectors)
            if not saved:
                self._log("No final save button found; continuing to verification")
            time.sleep(3)
            if not self.verify_profile():
                capture_profile_debug_bundle(self.page, "verification_failed", "Profile values missing after section saves")
                raise RuntimeError("Dice profile verification failed after section saves.")

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
    parser.add_argument(
        "--profile-visible",
        choices=["on", "off", "keep"],
        default="keep",
        help="Set Dice profile visibility on/off, or keep the current setting.",
    )
    args = parser.parse_args()

    email, password = _load_test_credentials()
    payload = build_profile_payload()
    if args.profile_visible != "keep":
        payload = replace(payload, profile_visible=args.profile_visible == "on")
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
