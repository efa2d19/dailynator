from src.db import Database


async def im_matcher(
        message: dict,
) -> bool:
    """
    WS matcher for DMs

    :param message: message object from WS
    :return: True if DM else False
    """

    if message["channel_type"] != "im":
        return False
    return True


async def thread_matcher(
        message: dict,
) -> bool:
    """
    WS matcher for messages in threads

    :param message: message object from WS
    :return: True if thread else False
    """

    if (
            message["channel_type"] != "channel"
            or message.get("thread_ts", None) is None
    ):
        return False
    return True


async def events_channel_subscribed_matcher(
     body: dict,
) -> bool:
    """
    WS matcher for checking if event happened in subscribed channel

    :param body: body object from WS
    :return: True if event happened in subscribed channel
    """

    db = Database()

    if await db.check_channel_exist(
            channel_id=body["channel_id"],
    ):
        return True
    return False


async def commands_channel_subscribed_matcher(
     body: dict,
) -> bool:
    """
    WS matcher for checking if command was sent in subscribed channel

    :param body: body object from WS
    :return: True if command was sent in subscribed channel
    """

    db = Database()

    if await db.check_channel_exist(
            channel_id=body["event"]["channel"],
    ):
        return True
    return False


async def threads_channel_subscribed_matcher(
        message: dict,
):
    """
    WS matcher for checking if message was sent in subscribed channel \n
    (for message listeners)

    :param message: message object from WS
    :return: True if message was sent in subscribed channel
    """

    db = Database()

    if await db.check_channel_exist(
            channel_id=message["channel"],
    ):
        return True
    return False
