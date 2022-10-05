async def im_matcher(
        message: dict,
) -> bool:
    if message["channel_type"] != "im":
        return False
    return True


async def thread_matcher(
        message: dict,
) -> bool:
    if (
            message["channel_type"] != "channel"
            or message.get("thread_ts", None) is None
    ):
        return False
    return True
