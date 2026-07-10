"""
Debug helpers for Dice profile automation.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower() or "profile"


def _safe(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def capture_profile_debug_bundle(page: Any, label: str, reason: str, base_dir: str = "app/dice/_experimental_/debug") -> None:
    debug_dir = Path(base_dir)
    debug_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{stamp}_{slugify(label)}"

    html_path = debug_dir / f"{base}_profile.html"
    png_path = debug_dir / f"{base}_profile.png"
    txt_path = debug_dir / f"{base}_controls.txt"

    try:
        html_path.write_text(page.content(), encoding="utf-8")
    except Exception as exc:
        txt_path.write_text(f"Failed to capture HTML: {exc}\nReason: {reason}", encoding="utf-8")
        return

    try:
        page.screenshot(path=str(png_path), full_page=True)
    except Exception:
        pass

    try:
        controls = page.evaluate(
            """
            () => {
              const results = [];
              const seen = new Set();
              const selector = 'input, textarea, button, a, [role="button"], select, [contenteditable="true"]';

              const walk = (root, depth = 0, host = 'document') => {
                const nodes = Array.from(root.querySelectorAll(selector));
                for (const el of nodes) {
                  if (seen.has(el)) continue;
                  seen.add(el);
                  results.push({
                    tag: el.tagName,
                    text: (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ').slice(0, 160),
                    name: el.getAttribute('name') || '',
                    id: el.id || '',
                    placeholder: el.getAttribute('placeholder') || '',
                    aria: el.getAttribute('aria-label') || '',
                    href: el.getAttribute('href') || '',
                    role: el.getAttribute('role') || '',
                    type: el.getAttribute('type') || '',
                    data_testid: el.getAttribute('data-testid') || '',
                    data_cy: el.getAttribute('data-cy') || '',
                    depth: String(depth),
                    host,
                  });
                }

                for (const el of Array.from(root.querySelectorAll('*'))) {
                  if (el.shadowRoot) {
                    walk(el.shadowRoot, depth + 1, el.tagName.toLowerCase());
                  }
                }
              };

              walk(document);
              return results;
            }
            """
        )
        lines = [f"Reason: {reason}", f"Captured: {stamp}", ""]
        for control in controls:
            lines.append(
                f"{_safe(control['tag'])} depth={_safe(control['depth'])} host={_safe(control['host'])} "
                f"testid={_safe(control['data_testid'])} cy={_safe(control['data_cy'])} "
                f"name={_safe(control['name'])} id={_safe(control['id'])} type={_safe(control['type'])} "
                f"role={_safe(control['role'])} aria={_safe(control['aria'])} href={_safe(control['href'])} "
                f"placeholder={_safe(control['placeholder'])} text={_safe(control['text'])}"
            )
        txt_path.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        txt_path.write_text(f"HTML saved to {html_path}\nScreenshot saved to {png_path}\nControl inventory failed: {exc}", encoding="utf-8")


def collect_profile_controls(page: Any) -> list[dict[str, str]]:
    return page.evaluate(
        """
        () => {
          const results = [];
          const seen = new Set();
          const selector = 'input, textarea, button, a, [role="button"], select, [contenteditable="true"]';

          const walk = (root, depth = 0, host = '') => {
            const nodes = Array.from(root.querySelectorAll(selector));
            for (const el of nodes) {
              if (seen.has(el)) continue;
              seen.add(el);
              results.push({
                tag: el.tagName,
                text: (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ').slice(0, 160),
                name: el.getAttribute('name') || '',
                id: el.id || '',
                placeholder: el.getAttribute('placeholder') || '',
                aria: el.getAttribute('aria-label') || '',
                href: el.getAttribute('href') || '',
                role: el.getAttribute('role') || '',
                type: el.getAttribute('type') || '',
                data_testid: el.getAttribute('data-testid') || '',
                data_cy: el.getAttribute('data-cy') || '',
                depth: String(depth),
                host,
              });
            }
            const elements = Array.from(root.querySelectorAll('*'));
            for (const el of elements) {
              if (el.shadowRoot) {
                walk(el.shadowRoot, depth + 1, el.tagName.toLowerCase());
              }
            }
          };

          walk(document, 0, 'document');
          return results;
        }
        """
    )


def print_profile_controls(page: Any, title: str = "Profile controls") -> list[dict[str, str]]:
    controls = collect_profile_controls(page)
    print(f"\n[{title}] count={len(controls)}", flush=True)
    for control in controls:
        print(
            f"{_safe(control['tag'])} "
            f"depth={_safe(control['depth'])} "
            f"host={_safe(control['host'])} "
            f"testid={_safe(control['data_testid'])} "
            f"cy={_safe(control['data_cy'])} "
            f"name={_safe(control['name'])} "
            f"id={_safe(control['id'])} "
            f"type={_safe(control['type'])} "
            f"role={_safe(control['role'])} "
            f"aria={_safe(control['aria'])} "
            f"href={_safe(control['href'])} "
            f"placeholder={_safe(control['placeholder'])} "
            f"text={_safe(control['text'])}",
            flush=True,
        )
    return controls


def dump_text_lines(path: str, lines: Iterable[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
