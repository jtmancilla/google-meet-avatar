#!/usr/bin/env python3
"""Script de despacho para enviar el avatar a una reunion de Google Meet.

Requisitos:
    pip install livekit-api python-dotenv

Variables necesarias en .env:
    LIVEKIT_URL=wss://tu-proyecto.livekit.cloud
    LIVEKIT_API_KEY=APIxxxx
    LIVEKIT_API_SECRET=secretxxxx

Uso:
    python avatar.py "https://meet.google.com/abc-defg-hij"
    python avatar.py "https://meet.google.com/abc-defg-hij" --avatar Clau --universidad TEC --sesion 03
"""

import argparse
import asyncio
import json
import uuid

from dotenv import load_dotenv
from livekit import api

load_dotenv()

AGENT_NAME = "meet-bot"
VALID_AVATARS = ["Tony", "Clau", "Julius"]
VALID_UNIVERSITIES = ["UP", "TEC", "UNAM"]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Despachar avatar a una reunion")
    parser.add_argument("meeting_url", help="URL completa de la reunion")
    parser.add_argument(
        "--avatar",
        choices=VALID_AVATARS,
        default="Tony",
        help="Avatar a utilizar (Tony, Clau, Julius)",
    )
    parser.add_argument(
        "--universidad",
        choices=VALID_UNIVERSITIES,
        default="UP",
        help="Perfil de universidad (UP, TEC, UNAM)",
    )
    parser.add_argument(
        "--sesion",
        default=None,
        help="Identificador de sesion (ej. '01', '03')",
    )
    parser.add_argument("--bot-name", default=None, help="Nombre visible en la llamada")
    parser.add_argument("--no-chat", action="store_true", help="Desactivar lectura del chat")
    parser.add_argument("--objective", default=None, help="Objetivo de la sesion para la minuta")
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
        print(f"Despachado '{args.avatar}' a la sala '{room_name}'")
        print(f"  URL:         {args.meeting_url}")
        print(f"  Avatar:      {args.avatar}")
        print(f"  Universidad: {args.universidad.upper()}")
        if args.sesion:
            print(f"  Sesion:      {args.sesion}")
        print(f"  Dispatch ID: {dispatch.id}")


if __name__ == "__main__":
    asyncio.run(main())
