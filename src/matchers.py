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
