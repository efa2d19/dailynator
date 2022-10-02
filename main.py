from asyncio import run

from dotenv import load_dotenv  # TODO: remove when dockerfile is ready
from logging import basicConfig, DEBUG

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler


basicConfig(level=DEBUG)  # TODO: change later

load_dotenv()  # TODO: remove when dockerfile is ready

app = AsyncApp()


async def main():
    import src.listeners as listeners

    # Get SocketHandler
    handler = AsyncSocketModeHandler(app=listeners.app)

    # Start server
    await handler.start_async()


if __name__ == "__main__":
    run(main())
