from slack_bolt.context.async_context import AsyncAck, AsyncWebClient

from src.utils import is_dm_in_command, all_non_bot_members, create_multiple_user_with_real_name, is_not_subscribed
from src.block_kit import success_block, error_block
from src.matchers import im_matcher, thread_matcher
from src.db import Database

from main import app
from asyncio import gather


@app.command(
    "/channel_append",
)
async def channel_append_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
) -> None:
    """
    Listen for channel_append command in channel bot was added to \n
    Exits if command was send in DM or channel has been already subscribed
    """

    await ack()

    # Catch if command was used in DM
    if await is_dm_in_command(
            client=client,
            channel_name=body["channel_name"],
            user_id=body["user_id"],
    ):
        return

    db = Database()

    # If where aren't channels or channel is not in the list - add channel to the list
    if not await db.check_channel_exist(
            channel_id=body["channel_id"]
    ):
        # Write channel
        await db.add_channel(
            channel_id=body["channel_id"],
            team_id=body["team_id"],
            channel_name=body["channel_name"],
        )

        # Post message on success
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            text=":white_check_mark: Channel has been successfully subscribed",
            blocks=success_block(
                header_text="Channel has been successfully subscribed",
            ),
            user=body["user_id"],
        )

        member_list = await all_non_bot_members(
            client=client,
            channel_id=body["channel_id"],
        )

        # Parse user to db
        await create_multiple_user_with_real_name(
            client=client,
            db_connection=db,
            channel_id=body["channel_id"],
            member_list=member_list,
        )

        # Post a message on success
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            text=":white_check_mark: All members was successfully parsed",
            blocks=success_block(
                header_text="All members was successfully parsed",
            ),
            user=body["user_id"],
        )
        return

    # Trash talk if bot is already in the channel
    await client.chat_postEphemeral(
        channel=body["channel_id"],
        text=":white_check_mark: Channel already has been added",
        blocks=success_block(
            header_text="Channel already has been added",
        ),
        user=body["user_id"],
    )


@app.command(
    "/channel_pop",
)
async def channel_pop_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    """
    Listen for channel_pop command in channel bot was added to \n
    Exits if command was send in DM or channel has been already unsubscribed
    """

    await ack()

    # Catch if command was used in DM
    if await is_dm_in_command(
            client=client,
            channel_name=body["channel_name"],
            user_id=body["user_id"],
    ):
        return

    db = Database()

    # If the channel is in the list - delete it from the list
    if await db.check_channel_exist(
            channel_id=body["channel_id"],
    ):
        # Delete all members except for bots
        await db.delete_users_by_main_channel(
            channel_id=body["channel_id"],
        )

        await client.chat_postEphemeral(
            channel=body["channel_id"],
            text=":white_check_mark: All members was successfully unsubscribed",
            blocks=success_block(
                header_text="All members was successfully unsubscribed",
            ),
            user=body["user_id"],
        )

        # Unsubscribe from the channel
        await db.delete_channel(
            channel_id=body["channel_id"],
        )

        await client.chat_postEphemeral(
            channel=body["channel_id"],
            text=":white_check_mark: Channel has been successfully unsubscribed",
            blocks=success_block(
                header_text="Channel has been successfully unsubscribed",
            ),
            user=body["user_id"],
        )

        return

    # Trash talk if bot is already left
    await client.chat_postEphemeral(
        channel=body["channel_id"],
        text=":white_check_mark: Channel already has been successfully unsubscribed",
        blocks=success_block(
            "Channel already has been successfully unsubscribed",
        ),
        user=body["user_id"],
    )


