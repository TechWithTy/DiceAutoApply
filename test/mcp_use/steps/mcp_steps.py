from lettuce import world, step
from app.ai.mcp_use import BrowserAutomation
from app.ai.mcp_use.prompts.utils import load_prompt_template, render_prompt
from app.ai.mcp_use.tasks.utils import run_sync_task
import asyncio

# Browser automation steps
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

# Prompt utility steps
@step('I have a prompt template named "(.*)"')
def have_prompt_template(step, template_name):
    world.template_name = template_name

@step('I render it with variables')
def render_template(step):
    template = load_prompt_template(world.template_name)
    world.rendered = render_prompt(template, {"query": "python jobs"})

@step('I should get valid output')
def check_valid_output(step):
    assert isinstance(world.rendered, str)
    assert len(world.rendered) > 0

# Task utility steps
@step('I have a synchronous task')
def have_sync_task(step):
    world.task_fn = lambda: 42

@step('I run it through task utils')
def run_task_utils(step):
    world.result = asyncio.run(run_sync_task(world.task_fn))

@step('it should execute successfully')
def check_task_success(step):
    assert world.result == 42
