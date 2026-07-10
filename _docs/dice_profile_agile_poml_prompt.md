# Dice Profile Agile POML Prompt

Use this prompt to drive implementation of Dice profile creation and editing through DOM automation.

## Objective

Build a Playwright-based workflow that can create, edit, validate, and maintain a Dice candidate profile by interacting with live DOM elements across the relevant pages and sections.

Use a dedicated test account for this work:

- `TEST_USER_EMAIL`
- `TEST_USER_PASSWORD`

Do not modify or depend on the current production Dice login for this prompt.

## Scope

The automation must support:

- Profile discovery after login.
- First-time profile creation.
- Existing profile editing.
- Field-level validation.
- Debug capture when selectors fail.
- Repeatable maintenance when Dice changes its UI.

## Repo Areas

Use these folders and files as the source of truth:

- `app/dice/utils/login.py`
- `app/dice/utils/utils.py`
- `app/dice/utils/apply.py`
- `app/dice/utils/extract.py`
- `app/dice/utils/profile_to_url.py`
- `app/dice/_experimental_/headless_test.py`
- `app/dice/_experimental_/debug/`
- `_data_/Profiles/main_profile.py`
- `_data_/Filters/diceFilterSettings.py`
- `_docs/dice_profile_dom_automation_plan.md`

## Operating Rules

- Work one task at a time.
- Keep selectors centralized.
- Prefer semantic locators over brittle CSS.
- Verify every write by reading back the DOM.
- Capture screenshots and HTML when a step fails.
- Do not mark a task complete until validation passes.

## Agile Board

### To Do

- [ ] Discover the Dice profile DOM after login.
- [ ] Map the profile hub, create screen, and edit sections.
- [ ] Identify stable selectors for inputs, buttons, and save controls.
- [ ] Create a selector registry module for profile pages.
- [ ] Build a read-only profile inspector that extracts visible values.
- [ ] Implement first-time profile creation flow.
- [ ] Implement edit flow for existing profiles.
- [ ] Add validation after every save.
- [ ] Add debug bundle generation for selector failures.
- [ ] Add smoke tests for profile page stability.

### In Progress

- [ ] Run only the currently active task here.
- [ ] Keep this section limited to one item at a time.
- [ ] Update the task status before moving to the next step.

### Complete

- [ ] Move tasks here only after:
  - The DOM step works in headed mode.
  - The same step works in headless mode.
  - The saved value is verified after refresh.
  - Failure artifacts are captured when a retry is needed.

## Workflow Prompt

You are implementing Dice profile DOM automation inside this repository.

Follow this sequence:

1. Sign in using the existing login utility, but load credentials only from `TEST_USER_EMAIL` and `TEST_USER_PASSWORD`.
2. Navigate to the Dice profile area.
3. Inspect the DOM and discover the candidate profile controls.
4. Record stable selectors in a dedicated profile selector module.
5. Build a read-only profile snapshot to confirm the visible values.
6. Implement create and edit flows as separate sectioned workflows.
7. Validate each field after save and after refresh.
8. Emit debug artifacts whenever a selector, save, or verification step fails.
9. Update the agile board status as work progresses.

## Folder Plan

### `app/dice/profile/`

- `selectors.py`
  - All stable selectors for profile hub, create, edit, save, and confirm states.
- `workflow.py`
  - High-level create/edit orchestration.
- `validators.py`
  - DOM assertions and post-save verification.
- `debug.py`
  - Screenshot, HTML, and selector inventory capture helpers.

### `app/dice/_experimental_/debug/`

- Store failing HTML snapshots.
- Store screenshots.
- Store control inventories.
- Store any selector diff output.

### `_data_/Profiles/`

- Treat this as the profile data source.
- Keep the automation reading from `main_profile.py` or a normalized export.

### `_docs/`

- Keep the implementation plan and prompt documents here.
- Update this prompt if the task flow changes.

## Field Coverage

Support these fields where Dice exposes them:

- Identity: name, headline, summary, title
- Contact: email, phone, location
- Links: LinkedIn, website, portfolio, booking link
- Work preferences: location, remote preference, authorization
- Resume / attachment upload
- Skills / tags / keywords
- Section-specific profile content

## Definition of Done

A task is complete only when:

- The target section can be opened reliably.
- The correct field values are entered or updated.
- The DOM shows the saved values after submit.
- A page refresh still shows the same values.
- Any failure produces debug artifacts.
- The task is moved from `In Progress` to `Complete`.

## Example Execution Order

1. Discover controls.
2. Add selectors.
3. Build read-only snapshot.
4. Create profile flow.
5. Edit profile flow.
6. Validate and harden.
7. Add tests.

## Notes

- If Dice changes layout, update `selectors.py` first.
- If a field is hidden behind a section toggle, add an explicit expand step.
- If an upload fails, confirm the file path and file input visibility before retrying.
- Keep the prompt current with the actual repository layout.
- This prompt must not be used with the user's existing Dice credentials.
- Any test run should use the separate test account only.
