"""Dispatch the meet-bot agent into a meeting.

Replaces `lk dispatch create` so the project only needs uv + .env
(no LiveKit CLI install required).

Usage:
    uv run python dispatch.py "https://meet.google.com/abc-defg-hij"
    uv run python dispatch.py "https://meet.google.com/abc-defg-hij" --bot-name "Mi Avatar"
"""

import argparse
import asyncio
import json
import uuid

from dotenv import load_dotenv

from livekit import api

load_dotenv()

AGENT_NAME = "meet-bot"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch meet-bot into a meeting")
    parser.add_argument("meeting_url", help="Full join URL of the meeting (Google Meet, Zoom, Teams, Webex)")
    parser.add_argument("--bot-name", default="Mi Avatar", help="Display name of the bot in the meeting")
    parser.add_argument("--no-chat", action="store_true", help="Do not relay meeting chat messages to the agent")
    args = parser.parse_args()

    metadata = {
        "meeting_url": args.meeting_url,
        "bot_name": args.bot_name,
        "listen_to_meeting_chat": not args.no_chat,
    }

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
        print(f"Dispatched '{AGENT_NAME}' into room '{room_name}'")
        print(f"  meeting_url: {args.meeting_url}")
        print(f"  bot_name:    {args.bot_name}")
        print(f"  dispatch id: {dispatch.id}")


if __name__ == "__main__":
    asyncio.run(main())
