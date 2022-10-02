import asyncio
import logging

from dotenv import load_dotenv
from logging import basicConfig, DEBUG

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.web.async_client import AsyncWebClient

from src.db import redis_instance
from src.report import post_report

basicConfig(level=DEBUG)

load_dotenv()

app = AsyncApp()


@app.event("message")
async def im_listener(
        ack: AsyncAck,
        say: AsyncSay,
        body: dict,
        client: AsyncWebClient,
        logger: logging.Logger,
        context,
        message,
):
    await ack()

    # Skip if daily wasn't started for the user
    if not await redis_instance.get(f"{body['user_id']}_started"):
        return

    # Get questions list
    questions: list[str] = list(map(bytes.decode, await redis_instance.lrange("questions", 0, -1)))

    # Get first channel from the channel list
    channel: list[str] = list(map(bytes.decode, await redis_instance.lrange("channels", 0, 0)))

    # Get user questions index
    user_idx = await redis_instance.get(f"{body['user_id']}_idx")

    # Set 0 if it's not set
    if not user_idx:
        user_idx = 1

    # Updated questions index
    await redis_instance.set(f"{body['user_id']}_idx", user_idx + 1)

    # Update user's daily status if idx is out of range
    if user_idx > len(questions):
        # Delete user's daily status
        await redis_instance.delete(f"{body['user_id']}_started")

        # Delete user's idx
        await redis_instance.delete(f"{body['user_id']}_idx")

        # Get user info
        user_info = (await client.users_info(user=body['user_id']))["user"]

        # Get user answers
        user_answers = await redis_instance.lrange(f"{body['user_id']}_answers", 0, -1)

        # Collect answers_block
        answers_block = ""

        for question, answer in zip(questions, user_answers):
            answers_block += f"**{question}**\n{answer.decode('utf-8')}\n"

        # Send report
        await post_report(
            app=client,
            channel=channel[0],
            text=answers_block,
            username=user_info["real_name"],
            icon_url=user_info["profile"]["image_48"],
        )

        # Exit
        return

    # Write user's answer
    await redis_instance.rpush(
        f"{body['user_id']}_answers",
        message["text"],
    )

    # Send question
    await client.chat_meMessage(
        channel=body["channel_id"],
        text=questions[user_idx]
    ) # noqa


async def main():
    import src.listeners as listeners

    # Get SocketHandler
    handler = AsyncSocketModeHandler(app=listeners.app)

    # Start server
    handler = await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
