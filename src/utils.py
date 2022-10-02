from slack_sdk.web.async_slack_response import AsyncSlackResponse
from slack_sdk.web.async_client import AsyncWebClient


async def parse_emoji_list(
        app: AsyncWebClient,
) -> list[str]:
    """
    Returns a list of emoji names

    :param app: App instance
    :return: List of all emoji names
    """

    emoji_r: AsyncSlackResponse = await app.emoji_list()
    return list(emoji_r.data.get("emoji", {':+1:'}).keys())
