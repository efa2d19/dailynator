import asyncio
import logging

from dotenv import load_dotenv
from logging import basicConfig, DEBUG

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.web.async_client import AsyncWebClient

from src.db import redis_instance
from src.report import post_report

basicConfig(level=DEBUG)

load_dotenv()

app = AsyncApp()


async def main():
    import src.listeners as listeners

    # Get SocketHandler
    handler = AsyncSocketModeHandler(app=listeners.app)

    # Start server
    handler = await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
