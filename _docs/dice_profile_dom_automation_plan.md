# Dice Profile DOM Automation Plan

## Goal

Build a Playwright-driven workflow that can create and edit a Dice candidate profile by interacting with the live DOM instead of hardcoding page state or relying on manual steps.

Use a separate test account for this work:

- `TEST_USER_EMAIL`
- `TEST_USER_PASSWORD`

Do not change the current production Dice login while working through this plan.

The automation should be able to:

- Open the Dice profile area after login.
- Detect whether a profile already exists.
- Create a new profile when needed.
- Edit profile fields when data changes.
- Verify the saved state from the DOM after submit.
- Capture screenshots and HTML snapshots when selectors break.

## Current Repo Inputs

The repo already has the building blocks needed for this work:

- `app/dice/utils/login.py` handles sign-in.
- `app/dice/utils/utils.py` already contains resilient Playwright cleanup.
- `app/dice/utils/apply.py` and `app/dice/utils/extract.py` show the existing selector style and failure logging pattern.
- `_data_/Profiles/main_profile.py` is the source of truth for user data, job titles, and links.
- `app/dice/_experimental_/debug/` already stores HTML, screenshots, and button-target dumps that can be reused for selector discovery.
- Profile automation should read credentials from the test account only when this plan is executed.

One useful observed navigation target from debug output is the Dice profile area under:

- `https://www.dice.com/dashboard/profiles`

## Non-Goals

This plan does not cover:

- Rewriting the whole app around a different browser automation framework.
- Scraping unrelated candidate data from Dice.
- Bypassing anti-bot systems or hidden controls.
- Editing production data without an explicit review step.
- Using the user's existing Dice login for automation tests.

## Target Profile Data

Define a normalized internal profile model before writing automation.

Minimum fields:

- Name
- Email
- Phone number
- LinkedIn URL
- Website URL
- Portfolio URL
- Booking link
- Resume path
- Desired job titles
- Skills list
- Work authorization preferences
- Location / timezone

Recommended source of truth:

- `_data_/Profiles/main_profile.py`
- `.env` for secrets and personal URLs
- Optional profile JSON export for easier testing and diffing
- `TEST_USER_EMAIL` and `TEST_USER_PASSWORD` for the dedicated test account

## DOM Discovery Phase

Before automating edits, map the profile UI from the live DOM.

Steps:

1. Log into Dice with the existing login helper, but load only `TEST_USER_EMAIL` and `TEST_USER_PASSWORD`.
2. Navigate to the profile hub, then the candidate profile editor.
3. Capture:
   - Full-page screenshot.
   - `page.content()` HTML dump.
   - `page.accessibility.snapshot()` if available.
   - Button and input inventory from the current page.
4. Identify all editable controls:
   - Text inputs.
   - Textareas.
   - Select menus.
   - Multi-select chips.
   - Toggle switches.
   - Upload controls.
   - Save buttons.
5. Record stable selectors for each control.

Selector preference order:

- `data-testid`
- `aria-label`
- Semantic role locators
- Stable `href` or `name`
- Visible text
- CSS classes only as a last resort

## Create Flow

The create flow should handle first-time profile setup.

Suggested sequence:

1. Open the profile page.
2. Detect the absence of an existing profile.
3. Click the create/start button.
4. Fill required identity fields.
5. Fill contact and location fields.
6. Add links and resume.
7. Save the profile.
8. Re-open or refresh the page.
9. Confirm the saved values are visible in the DOM.

Hard requirements:

- Never submit until all required fields are confirmed present.
- Never assume a field was accepted just because typing succeeded.
- Confirm save via UI text, URL change, toast, or persisted field value.

## Edit Flow

The edit flow should modify an existing Dice profile without wiping other sections.

Suggested sequence:

1. Open the profile page.
2. Detect existing profile sections.
3. Enter edit mode for the specific section.
4. Update only the fields that differ from source data.
5. Preserve unchanged values.
6. Save the section.
7. Validate the updated values from the rendered DOM.

