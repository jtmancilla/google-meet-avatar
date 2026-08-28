import json
import logging
import os

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    cli,
    inference,
    utils,
)
from livekit.plugins import lemonslice

logger = logging.getLogger("meet-avatar")
logger.setLevel(logging.INFO)

load_dotenv()

AGENT_NAME = "meet-bot"

server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext):
    await ctx.connect()

    lemonslice_image_url = os.getenv("LEMONSLICE_IMAGE_URL")
    if lemonslice_image_url is None:
        raise ValueError("LEMONSLICE_IMAGE_URL must be set")

    meta = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
    meeting_url = meta.get("meeting_url")
    if not meeting_url:
        raise ValueError("meeting_url must be provided in job metadata")

    session = AgentSession(
        stt=inference.STT(
            model="deepgram/nova-2",
            language="es",
            extra_kwargs={"interim_results": False},
        ),
        llm=inference.LLM(model="google/gemma-4-31b-it"),
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice=os.getenv("TTS_VOICE_ID", "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
            language="es",
        ),
        turn_handling=TurnHandlingOptions(
            interruption={
                "resume_false_interruption": False,
            },
        ),
    )
    avatar = lemonslice.AvatarSession(
        agent_image_url=lemonslice_image_url,
    )
    await avatar.start(session, room=ctx.room)

    await avatar.join_meeting(
        meeting_url,
        bot_name=meta.get("bot_name") or "Mi Avatar",
        listen_to_meeting_chat=meta.get("listen_to_meeting_chat", True),
    )
    room_options = avatar.room_options()

    agent = Agent(
        instructions=(
            "Eres un asistente útil en una videollamada de Google Meet. "
            "Responde en español, de forma concisa y natural para una "
            "conversación hablada."
        ),
    )

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_options,
    )

    # Wait for the LemonSlice avatar (AGENT participant) before the first reply.
    await utils.wait_for_agent(ctx.room)
    session.generate_reply(instructions="Preséntate brevemente y ofrece tu ayuda.")


if __name__ == "__main__":
    cli.run_app(server)
