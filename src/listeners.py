from slack_bolt.context.async_context import AsyncAck, AsyncWebClient

from main import app


@app.command("/channel_append")
async def channel_append_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
) -> None:
    await ack()

    # If where aren't channels or channel is not in the list - add channel to the list
    from src.db import get_all_channels, create_user, add_channel

    all_channels = get_all_channels()
    if (
            not all_channels
            or body["channel_id"] not in all_channels
    ):
        # Write channel
        add_channel(body["channel_id"])

        # Post message on success
        await client.chat_postEphemeral(
            text="Added channel to daily bot :blush: ",
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
            create_user(
                user_id=user,
                daily_status=False,
                q_idx=0,
                main_channel_id=body["channel_id"],
            )

        # Post a message on success
        await client.chat_postEphemeral(
            text="Parsed all users to the daily bot :robot_face: ",
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    # Trash talk if bot is already in the channel
    await client.chat_postEphemeral(
        text="I'm already here :japanese_goblin: ",
        channel=body["channel_id"],
        user=body["user_id"],
    )


@app.command("/channel_pop")
async def channel_pop_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    await ack()

    from src.db import get_all_channels, delete_channel, delete_users_by_main_channel

    # If the channel is in the list - delete it from the list
    if body["channel_id"] in get_all_channels():
        delete_channel(body["channel_id"])

        await client.chat_postEphemeral(
            text="Deleted channel from daily bot :wave: ",
            channel=body["channel_id"],
            user=body["user_id"],
        )

        # Delete all members except for bots
        delete_users_by_main_channel(body["channel_id"])

        await client.chat_postEphemeral(
            text="Deleted all users in the channel from the daily bot :skull_and_crossbones: ",
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return
    # Trash talk if bot is already left
    await client.chat_postEphemeral(
        text="I don't do stuff here already :japanese_goblin: ",
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

    await ack()

    from src.db import create_user

    # Add user to the user_list
    create_user(
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
        text=f"User `{real_name}` joined and was added to daily bot :kangaroo: ",
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

    await ack()

    from src.db import delete_user

    delete_user(body["event"]["user"])

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
        text=f"User `{real_name}` left and was removed from daily bot :cry: ",
        channel=body["event"]["channel"],
        user=admin_id,
    )


@app.command("/refresh_users")
async def refresh_users_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    await ack()

    # Delete set users
    from src.db import delete_users_by_main_channel
    delete_users_by_main_channel(body["channel_id"])

    # Parse and refresh all users in the channel
    members_list = [
        member for member in (await client.conversations_members(channel=body["channel_id"]))["members"]
        if not (await client.users_info(user=member))["user"]["is_bot"]
    ]

    # Parse user to db
    from src.db import create_user
    for user in members_list:
        create_user(
            user_id=user,
            daily_status=False,
            q_idx=0,
            main_channel_id=body["channel_id"],
        )

    # Notification to the user
    await client.chat_postEphemeral(
        text="User list was updated :robot_face: ",
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

    from src.db import get_all_questions
    question_list = get_all_questions()

    if not len(question_list):
        await client.chat_postEphemeral(
            text=f"None is available.\nAdd some with `/question_append How are you doing`",
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    question_list_formatted = ""
    for idx, question in enumerate(question_list, start=1):
        question_list_formatted += f"{idx}.  {question}.\n"

    # Send user list to user
    await client.chat_postEphemeral(
        text=f"Questions:\n{question_list_formatted}",
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

    from src.db import add_question

    # If user specified the question add it and notify the user
    if body["text"]:
        add_question(body["text"])

        await client.chat_postEphemeral(
            text="Your question has been added to the daily bot :zap: ",
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    # Else send the instructions
    await client.chat_postEphemeral(
        text="Enter the question after the command\nExample: `/question_append How are you doing`",
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

    from src.db import delete_question

    # If user specified the question add it and notify the user
    if body["text"]:
        if not body["text"].isdigit():
            await client.chat_postEphemeral(
                text="Enter the index of the question you want to delete\nExample: `/question_pop 1` ",
                channel=body["channel_id"],
                user=body["user_id"],
            )
            return

        delete_question(int(body["text"]))

        await client.chat_postEphemeral(
            text="Your question has been removed from the daily bot :zap: ",
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    # Else send the instructions
    await client.chat_postEphemeral(
        text="Enter the index after the command\nExample: `/question_pop 1`",
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
        await client.chat_postEphemeral(
            text="Incorrect cron :cry: \nCheck the cron here\nhttps://crontab.guru/",
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    from src.db import add_channel

    # Set specified cron to current channel
    add_channel(
        channel_id=body["channel_id"],
        cron=body["text"],
    )

    from src.utils import start_cron

    # Update CronTrigger in scheduler
    await start_cron()

    # Post notification on success
    await client.chat_postEphemeral(
        text="Cron was updated :zap: ",
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

    # Skip if daily wasn't started for the user
    from src.db import get_user_status

    if not get_user_status(user_id=message['user']):
        return

    # Import DB queries
    from src.db import get_user_answers, set_user_answer, get_user_q_idx
    from src.db import create_user, get_all_questions, get_user_main_channel, delete_user_answers

    # Import color scheme
    from src.utils import default_colors

    # Import block kit & post_report
    from src.block_kit import report_attachment_block, end_daily_block
    from src.report import post_report

    # Get user questions index
    user_idx = get_user_q_idx(message['user'])

    # Write user's answer
    set_user_answer(
        user_id=message['user'],
        question_id=user_idx,
        answer=message["text"],
    )

    # Set 0 if it's not set
    if not user_idx:
        user_idx = 1

    # Get questions list
    questions: list[str, str] = get_all_questions()
    questions_length: int = len(questions)

    user_main_channel = get_user_main_channel(user_id=message["user"])

    # Updated questions index
    create_user(
        user_id=message['user'],
        daily_status=True,
        q_idx=user_idx + 1,
        main_channel_id=user_main_channel,
    )

    # Update user's daily status if idx is out of range
    if user_idx == questions_length:
        # Delete user's daily status & idx
        create_user(
            user_id=message['user'],
            daily_status=False,
            q_idx=0,
            main_channel_id=user_main_channel,
        )

        # Get user info
        user_info = (await client.users_info(user=message['user']))["user"]

        # Get user answers
        user_answers = get_user_answers(user_id=message['user'])

        # Skip if there is no channel
        if not user_main_channel:
            return

        # Delete user's answers from Redis
        delete_user_answers(user_id=message['user'])

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
                end_body_text="",
            ),
        )

        # Exit
        return

    # Send question to dm
    await client.chat_postMessage(
        channel=message["channel"],
        text=questions[user_idx],
        mrkdwn=True,  # Enable markdown
    )
