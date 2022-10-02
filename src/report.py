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
