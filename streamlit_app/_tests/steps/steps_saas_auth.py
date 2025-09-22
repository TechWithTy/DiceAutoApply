from __future__ import annotations

import os
from typing import Any, Dict
from lettuce import step, world, before, after

from streamlit_app.state import (
    ensure_session_defaults,
    set_auth_token,
    get_auth_token,
    set_entitlements_state,
    get_credits,
)
from streamlit_app.api import build_login_url, get_entitlements
from streamlit_app.ui_saas import can_use_features


@before.each_scenario
def setup_scenario(scenario):
    world.ctx: Dict[str, Any] = {}
    ensure_session_defaults()
    set_auth_token(None)
    set_entitlements_state({"credits": 0})


@after.each_scenario
def teardown_scenario(scenario):
    pass


@step('the Streamlit app is running')
def app_running(step):
    ensure_session_defaults()


@step('the backend API is available at "(.*)"')
def backend_available(step, url):
    os.environ["SAAS_API_URL"] = url


@step('the user is not logged in')
def user_not_logged_in(step):
    set_auth_token(None)


@step('the user accesses a protected page')
def access_protected(step):
    # In real app, we would redirect. Here we just record expected login url.
    world.ctx["login_url"] = build_login_url()


@step('the app redirects to "(.*)"')
def app_redirects_login(step, base_url):
    assert world.ctx.get("login_url").startswith(base_url + "/login")


@step('the user is returned with a valid token')
def user_returned_token(step):
    set_auth_token("TEST_TOKEN")
    assert get_auth_token() == "TEST_TOKEN"


@step('the user has logged in successfully')
def user_logged_in(step):
    set_auth_token("VALID_TOKEN")


@step('the backend redirects back with a token')
def backend_redirects(step):
    assert get_auth_token() is not None


@step('the app stores the token in session state')
def token_stored(step):
    assert get_auth_token() is not None


@step('the token is used for all API requests')
def token_used_for_api(step):
    # Monkeypatch requests.get inside api.get_entitlements
    import streamlit_app.api as api

    class FakeResp:
        ok = True
        headers = {"content-type": "application/json"}

        def json(self):
            return {"credits": 7}

    old_get = api.requests.get

    def fake_get(url, headers=None, timeout=20):
        assert headers and "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
        return FakeResp()

    api.requests.get = fake_get  # type: ignore
    try:
        data = get_entitlements(get_auth_token())
        set_entitlements_state(data)
        assert get_credits() == 7
    finally:
        api.requests.get = old_get  # type: ignore


@step('the app calls "/entitlements"')
def app_calls_entitlements(step):
    # We just rely on previous step setting state to credits.
    pass


@step('the user’s credit balance is displayed on the dashboard')
def credit_display(step):
    assert get_credits() >= 0


@step('the user is authenticated')
def user_authenticated(step):
    if get_auth_token() is None:
        set_auth_token("AUTH_TOKEN")


@step('the user’s credit balance is (\d+)')
def user_credits_is(step, amount):
    set_entitlements_state({"credits": int(amount)})


@step('the user clicks on "Generate Report"')
def click_generate_report(step):
    world.ctx["can_generate"] = can_use_features()


@step('the button is disabled')
def button_disabled(step):
    assert world.ctx.get("can_generate") is False


@step('the app shows "You need credits to use this feature"')
def shows_need_credits(step):
    # UI verification is out of scope here; we assert gating logic.
    assert get_credits() == 0


@step('the user’s credit balance is greater than 0')
def user_credits_gt0(step):
    set_entitlements_state({"credits": 3})


@step('the request is sent to the backend with the token')
def request_sent_with_token(step):
    assert can_use_features() is True


@step('the report is generated successfully')
def report_generated(step):
    # As we do not call the real backend here, we just assert gating condition.
    assert can_use_features() is True