Important rule:

- Treat the profile as sectioned state, not one giant form.
- Update sections independently so a failure in one section does not corrupt the entire profile.

## Selector Strategy

Implement a selector registry rather than scattering raw selectors through the codebase.

Suggested structure:

- `app/dice/profile/selectors.py`
- `app/dice/profile/workflows.py`
- `app/dice/profile/validators.py`

Selector registry contents:

- Profile hub link
- Create profile button
- Edit section buttons
- Field locators by semantic name
- Save buttons
- Toast / success banners
- Error banners

Guidelines:

- Prefer locators that survive layout changes.
- Avoid long CSS chains.
- Avoid classes that look like generated framework output.
- Add a fallback list for every critical control.

## Form Handling

Handle each field type explicitly.

Text inputs:

- Use `fill()` when possible.
- Verify final value with `input_value()` or DOM text.

Textareas:

- Use `fill()` and confirm persisted text.

Selects:

- Prefer Playwright role-based dropdown interactions.
- Verify the selected option text.

Multi-select chips:

- Add missing chips only.
- Remove stale chips only after verifying they are safe to delete.

Uploads:

- Confirm the file exists before upload.
- Verify the file name appears after attachment.

Checkboxes / toggles:

- Read current checked state before clicking.
- Only toggle when the desired state differs.

## Validation

Every profile write should end with validation.

Validation checks:

- Field values match the expected model.
- Save confirmation appeared.
- No inline error message remains visible.
- A refresh still shows the updated values.

If validation fails:

- Capture a screenshot.
- Save HTML.
- Save the failing selector list.
- Stop the workflow for that section.

## Error Handling

The automation should fail safely.

Rules:

- If a selector is missing, collect debug data before retrying.
- Retry only on transient timing failures.
- Do not retry destructive actions indefinitely.
- If a section cannot be verified, mark the run as partial success.

Recommended debug bundle:

- Screenshot PNG
- Raw HTML
- Control inventory text file
- Error message with timestamp

## Implementation Milestones

1. Discovery
   - Log in and reach the Dice profile page.
   - Capture the DOM for the profile area.
   - Build the first selector map.

2. Read-only prototype
   - Read all editable fields.
   - Print them into a structured profile snapshot.
   - Confirm the snapshot matches the expected user data.

3. Edit prototype
   - Update one safe field.
   - Verify the value persists after save and refresh.

4. Full profile writer
   - Support all sections that matter for job applications.
   - Add per-section save and validation.

5. Maintenance harness
   - Add selector smoke tests.
   - Re-capture debug artifacts when Dice changes layout.

## Testing Plan

Use a staged approach:

- Headed mode first to observe the UI.
- Headless mode second to validate stability.
- Snapshot tests against saved HTML from `app/dice/_experimental_/debug/`.
- A small smoke test that verifies the profile page still exposes the expected controls.

Suggested test cases:

- Existing profile can be opened.
- Missing profile can be created.
- One text field can be edited and verified.
- A multi-select field can be updated without duplicate entries.
- Save failure produces a debug bundle.

## Maintenance Plan

Dice UI will change. Keep the automation maintainable by:

- Centralizing selectors.
- Keeping debug artifacts for failed runs.
- Re-checking the profile page whenever Dice changes layout.
- Using page-object style helpers for profile sections.
- Updating the selector registry before changing workflow code.

## Proposed Deliverable Structure

- `app/dice/profile/`
  - `selectors.py`
  - `workflow.py`
  - `validators.py`
  - `debug.py`
- `_docs/dice_profile_dom_automation_plan.md`
- Optional profile selector fixture files under `app/dice/_experimental_/debug/`

## Success Criteria

The work is done when:

- The automation can open the Dice profile page reliably.
- It can create a profile on a fresh account or detect an existing one.
- It can edit at least one real profile section end-to-end.
- It verifies the saved values after submit.
- It produces usable debug output when the page changes.
