import json
import logging
import os
from collections import deque

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    StopResponse,
    TurnHandlingOptions,
    cli,
    inference,
)
from livekit.plugins import lemonslice

from gate import WakeWordGate

logger = logging.getLogger("meet-avatar")
logger.setLevel(logging.INFO)

load_dotenv()

AGENT_NAME = "meet-bot"

# --- Configuración vía variables de entorno (ver .env.example) ---

GATE_ENABLED = os.getenv("AVATAR_GATE_ENABLED", "true").strip().lower() not in ("false", "0", "no")
GATE_NAME = os.getenv("AVATAR_NAME", "Tony")
GATE_WINDOW_S = float(os.getenv("AVATAR_ACTIVATION_WINDOW_S", "30"))
GATE_CLOSING_PHRASES = [
    p.strip()
    for p in os.getenv(
        "AVATAR_CLOSING_PHRASES",
        "gracias eso era todo,eso es todo,ya puedes irte",
    ).split(",")
    if p.strip()
]
GATE_AMBIENT_MAX_TURNS = int(os.getenv("AVATAR_AMBIENT_MAX_TURNS", "10"))
GATE_AMBIENT_LABEL = os.getenv(
    "AVATAR_AMBIENT_LABEL",
    "[conversación entre participantes, no dirigida a ti]",
)

DEFAULT_INSTRUCTIONS = (
    f"Eres {GATE_NAME}, un asistente de voz en una videollamada con varias "
    "personas. Responde en español, de forma concisa y natural para una "
    "conversación hablada: máximo 2 o 3 oraciones por turno.\n"
    "\n"
    f"Solo respondes cuando alguien te habla directamente usando tu nombre "
    f"({GATE_NAME}). Los mensajes etiquetados como \"{GATE_AMBIENT_LABEL} ...\" "
    "son contexto ambiental de la reunión: úsalos para entender de qué se "
    "habla, pero nunca los respondas."
)

AGENT_INSTRUCTIONS = os.getenv("AGENT_INSTRUCTIONS", DEFAULT_INSTRUCTIONS)


class GatedAgent(Agent):
    """Agente con modo de atención estilo wake-word (ver gate.py)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._gate = WakeWordGate(
            name=GATE_NAME,
            window_s=GATE_WINDOW_S,
            closing_phrases=GATE_CLOSING_PHRASES,
            ambient_max_turns=GATE_AMBIENT_MAX_TURNS,
            ambient_label=GATE_AMBIENT_LABEL,
        )
        self._ambient_ids: deque[str] = deque()

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        if not GATE_ENABLED:
            return

        transcript = (new_message.text_content or "").strip()
        if not transcript:
            raise StopResponse

        decision = self._gate.process(transcript)

        if decision.respond:
            new_message.content = [decision.text]
            return

        if not decision.closing:
            # Guardar el turno como contexto ambiental (con cap) y no responder.
            ambient_msg = self._chat_ctx.add_message(role="user", content=decision.text)
            self._ambient_ids.append(ambient_msg.id)
            while len(self._ambient_ids) > self._gate.ambient_max_turns:
                oldest = self._ambient_ids.popleft()
                self._chat_ctx.items = [
                    item for item in self._chat_ctx.items
                    if getattr(item, "id", None) != oldest
                ]
        raise StopResponse


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

    agent = GatedAgent(instructions=AGENT_INSTRUCTIONS)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_options,
    )


if __name__ == "__main__":
    cli.run_app(server)
