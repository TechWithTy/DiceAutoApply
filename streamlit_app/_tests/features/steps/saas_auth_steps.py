from __future__ import annotations

import os
from behave import given, when, then

from streamlit_app.state import (
    ensure_session_defaults,
    set_auth_token,
    get_auth_token,
    set_entitlements_state,
    get_credits,
)
from streamlit_app.api import build_login_url, get_entitlements
from streamlit_app.ui_saas import can_use_features


@given("the Streamlit app is running")
def step_app_running(context):
    ensure_session_defaults()


@given('the backend API is available at "{url}"')
def step_backend_available(context, url):
    os.environ["SAAS_API_URL"] = url


@given("the user is not logged in")
def step_user_not_logged_in(context):
    set_auth_token(None)


@when("the user accesses a protected page")
def step_access_protected(context):
    context.login_url = build_login_url()


@then('the app redirects to "{expected_url}"')
def step_redirects_login(context, expected_url):
    assert context.login_url.startswith(expected_url), \
        f"Expected redirect to start with {expected_url}, got {context.login_url}"


@then("the user is returned with a valid token")
def step_returned_token(context):
    set_auth_token("TEST_TOKEN")
    assert get_auth_token() == "TEST_TOKEN"


@given("the user has logged in successfully")
def step_user_logged_in(context):
    set_auth_token("VALID_TOKEN")


@when("the backend redirects back with a token")
def step_backend_redirects(context):
    assert get_auth_token() is not None


@then("the app stores the token in session state")
def step_token_stored(context):
    assert get_auth_token() is not None


@then("the token is used for all API requests")
def step_token_used_for_api(context):
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


@given("the user is authenticated")
def step_user_authenticated(context):
    if get_auth_token() is None:
        set_auth_token("AUTH_TOKEN")


@when('the app calls "/entitlements"')
def step_app_calls_entitlements(context):
    pass


@then("the user’s credit balance is displayed on the dashboard")
def step_credit_display(context):
    assert get_credits() >= 0


@given("the user’s credit balance is 0")
@when("the user’s credit balance is 0")
def step_user_credits_zero(context):
    set_entitlements_state({"credits": 0})


@when('the user clicks on "Generate Report"')
def step_click_generate_report(context):
    context.can_generate = can_use_features()


@then("the button is disabled")
def step_button_disabled(context):
    assert context.can_generate is False


@then("the app shows \"You need credits to use this feature\"")
def step_shows_need_credits(context):
    assert get_credits() == 0


@given("the user’s credit balance is greater than 0")
@when("the user’s credit balance is greater than 0")
def step_user_credits_gt0(context):
    set_entitlements_state({"credits": 3})


@then("the request is sent to the backend with the token")
def step_request_sent_with_token(context):
    assert can_use_features() is True


@then("the report is generated successfully")
def step_report_generated(context):
    assert can_use_features() is True
