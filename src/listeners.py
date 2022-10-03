from slack_bolt.context.async_context import AsyncAck, AsyncWebClient
from src.db import Database
from main import app


@app.command("/channel_append")
async def channel_append_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
) -> None:
    from src.block_kit import success_block

    await ack()

    db = Database()
    await db.connect()

    # If where aren't channels or channel is not in the list - add channel to the list
    all_channels = await db.get_all_channels()

    if (
            not all_channels
            or body["channel_id"] not in all_channels
    ):
        # Write channel
        await db.add_channel(body["channel_id"])

        # Post message on success
        await client.chat_postEphemeral(
            blocks=success_block(
                header_text="Channel has been successfully subscribed"
            ),
            channel=body["channel_id"],
            user=body["user_id"],
        )

        # Parse all members except bots
        members_list = [
            member for member in (await client.conversations_members(channel=body["channel_id"]))["members"]
            if not (await client.users_info(user=member))["user"]["is_bot"]
        ]

        # Parse user to db
        for user in members_list:
            await db.create_user(
                user_id=user,
                daily_status=False,
                q_idx=0,
                main_channel_id=body["channel_id"],
            )

        # Post a message on success
        await client.chat_postEphemeral(
            blocks=success_block(
                header_text="All members was successfully parsed",
            ),
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    # Trash talk if bot is already in the channel
    await client.chat_postEphemeral(
        blocks=success_block(
            header_text="Channel already has been added",
        ),
        channel=body["channel_id"],
        user=body["user_id"],
    )


@app.command("/channel_pop")
async def channel_pop_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    from src.block_kit import success_block

    await ack()

    db = Database()
    await db.connect()

    # If the channel is in the list - delete it from the list
    if body["channel_id"] in await db.get_all_channels():
        await db.delete_channel(body["channel_id"])

        await client.chat_postEphemeral(
            blocks=success_block(
                header_text="Channel has been successfully unsubscribed"
            ),
            channel=body["channel_id"],
            user=body["user_id"],
        )

        # Delete all members except for bots
        await db.delete_users_by_main_channel(body["channel_id"])

        await client.chat_postEphemeral(
            blocks=success_block(
                header_text="All members was successfully unsubscribed"
            ),
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    # Trash talk if bot is already left
    await client.chat_postEphemeral(
        blocks=success_block(
            "Channel already has been successfully unsubscribed"
        ),
        channel=body["channel_id"],
        user=body["user_id"],
    )


@app.event("member_joined_channel")
async def join_channel_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    if body["event"].get("subtype"):
        return

    from src.block_kit import success_block

    await ack()

    db = Database()
    await db.connect()

    # Add user to the user_list
    await db.create_user(
        user_id=body["event"]["user"],
        daily_status=False,
        q_idx=0,
        main_channel_id=body["event"]["channel"],
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
        blocks=success_block(
            f"User `{real_name}` joined and was successfully parsed",
        ),
        channel=body["event"]["channel"],
        user=creator_id,
    )


@app.event("member_left_channel")
async def leave_channel_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    if body["event"].get("subtype"):
        return

    from src.block_kit import success_block

    await ack()

    db = Database()
    await db.connect()

    await db.delete_user(body["event"]["user"])

    # Parse user's real_name and creator_id
    real_name = (
        await client.users_info(
            user=body["event"]["user"])
    )["user"]["real_name"]

    admin_id = (
        await client.conversations_info(
            channel=body["event"]["channel"])
    )["channel"]["creator"]

    # Send a nice notification to the creator
    await client.chat_postEphemeral(
        blocks=success_block(
            header_text=f"User `{real_name}` left and was successfully unsubscribed",
        ),
        channel=body["event"]["channel"],
        user=admin_id,
    )


@app.command("/refresh_users")
async def refresh_users_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    from src.block_kit import success_block

    await ack()

    db = Database()
    await db.connect()

    # Delete set users
    await db.delete_users_by_main_channel(body["channel_id"])

    # Parse and refresh all users in the channel
    members_list = [
        member for member in (await client.conversations_members(channel=body["channel_id"]))["members"]
        if not (await client.users_info(user=member))["user"]["is_bot"]
    ]

    # Parse user to db
    for user in members_list:
        await db.create_user(
            user_id=user,
            daily_status=False,
            q_idx=0,
            main_channel_id=body["channel_id"],
        )

    # Notification to the user
    await client.chat_postEphemeral(
        blocks=success_block(
            header_text="All members have been successfully parsed"
        ),
        channel=body["channel_id"],
        user=body["user_id"],
    )


@app.command("/questions")
async def questions_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    await ack()

    db = Database()
    await db.connect()

    question_list = await db.get_all_questions()

    if not len(question_list):
        from src.block_kit import error_block

        await client.chat_postEphemeral(
            blocks=error_block(
                header_text="None question available",
                body_text="Add some with `/question_append <your_daily_question>`",
            ),
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    from src.block_kit import question_list_block

    # Send user list to user
    await client.chat_postEphemeral(
        blocks=question_list_block(question_list=question_list),
        channel=body["channel_id"],
        user=body["user_id"],
    )


@app.command("/question_append")
async def question_append_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    await ack()

    db = Database()
    await db.connect()

    # If user specified the question add it and notify the user
    if body["text"]:
        from src.block_kit import success_block

        await db.add_question(body["text"])

        await client.chat_postEphemeral(
            blocks=success_block(
                header_text="Your question has been added to the list"
            ),
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    from src.block_kit import error_block

    # Else send the instructions
    await client.chat_postEphemeral(
        blocks=error_block(
            header_text="Question wasn't entered",
            body_text="Enter the question after the command\nExample: `/question_append <your_question>`",
        ),
        channel=body["channel_id"],
        user=body["user_id"],
    )


@app.command("/question_pop")
async def question_pop_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    await ack()

    db = Database()
    await db.connect()

    # If user specified the question add it and notify the user
    if body["text"]:
        if not body["text"].isdigit():
            from src.block_kit import error_block

            await client.chat_postEphemeral(
                blocks=error_block(
                    header_text="Not valid question index",
                    body_text="Enter the index of the question you want to delete\nExample: `/question_pop 1` ",
                ),
                channel=body["channel_id"],
                user=body["user_id"],
            )
            return

        await db.delete_question(int(body["text"]))

        from src.block_kit import success_block

        await client.chat_postEphemeral(
            blocks=success_block(
                header_text="Your question has been removed from the daily bot",
            ),
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    from src.block_kit import error_block

    # Else send the instructions
    await client.chat_postEphemeral(
        blocks=error_block(
            header_text="Index wasn't entered",
            body_text="Enter the index after the command\nExample: `/question_pop 1`",
        ),
        channel=body["channel_id"],
        user=body["user_id"],
    )


@app.command("/cron")
async def cron_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    await ack()

    # Validate user input
    try:
        from cron_validator import CronValidator

        # Raise an exception if cron wasn't specified
        if not body["text"]:
            raise ValueError
        CronValidator.parse(body["text"])
    except ValueError:
        from src.block_kit import error_block

        await client.chat_postEphemeral(
            blocks=error_block(
                header_text="Incorrect cron",
                body_text="Check cron on <https://crontab.guru/|CrontabGuru>",
            ),
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    db = Database()
    await db.connect()

    # Set specified cron to current channel
    await db.add_channel(
        channel_id=body["channel_id"],
        cron=body["text"],
    )

    from src.utils import start_cron
    from src.block_kit import success_block

    # Update CronTrigger in scheduler
    await start_cron()

    # Post notification on success
    await client.chat_postEphemeral(
        blocks=success_block(
            header_text="Cron was updated",
        ),
        channel=body["channel_id"],
        user=body["user_id"],
    )


@app.event("message")
async def im_listener(
        ack: AsyncAck,
        client: AsyncWebClient,
        message,
        body,
):
    await ack()

    db = Database()
    await db.connect()

    # Skip if daily wasn't started for the user
    if not await db.get_user_status(user_id=message['user']):
        return

    # Import color scheme
    from src.utils import default_colors

    # Import block kit & post_report
    from src.block_kit import report_attachment_block, end_daily_block
    from src.report import post_report

    # Get user questions index
    user_idx = await db.get_user_q_idx(message['user'])

    # Set 0 if it's not set
    if not user_idx:
        user_idx = 1

    # Write user's answer
    await db.set_user_answer(
        user_id=message['user'],
        question_id=user_idx,
        answer=message["text"],
    )

    # Get questions list
    questions: list[str, str] = await db.get_all_questions()
    questions_length: int = len(questions)

    user_main_channel = await db.get_user_main_channel(user_id=message["user"])

    # Updated questions index
    await db.create_user(
        user_id=message['user'],
        daily_status=True,
        q_idx=user_idx + 1,
        main_channel_id=user_main_channel,
    )

    # Update user's daily status if idx is out of range
    if user_idx == questions_length:
        # Delete user's daily status & idx
        await db.create_user(
            user_id=message['user'],
            daily_status=False,
            q_idx=0,
            main_channel_id=user_main_channel,
        )

        # Get user info
        user_info = (await client.users_info(user=message['user']))["user"]

        # Get user answers
        user_answers = await db.get_user_answers(user_id=message['user'])

        # Skip if there is no channel
        if not user_main_channel:
            return

        # Delete user's answers from Redis
        await db.delete_user_answers(user_id=message['user'])

        # Collect answers_block
        attachments = list()

        # Update color scheme length if needed
        if questions_length > len(default_colors):
            from math import ceil

            default_colors = default_colors * ceil(questions_length / len(default_colors))

        for idx, user_set in enumerate(user_answers):
            # Check for skips in user answers
            if user_set["answer"].lower() in ("-", "nil", "none", "null"):
                continue

            # Create attachments
            attachments.append(
                report_attachment_block(
                    header_text=user_set["question"],
                    body_text=user_set["answer"],
                    color=default_colors[idx],
                )
            )

        # Send report
        await post_report(
            app=client,
            channel=user_main_channel,
            attachments=attachments,
            username=user_info["real_name"],
            icon_url=user_info["profile"]["image_48"],
        )

        # Send notification to the user
        await client.chat_postMessage(
            channel=body["event"]["channel"],
            blocks=end_daily_block(
                start_body_text=f"Thanks, {user_info['real_name']}!",
                end_body_text="Have a wonderful and productive day :four_leaf_clover: ",
            ),
        )

        # Exit
        return

    # Send question to dm
    await client.chat_postMessage(
        channel=message["channel"],
        text=">" + questions[user_idx],
        mrkdwn=True,  # Enable markdown
    )
# TODO: add thread listener
