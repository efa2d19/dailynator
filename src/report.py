"""Utils for posting and collecting reports"""

from typing import Sequence
from slack_sdk.models.attachments import BlockAttachment
from slack_sdk.web.async_client import AsyncWebClient
from asyncio import gather

from src.block_kit import error_block
from src.db import Database


async def post_report(
        app: AsyncWebClient,
        db_connection: Database,
        channel: str,
        user_id: str,
        attachments: Sequence[BlockAttachment],
        username: str,
        icon_url: str,
) -> None:
    """
    Posts a report to the specified channel
        :param app: Async App instance
        :param db_connection: Database connection instance
        :param channel: Channel id
        :param user_id: Slack user id
        :param attachments: Sequence of attachments
        :param username: Custom username
        :param icon_url: Custom icon url
    """

    from os import getenv

    # Collect kwargs from params
    kwargs = dict()
    kwargs["channel"] = channel
    kwargs["text"] = f"<@{user_id}> has sent daily report"
    kwargs["attachments"] = attachments
    kwargs["username"] = username
    kwargs["icon_url"] = icon_url
    kwargs["icon_emoji"] = None

    # Parse emoji if USE_AVATARS is set to False
    if getenv("USE_AVATARS").lower() == "false":
        from src.utils import parse_emoji_list
        from random import choice

        # Parse emoji list
        emoji_list = await parse_emoji_list(app=app)
        # Choose random emoji
        kwargs["icon_emoji"] = choice(emoji_list)

    message_response = await app.chat_postMessage(**kwargs)

    await db_connection.write_daily_ts(
        ts=message_response["ts"],
        user_id=user_id,
    )


async def start_daily(
        channel_id: str,
) -> None:
    """
    Collect everything needed to start a daily meeting and start a new one
        :param channel_id: Slack channel id
    """

    from src.db import Database
    from src.block_kit import start_daily_block
    from main import app

    from datetime import datetime
    from zoneinfo import ZoneInfo

    db = Database()

    # Get team_id
    _, team_id = await db.get_channel_link_info(
        channel_id=channel_id,
    )

    # Get raw user_list
    raw_user_list = await db.get_all_users_by_channel_id(
        channel_id=channel_id,
    )

    # Check users DND status
    user_list = list()

    async def check_user_dnd_status(
            user_id: str,
    ) -> None:
        """
        Checks user DND status by comparing next dnd start timestamp with time aware datetime on the machine
            :param user_id: Slack user id
        """

        user_next_dnd_start = (
            await app.client.dnd_info(
                team_id=team_id,
                user=user_id,
            )
        )["next_dnd_start_ts"]

        user_tz = (
            await app.client.users_info(
                user=user_id,
            )
        )["user"]["tz"]

        # Get user's current offset-aware datetime
        user_dnd_start_aware = datetime.fromtimestamp(
            user_next_dnd_start,
            tz=ZoneInfo(key=user_tz),
        )

        # Get current offset-aware datetime
        time_now_aware = datetime.now().astimezone()

        if time_now_aware < user_dnd_start_aware:
            user_list.append(
                user_id
            )

    async_tasks = list()

    for user in raw_user_list:
        async_tasks.append(
            check_user_dnd_status(
                user_id=user,
            )
        )

    await gather(*async_tasks)

    # Get first question
    first_question, first_question_idx = await db.get_first_question(
        channel_id=channel_id,
    )

    if first_question is None:
        # Notify channel about missing questions
        await app.client.chat_postMessage(
            channel=channel_id,
            text=":x: No questions are available",
            blocks=error_block(
                header_text="No questions are available",
                body_text="Please, add question(s) via `/question_append <question>`",
            ),
        )

        return

    async def start_setup_daily(
            user_id: str,
    ) -> None:
        """
        Wrapper for async setting necessary field in database and deleting old answers if still present
            :param user_id: Slack user id
        """

        # Set user daily status & delete user's old idx
        await db.start_user_daily_status(
            user_id=user_id,
            q_idx=first_question_idx,
        )

        # Delete old user's answers from Redis
        await db.delete_user_answers(
            user_id=user_id,
        )

    async def post_first_question(
            user_id: str,
    ) -> None:
        """
        Wrapper for async posting the first question
            :param user_id: Slack user id
        """

        # Get channel_id
        user_im_channel = (
            await app.client.conversations_open(
                users=user_id,
            )
        )["channel"]["id"]

        # Send first question
        await app.client.chat_postMessage(
            channel=user_im_channel,
            text=":robot_face: Daily has started",
            blocks=start_daily_block(
                header_text=f"Hey, <@{user_id}>! :sun_with_face: ",
                body_text="*Daily time has come* :melting_face: ",
                first_question=first_question,
            ),
        )

    async_tasks_primary = list()
    async_tasks_secondary = list()

    for user in user_list:
        async_tasks_primary.append(
            start_setup_daily(
                user_id=user,
            )
        )

        async_tasks_secondary.append(
            post_first_question(
                user_id=user,
            )
        )

    # Update all necessary statuses at once
    await gather(*async_tasks_primary)

    # Post all DMs at once
    await gather(*async_tasks_secondary)
