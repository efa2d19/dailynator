from slack_sdk.web.async_slack_response import AsyncSlackResponse
from slack_sdk.web.async_client import AsyncWebClient

from src.db import Database

default_colors = ["#e8aeb7", "#b8e1ff", "#3c7a89", "#f4d06f", "#82aba1"]


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


async def start_cron():
    from functools import partial
    from apscheduler.triggers.cron import CronTrigger
    from main import scheduler
    from src.report import start_daily
    from src.db import Database

    db = Database()

    # Get current cron as str
    cron_list = await db.get_all_cron_with_channels()

    # Remove all existing triggers
    scheduler.remove_all_jobs()

    for channel_id, team_id, cron in cron_list:
        # Skip if cron not set
        if not cron:
            return

        # Split cron
        split_cron = cron.split(" ")

        # Filter stars
        split_cron = [unit if unit != "*" else None for unit in split_cron]

        # Collect kwargs for CronTrigger
        kwargs = dict(zip(['minute', 'hour', 'day', 'month', 'day_of_week'], split_cron))

        # Get an instance of CronTrigger
        cron_trigger = CronTrigger(**kwargs)

        # Schedule a job
        scheduler.add_job(
            func=partial(start_daily, channel_id=channel_id),  # Supply channel_id to start_daily
            trigger=cron_trigger,
            name=f"start_daily_{team_id}_{channel_id}"
        )

    # Start Async scheduler
    if not scheduler.state:
        scheduler.start()


async def is_dm_in_command(
        client: AsyncWebClient,
        channel_id: str,
        channel_name: str,
        user_id: str,
) -> bool:
    """
    Checks if command was used in DM

    :param client: AsyncWebClient instance
    :param channel_id: Slack channel id
    :param channel_name: Slack channel name
    :param user_id: Slack user id
    :return: True if command was used in DM else False
    """

    # Catch if command was used in DM
    if channel_name == "directmessage":  # noqa
        from src.block_kit import error_block

        await client.chat_postEphemeral(
            blocks=error_block(
                header_text="You can't use command in DMs",
                body_text="Open any available channel and send the command there",
            ),
            channel=channel_id,
            user=user_id,
        )
        return True
    return False


async def all_non_bot_members(
        client: AsyncWebClient,
        channel_id: str,
) -> list[str]:
    """
    Get all non bot members of the channel

    :param client: AsyncWebClient instance
    :param channel_id: Slack channel id
    :return: List of all non bot members
    """

    from asyncio import gather

    # Parse all members except bots
    raw_member_list = (await client.conversations_members(channel=channel_id))["members"]

    member_list = list()

    async def check_member_is_bot(
            user_id: str,
    ) -> None:
        """
        Wrapper for async check if member is bot and populating member list

        :param user_id: Slack channel id
        """
        if not (await client.users_info(user=user_id))["user"]["is_bot"]:
            member_list.append(user_id)

    async_tasks = list()

    for member in raw_member_list:
        async_tasks.append(
            check_member_is_bot(user_id=member)
        )

    await gather(*async_tasks)

    return member_list


async def create_user_with_real_name(
        client: AsyncWebClient,
        db_connection: Database,
        user_id: str,
        channel_id: str,
) -> None:
    """
    Wrapper for async creating new user in database w/ real_name

    :param client: ASyncWebClient instance
    :param db_connection: Database connection instance
    :param user_id: Slack user id
    :param channel_id: Slack channel id
    """

    real_name = (
            await client.users_info(
                user=user_id,
            )
        )["user"]["real_name"]

    await db_connection.create_user(
        user_id=user_id,
        daily_status=False,
        q_idx=0,
        main_channel_id=channel_id,
        real_name=real_name,
    )


async def create_multiple_user_with_real_name(
        client: AsyncWebClient,
        db_connection: Database,
        channel_id: str,
        member_list: list[str],
) -> None:
    """
    Create lots new users in database w/ real_name

    :param client: AsyncWebClient
    :param db_connection: Database connection instance
    :param channel_id: Slack channel id
    :param member_list: List of users to be created
    """

    from asyncio import gather
    async_tasks = list()

    for user in member_list:
        async_tasks.append(
            create_user_with_real_name(
                client=client,
                db_connection=db_connection,
                user_id=user,
                channel_id=channel_id,
            )
        )

    await gather(*async_tasks)
