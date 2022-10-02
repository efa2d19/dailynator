import asyncio

from slack_bolt.context.async_context import AsyncAck, AsyncWebClient

from main import app
from src.db import redis_instance


@app.command("/channel_append")
async def channel_append_listener(
        ack: AsyncAck,
        body: dict,
        client: AsyncWebClient,
):
    await ack()

    # If where aren't channels or channel is not in the list - add channel to the list
    if (
            not await redis_instance.llen("channels")
            or body["channel_id"].encode() not in await redis_instance.lrange("channels", 0, -1)
    ):
        # Write channel to Redis
        await redis_instance.set(f"channels", body["channel_id"])

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

        # Update user_list
        await redis_instance.rpush(
            "users",
            *members_list
        )

        # Set main channel for every member
        async_tasks = list()

        for member in members_list:
            async_tasks.append(
                redis_instance.set(f"{member}_channel", body["channel_id"])
            )

        await asyncio.gather(*async_tasks)

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

    # If the channel is in the list - delete it from the list
    if body["channel_id"].encode() in await redis_instance.lrange("channels", 0, -1):
        await redis_instance.lrem("channels", 0, body["channel_id"])

        await client.chat_postEphemeral(
            text="Deleted channel from daily bot :wave: ",
            channel=body["channel_id"],
            user=body["user_id"],
        )

        # Delete all members except for bots
        members_list = await client.conversations_members(channel=body["channel_id"])
        for member in members_list["members"]:
            if not (await client.users_info(user=member))["user"]["is_bot"]:
                await redis_instance.lrem("users", 0, member,)

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

    # Add user to the user_list
    await redis_instance.rpush("users", body["event"]["user"])

    # Set users main channel
    await redis_instance.set(f"{body['event']['user']}_channel", body["event"]["channel"])

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

    await redis_instance.lrem("users", 0, body["event"]["user"])

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
    await redis_instance.delete("users")

    # Parse and refresh all users in the channel
    members_list = [
        member for member in (await client.conversations_members(channel=body["channel_id"]))["members"]
        if not (await client.users_info(user=member))["user"]["is_bot"]
    ]

    # Add users to user_list
    await redis_instance.rpush(
        "users",
        *members_list
    )

    # Set main channel for every member
    async_tasks = list()

    for member in members_list:
        async_tasks.append(
            redis_instance.set(f"{member}_channel", body["channel_id"])
        )

    await asyncio.gather(*async_tasks)

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

    question_list = await redis_instance.lrange("questions", 0, -1)

    if not len(question_list):
        await client.chat_postEphemeral(
            text=f"None is available.\nAdd some with `/question_append How are you doing`",
            channel=body["channel_id"],
            user=body["user_id"],
        )
        return

    question_list_formatted = ""
    for idx, question in enumerate(question_list, start=1):
        question_list_formatted += f"{idx}.  {question.decode('utf-8')}.\n"

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

    # If user specified the question add it and notify the user
    if body["text"]:
        await redis_instance.rpush(
            "questions",
            body["text"],
        )

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

    # If user specified the question add it and notify the user
    if body["text"]:
        if not body["text"].isdigit():
            await client.chat_postEphemeral(
                text="Enter the index of the question you want to delete\nExample: `/question_pop 1` ",
                channel=body["channel_id"],
                user=body["user_id"],
            )
            return

        question_list = await redis_instance.lrange("questions", 0, -1)
        for idx, question in enumerate(question_list, start=1):
            if idx == int(body["text"]):
                await redis_instance.lrem(
                    "questions",
                    0,
                    question,
                )
                break

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

    # Set specified cron to Redis
    await redis_instance.set(
        "cron",
        body["text"],
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
):
    await ack()

    # Skip if daily wasn't started for the user
    if not await redis_instance.get(f"{message['user']}_started"):
        return

    # Write user's answer
    await redis_instance.rpush(
        f"{message['user']}_answers",
        message["text"],
    )

    # Get questions list
    questions: list[str] = list(map(bytes.decode, await redis_instance.lrange("questions", 0, -1)))

    # Get user's main channel
    channel: bytes | str = await redis_instance.get(f"{message['user']}_channel")

    # Skip if there is no channel
    if not channel:
        return

    # Decode channel
    channel = channel.decode("utf-8")

    # Get user questions index
    user_idx = await redis_instance.get(f"{message['user']}_idx")

    # Set 0 if it's not set
    if not user_idx:
        user_idx = 1
    else:
        user_idx = int(user_idx)

    # Updated questions index
    await redis_instance.set(f"{message['user']}_idx", str(user_idx + 1))

    # Update user's daily status if idx is out of range
    if user_idx == len(questions):
        # Delete user's daily status
        await redis_instance.delete(f"{message['user']}_started")

        # Delete user's idx
        await redis_instance.delete(f"{message['user']}_idx")

        # Get user info
        user_info = (await client.users_info(user=message['user']))["user"]

        # Get user answers
        user_answers = list(map(bytes.decode, await redis_instance.lrange(f"{message['user']}_answers", 0, -1)))

        # Delete user's answers from Redis
        await redis_instance.delete(f"{message['user']}_answers")

        # Collect answers_block
        attachments = list()

        # Import color scheme
        from src.utils import default_colors

        # Update color scheme length if needed
        if len(questions) > len(default_colors):
            from math import ceil

            default_colors = default_colors * ceil(len(questions) / len(default_colors))

        for idx, (question, answer) in enumerate(zip(questions, user_answers)):
            # Check for skips in user answers
            if answer.lower() in ("-", "nil", "none", "null"):
                continue

            from slack_sdk.models.blocks import HeaderBlock, MarkdownTextObject, SectionBlock
            from slack_sdk.models.attachments import BlockAttachment

            # Create attachments
            attachments.append(
                BlockAttachment(
                    blocks=[
                        HeaderBlock(text=question),
                        SectionBlock(text=MarkdownTextObject(text=answer))
                    ],
                    color=default_colors[idx]
                )
            )

        from src.report import post_report

        # Send report
        await post_report(
            app=client,
            channel=channel,
            attachments=attachments,
            username=user_info["real_name"],
            icon_url=user_info["profile"]["image_48"],
        )

        # Exit
        return

    # Send question
    await client.chat_meMessage(
        channel=message["channel"],
        text=questions[user_idx]
    )
