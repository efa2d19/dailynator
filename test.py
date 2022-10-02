import asyncio
import os
from dotenv import load_dotenv  # TODO: remove this when dockerfile is ready
from slack_sdk.socket_mode.websockets import SocketModeClient
import logging

from slack_sdk.web.async_client import AsyncWebClient

from src.ws import *
from src.report import dispatch_im_listeners


load_dotenv()  # TODO: remove this when dockerfile is ready

logging.basicConfig(level=logging.DEBUG if os.getenv("DEVELOPMENT") else logging.ERROR)


async def main():
    web_client = AsyncWebClient(
        token=os.environ.get("SLACK_BOT_TOKEN")  # xoxb-xxxx
    )

    main_client = SocketModeClient(
        app_token=os.getenv("SLACK_APP_TOKEN"),  # xapp-xxxx
        web_client=web_client,
    )

    # Add a new listener to receive messages from Slack
    main_client.socket_mode_request_listeners.append(channel_append_listener)
    main_client.socket_mode_request_listeners.append(channel_pop_listener)
    main_client.socket_mode_request_listeners.append(join_channel_listener)
    main_client.socket_mode_request_listeners.append(leave_channel_listener)
    main_client.socket_mode_request_listeners.append(refresh_users_listener)
    main_client.socket_mode_request_listeners.append(questions_listener)
    main_client.socket_mode_request_listeners.append(question_append_listener)
    main_client.socket_mode_request_listeners.append(question_pop_listener)

    # Start asking stuff
    await dispatch_im_listeners(main_client=main_client, web_client=web_client)

    # Establish a WebSocket connection to the Socket Mode servers
    await main_client.connect()
    # Just not to stop this process
    await asyncio.sleep(float("inf"))


if __name__ == '__main__':
    asyncio.run(main())
