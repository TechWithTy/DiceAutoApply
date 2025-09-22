from __future__ import annotations

import os
from typing import Dict, Any
import requests
from urllib.parse import quote

API_URL = os.getenv("SAAS_API_URL", "https://api.saasidea.com")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501")


def build_login_url() -> str:
    redirect = APP_BASE_URL
    return f"{API_URL}/login?redirect_url={quote(redirect, safe='') }"


def get_entitlements(token: str) -> Dict[str, Any]:
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{API_URL}/entitlements", headers=headers, timeout=20)
        if resp.ok:
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            return data or {"credits": 0}
    except Exception:
        pass
    return {"credits": 0}


def generate_report(token: str) -> Dict[str, Any]:
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(f"{API_URL}/generate-report", headers=headers, timeout=60)
        if resp.ok:
            return {"ok": True, "detail": resp.text}
        return {"ok": False, "status": resp.status_code, "detail": resp.text}
    except Exception as e:
        return {"ok": False, "detail": str(e)}