@app.event(
    "member_joined_channel",
)
async def join_channel_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    """
    Listen for user's joining subscribed channels \n
    """

    await ack()

    # Check if got any subtype
    if body["event"].get("subtype"):
        return

    db = Database()

    # Check if not subscribed
    if await is_not_subscribed(
            client=client,
            db_connection=db,
            channel_id=body["event"]["channel"],
            user_id=body["event"]["user"],
    ):
        return

    # Parse user's real_name and creator_id
    real_name = (
        await client.users_info(
            user=body["event"]["user"])
    )["user"]["real_name"]

    # Add user to the user_list
    await db.create_user(
        user_id=body["event"]["user"],
        daily_status=False,
        q_idx=0,
        main_channel_id=body["event"]["channel"],
        real_name=real_name,
    )

    # Parse channel's creator_id
    creator_id = (
        await client.conversations_info(
            channel=body["event"]["channel"])
    )["channel"]["creator"]

    # Send a nice notification to the creator of the channel
    await client.chat_postEphemeral(
        channel=body["event"]["channel"],
        text=f":white_check_mark: {real_name} joined and was successfully parsed",
        blocks=success_block(
            f"<@{body['event']['user']}> joined and was successfully parsed",
        ),
        user=creator_id,
    )


@app.event(
    "member_left_channel",
)
async def leave_channel_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    """
    Listen for user's leaving subscribed channels \n
    """

    if body["event"].get("subtype"):
        return

    await ack()

    db = Database()

    # Check if not subscribed
    if await is_not_subscribed(
        client=client,
        db_connection=db,
        channel_id=body["event"]["channel"],
        user_id=body["event"]["user"],
    ):
        return

    await db.delete_user(
        user_id=body["event"]["user"],
    )

    # Parse user's real_name and creator_id
    real_name = (
        await client.users_info(
            user=body["event"]["user"])
    )["user"]["real_name"]

    creator_id = (
        await client.conversations_info(
            channel=body["event"]["channel"])
    )["channel"]["creator"]

    # Send a nice notification to the creator
    await client.chat_postEphemeral(
        channel=body["event"]["channel"],
        text=f":white_check_mark: {real_name} left and was successfully unsubscribed",
        blocks=success_block(
            header_text=f"<@{body['event']['user']}> left and was successfully unsubscribed",
        ),
        user=creator_id,
    )


@app.command(
    "/refresh_users",
)
async def refresh_users_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    """
    Listen for command refresh_users in subscribed channels \n
    Exits if command was send in DM
    """

    await ack()

    # Catch if command was used in DM
    if await is_dm_in_command(
            client=client,
            channel_name=body["channel_name"],
            user_id=body["user_id"],
    ):
        return

    db = Database()

    # Check if not subscribed
    if await is_not_subscribed(
        client=client,
        db_connection=db,
        channel_id=body["channel_id"],
        user_id=body["user_id"],
    ):
        return

    # Delete all members from database
    await db.delete_users_by_main_channel(
        channel_id=body["channel_id"],
    )

    member_list = await all_non_bot_members(
        client=client,
        channel_id=body["channel_id"],
    )

    # Parse user to db
    await create_multiple_user_with_real_name(
        client=client,
        db_connection=db,
        channel_id=body["channel_id"],
        member_list=member_list,
    )

    # Notification to the user
    await client.chat_postEphemeral(
        channel=body["channel_id"],
        text=":white_check_mark: All members have been successfully parsed",
        blocks=success_block(
            header_text="All members have been successfully parsed",
        ),
        user=body["user_id"],
    )


@app.command(
    "/questions",
)
async def questions_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    """
    Listen for command questions in subscribed channels \n
    Exits if command was send in DM
    """

    await ack()

    # Catch if command was used in DM
    if await is_dm_in_command(
            client=client,
            channel_name=body["channel_name"],
            user_id=body["user_id"],
    ):
        return

    db = Database()

    # Check if not subscribed
    if await is_not_subscribed(
            client=client,
            db_connection=db,
            channel_id=body["channel_id"],
            user_id=body["user_id"],
    ):
        return

    question_info = await db.get_all_questions(
        channel_id=body["channel_id"],
    )

    question_list = [question for question, idx in question_info if question]

    if not question_list:
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            text=":x: None question available",
            blocks=error_block(
                header_text="None question available",
                body_text="Add some with\n`/question_append <your_daily_question>`",
            ),
            user=body["user_id"],
        )
        return

    from src.block_kit import question_list_block

    # Send user list to user
    await client.chat_postEphemeral(
        text="Question list has arrived",
        blocks=question_list_block(
            question_list=question_list,
        ),
        channel=body["channel_id"],
        user=body["user_id"],
    )


