from dataclasses import replace

import app.dice.profile.workflow as workflow
from app.dice.profile.model import build_profile_payload


class _EvaluatePage:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []
        self.wait_calls = []

    def evaluate(self, script, *args):
        self.calls.append((script, args))
        if not self.results:
            return None
        return self.results.pop(0)

    def wait_for_load_state(self, *args, **kwargs):
        self.wait_calls.append((args, kwargs))


def test_completion_required_complete_detects_remaining_plus_items():
    page = _EvaluatePage("+Profile Photo 10%\nResume 25%\n+Employment Type 5%")

    assert workflow._completion_required_complete(page) is False


def test_completion_required_complete_accepts_completed_profile_items():
    page = _EvaluatePage("Profile Photo 10%\nResume 25%\nEmployment Type 5%\nSkills (at least 5) 5%")

    assert workflow._completion_required_complete(page) is True


def test_set_profile_visibility_noops_when_state_already_matches(monkeypatch):
    page = _EvaluatePage({"found": True, "changed": False, "state": True})
    prompts = []

    monkeypatch.setattr(workflow, "_profile_visibility_state", lambda _page: True)
    monkeypatch.setattr(workflow, "_confirm_profile_visibility_prompt", lambda *_args: prompts.append("prompted"))

    assert workflow._set_profile_visibility(page, True) is True
    assert prompts == []
    assert page.wait_calls == []


def test_set_profile_visibility_confirms_when_toggle_changes(monkeypatch):
    page = _EvaluatePage({"found": True, "changed": True, "state": False})
    prompts = []

    monkeypatch.setattr(workflow, "_profile_visibility_state", lambda _page: False)
    monkeypatch.setattr(workflow, "_confirm_profile_visibility_prompt", lambda *_args: prompts.append("prompted"))

    assert workflow._set_profile_visibility(page, False) is True
    assert prompts == ["prompted"]
    assert page.wait_calls


def test_profile_payload_contains_required_creation_sections():
    payload = build_profile_payload()

    assert payload.resume_path
    assert payload.profile_photo_path.endswith("profile_photo_placeholder.png")
    assert payload.headline
    assert len(payload.skills) >= 5
    assert payload.years_experience >= 1
    assert payload.work_experiences
    assert payload.educations
    assert payload.ideal_company_size
    assert payload.ideal_company_age


def test_profile_payload_visibility_can_be_overridden_for_runs(monkeypatch):
    monkeypatch.setenv("DICE_PROFILE_VISIBLE", "off")
    hidden_payload = build_profile_payload()

    monkeypatch.setenv("DICE_PROFILE_VISIBLE", "on")
    visible_payload = build_profile_payload()

    assert hidden_payload.profile_visible is False
    assert visible_payload.profile_visible is True


def test_profile_payload_can_be_replaced_with_explicit_visibility():
    payload = build_profile_payload()

    assert replace(payload, profile_visible=False).profile_visible is False
