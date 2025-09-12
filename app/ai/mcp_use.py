import asyncio
from dotenv import load_dotenv
from browser_use import Agent
from langchain_openai import ChatOpenAI


class BrowserAutomation:
    def __init__(self, task: str, model: str = "gpt-4.1-mini", headless: bool = True):
        self.task = task
        self.model = model
        self.headless = headless

    async def run(self):
        load_dotenv()
        agent = Agent(
            task=self.task,
            llm=ChatOpenAI(model=self.model),
            headless=self.headless,
        )
        await agent.run()


def run_automation(task: str, model: str = "gpt-4.1-mini", headless: bool = True):
    automation = BrowserAutomation(task, model, headless)
    asyncio.run(automation.run())
