"""Dispatch the meet-bot agent into a meeting.

Usage:
    uv run python dispatch.py "https://meet.google.com/abc-defg-hij"
    uv run python dispatch.py "https://meet.google.com/abc-defg-hij" --avatar Tony --universidad UP --sesion 1
    uv run python dispatch.py "https://meet.google.com/abc-defg-hij" --avatar Clau --universidad TEC --sesion 3
"""

import argparse
import asyncio
import json
import uuid

from dotenv import load_dotenv
from livekit import api

from profiles import AVATAR_NAMES, UNIVERSITY_NAMES

load_dotenv()

AGENT_NAME = "meet-bot"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch meet-bot into a meeting")
    parser.add_argument("meeting_url", help="Full join URL of the meeting")
    parser.add_argument(
        "--avatar",
        choices=AVATAR_NAMES,
        default="Tony",
        help="Avatar to use (default: Tony)",
    )
    parser.add_argument(
        "--universidad",
        choices=UNIVERSITY_NAMES,
        default="UP",
        help="University profile (default: UP)",
    )
    parser.add_argument(
        "--sesion",
        default=None,
        help="Session identifier (e.g. '01', '03')",
    )
    parser.add_argument("--bot-name", default=None, help="Override display name")
    parser.add_argument("--no-chat", action="store_true", help="Do not relay meeting chat to the agent")
    parser.add_argument("--objective", default=None, help="Objective of the session")
    args = parser.parse_args()

    metadata = {
        "meeting_url": args.meeting_url,
        "avatar": args.avatar,
        "universidad": args.universidad,
        "bot_name": args.bot_name or args.avatar,
        "listen_to_meeting_chat": not args.no_chat,
    }
    if args.sesion:
        metadata["session_id"] = args.sesion
    if args.objective:
        metadata["objective"] = args.objective

    async with api.LiveKitAPI() as lkapi:
        room_name = f"meet-bot-{uuid.uuid4().hex[:8]}"
        await lkapi.room.create_room(api.CreateRoomRequest(name=room_name))
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )
        print(f"Dispatched '{args.avatar}' into room '{room_name}'")
        print(f"  meeting_url:  {args.meeting_url}")
        print(f"  avatar:       {args.avatar}")
        print(f"  universidad:  {args.universidad.upper()}")
        if args.sesion:
            print(f"  sesion:       {args.sesion}")
        print(f"  dispatch_id:  {dispatch.id}")


if __name__ == "__main__":
    asyncio.run(main())