@app.command(
    "/question_append",
)
async def question_append_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    """
    Listen for command question_append in subscribed channels \n
    Exits if command was send in DM
    """

    await ack()

    # Catch if command was used in DM
    if await is_dm_in_command(
            client=client,
            channel_name=body["channel_name"],
            user_id=body["user_id"],
    ):
        return

    db = Database()

    # Check if not subscribed
    if await is_not_subscribed(
            client=client,
            db_connection=db,
            channel_id=body["channel_id"],
            user_id=body["user_id"],
    ):
        return

    # If user specified the question add it and notify the user
    if body["text"]:
        await db.add_question(
            channel_id=body["channel_id"],
            question=body["text"],
        )

        await client.chat_postEphemeral(
            channel=body["channel_id"],
            text=":white_check_mark:  Your question has been added to the list",
            blocks=success_block(
                header_text="Your question has been added to the list",
            ),
            user=body["user_id"],
        )
        return

    # Else send the instructions
    await client.chat_postEphemeral(
        channel=body["channel_id"],
        text=":x: Question wasn't entered",
        blocks=error_block(
            header_text="Question wasn't entered",
            body_text="Enter the question after the command\nExample:\n `/question_append <your_question>`",
        ),
        user=body["user_id"],
    )


@app.command(
    "/question_pop",
)
async def question_pop_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    """
    Listen for command question_pop in subscribed channels \n
    Exits if command was send in DM
    """

    await ack()

    # Catch if command was used in DM
    if await is_dm_in_command(
            client=client,
            channel_name=body["channel_name"],
            user_id=body["user_id"],
    ):
        return

    db = Database()

    # Check if not subscribed
    if await is_not_subscribed(
            client=client,
            db_connection=db,
            channel_id=body["channel_id"],
            user_id=body["user_id"],
    ):
        return

    # If user specified the question add it and notify the user
    if body["text"]:
        if (
                not body["text"].isdigit()
                or len((
                    await db.get_all_questions(
                        channel_id=body["channel_id"],
                    ))
                ) < int(body["text"])
        ):
            await client.chat_postEphemeral(
                channel=body["channel_id"],
                text=":x: Not valid question index",
                blocks=error_block(
                    header_text="Not valid question index",
                    body_text="Enter the index of the question you want to delete\nExample: `/question_pop 1` ",
                ),
                user=body["user_id"],
            )

            return

        # Delete question from database
        await db.delete_question(
            question_rowid=int(body["text"]),
            channel_id=body["channel_id"],
        )

        # Notify user
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            text=":white_check_mark: Your question has been removed from the daily bot",
            blocks=success_block(
                header_text="Your question has been removed from the daily bot",
            ),
            user=body["user_id"],
        )

        return

    # Else send the instructions
    await client.chat_postEphemeral(
        channel=body["channel_id"],
        text=":x: Index wasn't entered'",
        blocks=error_block(
            header_text="Index wasn't entered",
            body_text="Enter the index after the command\nExample: `/question_pop 1`",
        ),
        user=body["user_id"],
    )


