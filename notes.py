"""Meeting notes generation: build a follow-up doc from the conversation.

Pure helpers (no network) for extraction and file writing. The LLM call is
injected by the caller so this module stays testable offline.
"""

import re
from datetime import datetime
from pathlib import Path


def extract_meet_code(meeting_url: str) -> str:
    """Extract a stable meeting identifier from a meeting URL.

    Examples:
        "https://meet.google.com/abc-defg-hij" -> "abc-defg-hij"
        "https://us06web.zoom.us/j/12345678901?pwd=x" -> "zoom-12345678901"
    """
    url = meeting_url.strip().rstrip("/")
    if "meet.google.com" in url:
        return url.split("/")[-1].split("?")[0]
    m = re.search(r"/j/(\d+)", url)
    if m:
        return f"zoom-{m.group(1)}"
    # fallback: last path segment, sanitized
    tail = url.split("/")[-1].split("?")[0] or "meeting"
    return re.sub(r"[^A-Za-z0-9_-]", "-", tail)


def build_notes_filename(meet_code: str, now: datetime | None = None) -> str:
    """memoria filename: <meet_code>-<YYYYMMDD-HHMM>.md"""
    now = now or datetime.now()
    return f"{meet_code}-{now.strftime('%Y%m%d-%H%M')}.md"


def render_notes_document(
    summary_body: str,
    meet_code: str,
    objective: str | None = None,
    now: datetime | None = None,
) -> str:
    """Wrap the LLM-generated body with a document header."""
    now = now or datetime.now()
    lines = [
        f"# Acciones y Decisiones — {meet_code}",
        "",
        f"Fecha de generación: {now.strftime('%Y-%m-%d %H:%M')}",
    ]
    if objective:
        lines.append(f"Objetivo de la sesión: {objective}")
    lines += ["", summary_body.strip(), ""]
    return "\n".join(lines)


def save_notes(output_dir: str | Path, filename: str, content: str) -> Path:
    """Write the notes document, creating the folder if needed. Returns the path."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def transcript_from_chat_ctx(chat_ctx) -> str:
    """Flatten the chat context into a plain transcript for the summary LLM."""
    lines = []
    for item in chat_ctx.items:
        role = getattr(item, "role", None)
        text = getattr(item, "text_content", None)
        if role in ("user", "assistant") and text:
            who = "Participante" if role == "user" else "Asistente"
            lines.append(f"{who}: {text}")
    return "\n".join(lines)
