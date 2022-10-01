from slack_sdk.socket_mode.websockets import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from src.db import redis_instance


async def channel_append_listener(
        client: SocketModeClient,
        req: SocketModeRequest,
):
    if req.type == "slash_commands":
        if (
                req.payload["command"] == "/channel_append"
        ):
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)

            # If where aren't channels or channel is not in the list - add channel to the list
            if (
                    not await redis_instance.llen("channels")
                    or req.payload["channel_id"].encode() not in await redis_instance.lrange("channels", 0, -1)
            ):
                await redis_instance.rpush("channels", req.payload["channel_id"])

                await client.web_client.chat_postEphemeral(
                    text="Added channel to daily bot :blush: ",
                    channel=req.payload["channel_id"],
                    user=req.payload["user_id"],
                )

                # Parse all members except for bots
                members_list = await client.web_client.conversations_members(channel=req.payload["channel_id"])
                await redis_instance.rpush(
                    "users",
                    *[
                        member for member in members_list["members"]
                        if not (await client.web_client.users_info(user=member))["user"]["is_bot"]
                    ]
                )

                await client.web_client.chat_postEphemeral(
                    text="Parsed all users to the daily bot :robot_face: ",
                    channel=req.payload["channel_id"],
                    user=req.payload["user_id"],
                )
                return
            # Trash talk if bot is already in the channel
            await client.web_client.chat_postEphemeral(
                text="I'm already here :japanese_goblin: ",
                channel=req.payload["channel_id"],
                user=req.payload["user_id"],
            )


async def channel_pop_listener(
        client: SocketModeClient,
        req: SocketModeRequest,
):
    if req.type == "slash_commands":
        if (
                req.payload["command"] == "/channel_pop"
        ):
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)

            # If the channel is in the list - delete it from the list
            if req.payload["channel_id"].encode() in await redis_instance.lrange("channels", 0, -1):
                await redis_instance.lrem("channels", 0, req.payload["channel_id"])

                await client.web_client.chat_postEphemeral(
                    text="Deleted channel from daily bot :wave: ",
                    channel=req.payload["channel_id"],
                    user=req.payload["user_id"],
                )

                # Delete all members except for bots
                members_list = await client.web_client.conversations_members(channel=req.payload["channel_id"])
                for member in members_list["members"]:
                    if not (await client.web_client.users_info(user=member))["user"]["is_bot"]:
                        await redis_instance.lrem(
                            "users",
                            0,
                            member,
                        )

                await client.web_client.chat_postEphemeral(
                    text="Parsed all users from the daily bot :skull_and_crossbones: ",
                    channel=req.payload["channel_id"],
                    user=req.payload["user_id"],
                )
                return
            # Trash talk if bot is already left
            await client.web_client.chat_postEphemeral(
                text="I don't do stuff here already :japanese_goblin: ",
                channel=req.payload["channel_id"],
                user=req.payload["user_id"],
            )


async def join_channel_listener(
        client: SocketModeClient,
        req: SocketModeRequest,
):
    if req.type == "events_api":
        if (
                req.payload["event"]["type"] == "member_joined_channel"
                and req.payload["event"].get("subtype") is None
        ):
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)

            await redis_instance.rpush("users", req.payload["event"]["user"])

            # Parse user's real_name and creator_id
            real_name = (
                await client.web_client.users_info(
                    user=req.payload["event"]["user"])
            )["user"]["real_name"]

            creator_id = (
                await client.web_client.conversations_info(
                    channel=req.payload["event"]["channel"])
            )["channel"]["creator"]

            # Send a nice notification to the creator
            await client.web_client.chat_postEphemeral(
                text=f"User `{real_name}` joined and was added to daily bot :kangaroo: ",
                channel=req.payload["event"]["channel"],
                user=creator_id,
            )