@app.command(
    "/cron",
)
async def cron_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    """
    Listen for command cron in subscribed channels \n
    Exits if command was send in DM
    """

    await ack()

    # Catch if command was used in DM
    if await is_dm_in_command(
            client=client,
            channel_name=body["channel_name"],
            user_id=body["user_id"],
    ):
        return

    db = Database()

    # Check if not subscribed
    if await is_not_subscribed(
            client=client,
            db_connection=db,
            channel_id=body["channel_id"],
            user_id=body["user_id"],
    ):
        return

    # Validate user input
    try:
        from apscheduler.triggers.cron import CronTrigger

        # Raise an exception if cron wasn't specified
        if not body["text"]:
            raise ValueError

        # Validate specified cron
        CronTrigger().from_crontab(body["text"])
    except ValueError:
        # Notify user about invalid cron
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            text=":x: Incorrect cron",
            blocks=error_block(
                header_text="Incorrect cron",
                body_text="Check cron on <https://crontab.guru/|CrontabGuru>",
            ),
            user=body["user_id"],
        )
        return

    # Set specified cron to current channel
    await db.update_cron_by_channel_id(
        channel_id=body["channel_id"],
        cron=body["text"],
    )

    from src.utils import start_cron

    # Update CronTrigger in scheduler
    await start_cron()

    # Post notification on success
    await client.chat_postEphemeral(
        channel=body["channel_id"],
        text=":white_check_mark: Cron was updated",
        blocks=success_block(
            header_text="Cron was updated",
        ),
        user=body["user_id"],
    )


@app.event(
    "message",
    matchers=[
        im_matcher,
    ],
)
async def im_listener(
        ack: AsyncAck,
        client: AsyncWebClient,
        message: dict,
):
    """
    Listen for DMs if daily status is True for the user \n
    """

    await ack()

    db = Database()

    # Get user daily status
    user_status = await db.get_user_status(
        user_id=message["user"],
    )

    # Notify if user not subscribed
    if user_status is None:
        # Send notification about unsubscribed status
        await client.chat_postMessage(
            channel=message["channel"],
            text=":x: You are not subscribed",
            blocks=error_block(
                header_text="You are not subscribed to daily bot",
                body_text="Invite the bot to the channel with you as a member to subscribe",
            ),
        )

        return

    # Skip if daily wasn't started for the user
    if not user_status:
        # Send notification about user's daily status
        await client.chat_postMessage(
            channel=message["channel"],
            text=":x: Bot is inactive at the moment",
            blocks=error_block(
                header_text="Bot is inactive at the moment",
                body_text="Daily meeting hasn't been started yet or you answered on all questions",
            ),
        )
        return

    # Import color scheme
    from src.utils import default_colors

    # Import block kit & post_report
    from src.block_kit import report_attachment_block, end_daily_block
    from src.report import post_report

    # Get questions list
    user_main_channel = await db.get_user_main_channel(
        user_id=message["user"],
    )

    questions_info = await db.get_all_questions(
        channel_id=user_main_channel,
    )

    question_idx_list = [idx for question, idx in questions_info]

    # Get question_list length
    questions_length: int = len(questions_info)

    # Get user questions index
    user_idx = await db.get_user_q_idx(
        user_id=message['user'],
    )

    if not user_idx:
        current_question_idx = 1
    else:
        current_question_idx = question_idx_list.index(user_idx)

    next_q_idx = question_idx_list[
        current_question_idx + 1
        if current_question_idx + 1 < questions_length
        else 0
    ]

    # Updated questions index
    await db.update_user_q_idx(
        user_id=message["user"],
        q_idx=next_q_idx,
    )

    # Write user's answer
    await db.set_user_answer(
        user_id=message["user"],
        question_id=user_idx,  # Get question id
        answer=message["text"],
    )

    # Update user's daily status if idx is out of range
    if user_idx == question_idx_list[-1]:
        # Delete user's daily status & idx
        await db.reset_user_daily_status(
            user_id=message["user"],
        )

        # Skip if there is no channel
        if not user_main_channel:
            await client.chat_postMessage(
                channel=message["channel"],
                text=":x: Daily will not be posted",
                blocks=error_block(
                    header_text="Daily will not be posted",
                    body_text="You aren't subscribed to a channel.\nRun this in your daily channel `/refresh_users`",
                ),
            )

            return

        # Get user answers
        user_answers = await db.get_user_answers(
            user_id=message["user"],
        )

        # Delete user's answers from database
        await db.delete_user_answers(
            user_id=message["user"],
        )

        # Collect answers_block
        attachments = list()

        # Update color scheme length if needed
        if questions_length > len(default_colors):
            from math import ceil

            default_colors = default_colors * ceil(questions_length / len(default_colors))

        for idx, user_set in enumerate(user_answers):
            # Check for skips in user answers
            if str(user_set["answer"]).lower() in ("-", "nil", "none", "null"):
                continue

            # Create attachments
            attachments.append(
                report_attachment_block(
                    header_text=str(user_set["question"]),
                    body_text=str(user_set["answer"]),
                    color=default_colors[idx],
                )
            )

        # Get user info
        user_info = (await client.users_info(user=message["user"]))["user"]

        # Create channel link
        channel_name, channel_team_id = await db.get_channel_link_info(
            channel_id=user_main_channel,
        )

        channel_link = f"<slack://channel?team={channel_team_id}&id={user_main_channel}|#{channel_name}>"

        # Send report
        async_tasks = list()

        async_tasks.append(
            post_report(
                app=client,
                db_connection=db,
                channel=user_main_channel,
                user_id=message["user"],
                attachments=attachments,
                username=user_info["real_name"],
                icon_url=user_info["profile"]["image_48"],
            )
        )

        # Send notification to the user
        async_tasks.append(
            client.chat_postMessage(
                channel=message["channel"],
                text=":white_check_mark: Daily was posted",
                blocks=end_daily_block(
                    start_body_text=f"Thanks, <@{message['user']}>!",
                    end_body_text="Have a wonderful and productive day :four_leaf_clover: ",
                    footer_text=f"You can see your latest report in {channel_link}",
                ),
            )
        )

        # Execute all tasks at once
        await gather(*async_tasks)

        # Exit
        return

    next_question = list(filter(lambda question_info: question_info[1] == next_q_idx, questions_info))[0][0]

    # Send question to dm
    await client.chat_postMessage(
        channel=message["channel"],
        text=">" + next_question,
        mrkdwn=True,  # Enable markdown
    )


