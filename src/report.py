from slack_sdk.web.async_client import AsyncWebClient


async def post_report(
        app: AsyncWebClient,
        channel: str,
        text: str,
        username: str,
        icon_url: str,
) -> None:
    """
    Posts a report to the specified channel

    :param app: Async App instance
    :param channel: Channel id
    :param text: Body of the report
    :param username: Custom username
    :param icon_url: Custom icon url
    """

    from os import getenv

    # Collect kwargs from params
    kwargs = dict()
    kwargs["channel"] = channel
    kwargs["text"] = text
    kwargs["username"] = username
    kwargs["icon_url"] = icon_url
    kwargs["icon_emoji"] = None

    # Parse emoji if USE_AVATARS is set to False
    if getenv("USE_AVATARS").lower() == "false":
        from src.utils import parse_emoji_list
        from random import choice

        # Parse emoji list
        emoji_list = await parse_emoji_list(app)
        # Choose random emoji
        kwargs["icon_emoji"] = choice(emoji_list)

    await app.chat_postMessage(**kwargs)


async def start_daily():
    from src.db import redis_instance
    from main import app

    # Get user_list
    user_list: list[str] = list(map(bytes.decode, await redis_instance.lrange("users", 0, -1)))

    # Get first question
    first_question: list[str] = list(map(bytes.decode, await redis_instance.lrange("questions", 0, 0)))

    for user in user_list:
        # Set user daily status
        await redis_instance.set(f"{user}_started", "1")

        # Get channel_id
        user_im_channel = (await app.client.conversations_open(users=user))["channel"]["id"]

        # Send first question
        await app.client.chat_meMessage(
            channel=user_im_channel,
            text=first_question[0],
        )
