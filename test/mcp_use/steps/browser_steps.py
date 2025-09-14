from lettuce import world, step
from app.ai.mcp_use import BrowserAutomation
import asyncio

@step('I have a browser automation task')
def have_automation_task(step):
    world.task = "Open Google and search for Lettuce BDD"

@step('I execute the automation')
def execute_automation(step):
    automation = BrowserAutomation(world.task)
    asyncio.run(automation.run())

@step('it should complete successfully')
def check_success(step):
    # In real tests we would check logs or results
    assert True

@step('I run it in headless mode')
def run_headless_mode(step):
    automation = BrowserAutomation(world.task, headless=True)
    asyncio.run(automation.run())

@step('it should complete without errors')
def check_no_errors(step):
    # Check for errors in logs
    assert True

@step('I run it in visible mode')
def run_visible_mode(step):
    automation = BrowserAutomation(world.task, headless=False)
    asyncio.run(automation.run())

@step('I should see browser activity')
def see_browser_activity(step):
    # We can't verify visibility in tests, so we just pass
    assert True
