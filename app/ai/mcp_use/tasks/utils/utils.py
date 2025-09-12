import asyncio
from typing import Callable, Any, Coroutine


def run_sync_task(task_fn: Callable[[], Any]):
    """Run a synchronous task in a thread pool."""
    return asyncio.to_thread(task_fn)


async def run_async_task(task_fn: Coroutine[Any, Any, Any]):
    """Run an asynchronous task with proper event loop handling."""
    return await task_fn


def handle_task_errors(func: Callable):
    """Decorator to handle common task errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Task failed: {str(e)}")
            # Add error reporting/handling logic here
            raise
    return wrapper


def log_task_execution(task_name: str, duration: float, success: bool):
    """Log task execution details."""
    print(f"Task '{task_name}' {'succeeded' if success else 'failed'} "
          f"in {duration:.2f} seconds")
