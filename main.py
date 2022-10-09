from asyncio import run

from os import getenv
from dotenv import load_dotenv  # TODO: remove when dockerfile is ready
from logging import basicConfig, DEBUG, ERROR

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.utils import start_cron

load_dotenv()  # TODO: remove when dockerfile is ready

# Establish logging level
basicConfig(level=DEBUG if getenv("DEVELOPMENT", None) else ERROR)

# Async App instance
app = AsyncApp()

# Async scheduler instance
scheduler = AsyncIOScheduler()


async def main():
    import src.listeners as listeners
    from src.db import Database

    # Create database connection
    await Database().connect()

    # Get SocketHandler
    handler = AsyncSocketModeHandler(app=listeners.app)

    # Initialize cron
    await start_cron()

    # Start server
    await handler.start_async()


if __name__ == "__main__":
    run(main())

# TODO: add logging everywhere (+ write to a file)
# TODO: add change my report button in end daily block
# TODO: add use last, skip, out of office in start daily block
