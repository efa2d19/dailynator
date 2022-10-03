from slack_sdk.web.async_slack_response import AsyncSlackResponse
from slack_sdk.web.async_client import AsyncWebClient

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
    from apscheduler.triggers.cron import CronTrigger
    from main import scheduler

    from src.report import start_daily
    from src.db import get_all_cron

    # Get current cron as str
    cron_list = get_all_cron()

    # Remove all existing triggers
    scheduler.remove_all_jobs()

    for idx, cron in enumerate(cron_list):

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
            func=start_daily,
            trigger=cron_trigger,
            name=f"start_daily_{idx}"
        )

    # Start Async scheduler
    if not scheduler.state:
        scheduler.start()
