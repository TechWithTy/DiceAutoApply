# Headless Mode Troubleshooting for Dice Auto Apply

## Common Issues

- **Easy Apply Button Not Found**: In headless mode, the Easy Apply button may be hidden or not rendered due to anti-bot detection or UI differences.
- **Timing/Race Conditions**: Headless browsers are much faster, so elements may not be ready when the script tries to interact.
- **Headless Detection**: Some sites change their UI or hide elements when they detect headless browsers.
- **Return Value Errors**: If a function like `write_job_titles_to_file` returns `None` on failure but the main code expects a tuple, you may see errors like `cannot unpack non-iterable NoneType object`.

## Debugging Steps

1. **Test in Headed Mode**
   - Set `headless=False` in Playwright to see if the UI behaves differently.
   - If Easy Apply works in headed but not headless, it's likely anti-bot logic.

2. **Set a Realistic User Agent**
   - Use the same custom user agent string as your working script.

3. **Simulate Human Interaction**
   - Add delays (`time.sleep()`), scrolling, or mouse movements before searching for the Easy Apply button.
   - Use `page.mouse.move()` or `page.keyboard.press('PageDown')`.

4. **Use Stealth Techniques**
   - Set viewport, timezone, geolocation, and other context options to mimic a real user.
   - Consider using stealth plugins/packages if available.

5. **Add Visual Debugging**
   - Take screenshots with `page.screenshot(path="debug.png")` before/after searching for the button to inspect the DOM visually.

6. **Improve Error Handling**
   - Ensure all utility functions return consistent types (e.g., always return a tuple from `write_job_titles_to_file`).
   - Add logging for every failure and skipped job.

## Example: Making Headless Mode More Human

```python
custom_user_agent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) ..."
context = browser.new_context(user_agent=custom_user_agent, viewport={"width": 1280, "height": 800}, timezone_id="America/Denver")
page = context.new_page()
page.goto(url)
page.mouse.move(100, 100)
page.keyboard.press('PageDown')
time.sleep(2)
```

## What To Do If All Else Fails
- Run in headed mode for critical jobs.
- Periodically review and update selectors.
- Watch for changes in Dice's anti-bot logic and UI.
- Consider reporting issues and sharing logs/screenshots for further help.

---
**Last updated:** 2025-05-15