@app.command(
    "/skip_daily",
)
async def skip_daily_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    """
    Listen for command skip_daily in subscribed channels \n
    Exits if command was send in DM
    """

    await ack()

    # Catch if command was used in DM
    if await is_dm_in_command(
            client=client,
            channel_name=body["channel_name"],
            user_id=body["user_id"],
    ):
        return

    db = Database()

    # Check if not subscribed
    if await is_not_subscribed(
            client=client,
            db_connection=db,
            channel_id=body["channel_id"],
            user_id=body["user_id"],
    ):
        return

    from src.utils import skip_cron

    # Skip next cron
    await skip_cron(
        channel_id=body["channel_id"],
    )

    # Notify channel about skipped daily
    await client.chat_postMessage(
        channel=body["channel_id"],
        text=":white_check_mark: Daily was skipped",
        blocks=success_block(
            header_text="Next daily was successfully skipped",
            body_text=f"<@{body['user_id']}> skipped next daily",
        ),
    )


@app.event(
    "message",
    matchers=[
        thread_matcher,
    ],
)
async def thread_listener(
        ack: AsyncAck,
        client: AsyncWebClient,
        message: dict,
):
    """
    Listen for messages in threads in subscriber channels \n
    """

    await ack()

    db = Database()

    # Check if thread is report (None if not a report)
    # If report - the entry will be deleted
    user_id = await db.get_user_id_by_thread_ts(
        thread_ts=message["thread_ts"],
    )

    if user_id:
        # Notify
        await client.chat_postMessage(
            text=f"Hey, <@{user_id}>.\nYou was mentioned in the thread",
            channel=message["channel"],
            thread_ts=message["thread_ts"],
            mrkdwn=True,
        )
