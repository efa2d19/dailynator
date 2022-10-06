from src.db import Database


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


async def channel_subscribed_matcher(
     body: dict,
) -> bool:
    db = Database()

    if await db.check_channel_exist(
            channel_id=body["event"]["channel"],
    ):
        return True
    return False
