from __future__ import annotations

import os
import subprocess
from typing import Dict, Iterator, Tuple, Optional


def _build_env_with_creds(creds: Dict[str, str]) -> Dict[str, str]:
    env = os.environ.copy()
    # Map provided creds to common env names used by headless_test
    email = creds.get("email", "")
    password = creds.get("password", "")
    if email:
        env["DICE_EMAIL"] = email
        env["EMAIL"] = email
    if password:
        env["DICE_PASSWORD"] = password
        env["PASSWORD"] = password
    return env


def stream_headless_run(creds: Dict[str, str]) -> Tuple[int, Iterator[str]]:
    """
    Launch `uv run apply-dice-headless` and stream stdout lines.

    Returns (return_code, iterator_over_lines). The iterator should be consumed to execute the process.
    """
    env = _build_env_with_creds(creds)
    # Using uv ensures project deps/env are resolved.
    # headless_test currently takes no CLI args; it relies on env + _data_ profile.
    process = subprocess.Popen(
        ["uv", "run", "apply-dice-headless"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        env=env,
    )

    def _iter() -> Iterator[str]:
        assert process.stdout is not None
        for line in process.stdout:
            yield line.rstrip("\n")
        process.wait()

    return process.returncode or 0, _iter()


def parse_summary_from_logs(log_lines: Iterator[str]) -> Tuple[int, dict]:
    """
    Consume log lines, yield them to caller as we go (caller can display),
    and try to parse final summary from headless_test standard prints.

    Returns (return_code, summary_dict)
    """
    applied: Optional[int] = None
    failed: Optional[int] = None
    failed_jobs: list[str] = []
    last_rc = 0

    # We buffer lines to return summary while allowing caller to stream
    from collections import deque
    buffer = deque()

    for line in log_lines:
        buffer.append(line)
        # Parse known markers from headless_test.py
        if line.startswith("Jobs successfully applied:"):
            try:
                applied = int(line.split(":", 1)[1].strip())
            except Exception:
                pass
        elif line.startswith("Jobs failed:"):
            try:
                failed = int(line.split(":", 1)[1].strip())
            except Exception:
                pass
        elif line.strip().startswith("- "):
            failed_jobs.append(line.strip()[2:])

    summary = {
        "applied": applied if applied is not None else 0,
        "failed": failed if failed is not None else 0,
        "failed_jobs": failed_jobs,
    }
    return last_rc, summary