async def leave_channel_listener(
        client: SocketModeClient,
        req: SocketModeRequest,
):
    if req.type == "events_api":
        if (
                req.payload["event"]["type"] == "member_left_channel"
                and req.payload["event"].get("subtype") is None
        ):
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)

            await redis_instance.lrem("users", 0, req.payload["event"]["user"])

            # Parse user's real_name and creator_id
            real_name = (
                await client.web_client.users_info(
                    user=req.payload["event"]["user"])
            )["user"]["real_name"]

            admin_id = (
                    await client.web_client.conversations_info(
                        channel=req.payload["event"]["channel"])
            )["channel"]["creator"]

            # Send a nice notification to the creator
            await client.web_client.chat_postEphemeral(
                text=f"User `{real_name}` left and was removed from daily bot :cry: ",
                channel=req.payload["event"]["channel"],
                user=admin_id,
            )


async def refresh_users_listener(
        client: SocketModeClient,
        req: SocketModeRequest,
):
    if req.type == "slash_commands":
        if (
                req.payload["command"] == "/refresh_users"
        ):
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)

            # Delete set users
            await redis_instance.delete("users")

            # Parse and refresh all users in the channel
            members_list = await client.web_client.conversations_members(channel=req.payload["channel_id"])
            await redis_instance.rpush(
                "users",
                *[
                    member for member in members_list["members"]
                    if not (await client.web_client.users_info(user=member))["user"]["is_bot"]
                ]
            )

            # Notification to the user
            await client.web_client.chat_postEphemeral(
                text="User list was updated :robot_face: ",
                channel=req.payload["channel_id"],
                user=req.payload["user_id"],
            )


async def questions_listener(
        client: SocketModeClient,
        req: SocketModeRequest,
):
    if req.type == "slash_commands":
        if (
                req.payload["command"] == "/questions"
        ):
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)

            question_list = await redis_instance.lrange("questions", 0, -1)

            if not len(question_list):
                await client.web_client.chat_postEphemeral(
                    text=f"None is available.\nAdd some with `/question_append How are you doing`",
                    channel=req.payload["channel_id"],
                    user=req.payload["user_id"],
                )
                return

            question_list_formatted = ""
            for idx, question in enumerate(question_list, start=1):
                question_list_formatted += f"{idx}.  {question.decode('utf-8')}.\n"

            # Send user list to user
            await client.web_client.chat_postEphemeral(
                text=f"Questions:\n{question_list_formatted}",
                channel=req.payload["channel_id"],
                user=req.payload["user_id"],
            )


async def question_append_listener(
        client: SocketModeClient,
        req: SocketModeRequest,
):
    if req.type == "slash_commands":
        if (
                req.payload["command"] == "/question_append"
        ):
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)

            # If user specified the question add it and notify the user
            if req.payload["text"]:
                await redis_instance.rpush(
                    "questions",
                    req.payload["text"],
                )

                await client.web_client.chat_postEphemeral(
                    text="Your question has been added to the daily bot :zap: ",
                    channel=req.payload["channel_id"],
                    user=req.payload["user_id"],
                )
                return
            # Else send the instructions
            await client.web_client.chat_postEphemeral(
                text="Enter the question after the command\nExample: `/question_append How are you doing`",
                channel=req.payload["channel_id"],
                user=req.payload["user_id"],
            )


async def question_pop_listener(
        client: SocketModeClient,
        req: SocketModeRequest,
):
    if req.type == "slash_commands":
        if (
                req.payload["command"] == "/question_pop"
        ):
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)

            # If user specified the question add it and notify the user
            if req.payload["text"]:
                try:
                    req.payload["text"] = int(req.payload["text"])
                except ValueError:
                    await client.web_client.chat_postEphemeral(
                        text="Enter the index of the question you want to delete\nExample: `/question_pop 1` ",
                        channel=req.payload["channel_id"],
                        user=req.payload["user_id"],
                    )
                    return

                question_list = await redis_instance.lrange("questions", 0, -1)
                for idx, question in enumerate(question_list, start=1):
                    if idx == int(req.payload["text"]):
                        await redis_instance.lrem(
                            "questions",
                            0,
                            question,
                        )
                        break

                await client.web_client.chat_postEphemeral(
                    text="Your question has been removed from the daily bot :zap: ",
                    channel=req.payload["channel_id"],
                    user=req.payload["user_id"],
                )
                return
            # Else send the instructions
            await client.web_client.chat_postEphemeral(
                text="Enter the index after the command\nExample: `/question_pop 1`",
                channel=req.payload["channel_id"],
                user=req.payload["user_id"],
            )
