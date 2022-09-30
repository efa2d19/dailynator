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
                    not await redis_instance.scard("channels")
                    or req.payload["channel_id"].encode() not in await redis_instance.smembers("channels")
            ):
                await redis_instance.sadd("channels", req.payload["channel_id"])

                await client.web_client.chat_postEphemeral(
                    text="Added channel to daily bot :blush: ",
                    channel=req.payload["channel_id"],
                    user=req.payload["user_id"],
                )

                # Parse all members except for bots
                members_list = await client.web_client.conversations_members(channel=req.payload["channel_id"])
                await redis_instance.sadd(
                    "users",
                    *[
                        member for member in members_list["members"]
                        if not (await client.web_client.users_info(user=member))["user"]["is_bot"]
                    ]
                )
            else:
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
            if req.payload["channel_id"].encode() in await redis_instance.smembers("channels"):
                await redis_instance.srem("channels", req.payload["channel_id"])

                await client.web_client.chat_postEphemeral(
                    text="Deleted channel from daily bot :wave: ",
                    channel=req.payload["channel_id"],
                    user=req.payload["user_id"],
                )

                # Delete all members except for bots
                members_list = await client.web_client.conversations_members(channel=req.payload["channel_id"])
                await redis_instance.srem(
                    "users",
                    *[
                        member for member in members_list["members"]
                        if not (await client.web_client.users_info(user=member))["user"]["is_bot"]
                    ]
                )
            else:
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

            await redis_instance.sadd("users", req.payload["event"]["user"])

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

            await redis_instance.srem("users", req.payload["event"]["user"])

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
            await redis_instance.sadd(
                "users",
                *[
                    member for member in members_list["members"]
                    if not (await client.web_client.users_info(user=member))["user"]["is_bot"]
                ]
            )


# async def questions_listener(
#         client: SocketModeClient,
#         req: SocketModeRequest,
# ):
#     if req.type == "slash_commands":
#         if (
#                 req.payload["command"] == "/questions"
#         ):
#             # Acknowledge the request
#             response = SocketModeResponse(envelope_id=req.envelope_id)
#             await client.send_socket_mode_response(response)
#
