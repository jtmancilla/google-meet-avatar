"""Wake-word gate for the meeting agent (Alexa-style attention mode).

Pure synchronous logic — no network, no threads, no livekit imports.
Fully configurable via constructor arguments (wired to env vars in agent.py).

Modes:
- IDLE: user turns are returned as ambient context, not answered.
- ACTIVE: user turns are answered; each directed turn renews the window.
"""

import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Callable

# Accent-tolerant character classes so "óye"/"oye" both match.
_ACCENT_GROUPS = {
    "a": "[aá]",
    "e": "[eé]",
    "i": "[ií]",
    "o": "[oó]",
    "u": "[uúü]",
    "n": "[nñ]",
}


def _normalize(text: str) -> str:
    """Lowercase-folded, accent-stripped text for matching."""
    folded = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in folded if unicodedata.category(c) != "Mn")


def _normalize_for_phrases(text: str) -> str:
    """Like _normalize but also strips punctuation and collapses whitespace."""
    normalized = _normalize(text)
    kept = (
        c if (unicodedata.category(c)[0] in "LN" or c.isspace()) else " "
        for c in normalized
    )
    return " ".join("".join(kept).split())


def _tolerant(word: str) -> str:
    """Regex pattern for `word` that tolerates accents and case."""
    parts = []
    for ch in _normalize(word):
        parts.append(_ACCENT_GROUPS.get(ch, re.escape(ch)))
    return "".join(parts)


@dataclass
class GateDecision:
    """Result of processing one user transcript."""

    respond: bool
    text: str  # cleaned text for the LLM (respond) or labeled text (ambient)
    closing: bool = False  # True if this turn closed the attention window


class WakeWordGate:
    def __init__(
        self,
        name: str,
        window_s: float = 30.0,
        closing_phrases: list[str] | None = None,
        ambient_max_turns: int = 10,
        ambient_label: str = "[conversación entre participantes, no dirigida a ti]",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.name = name
        self.window_s = window_s
        self.closing_phrases = [_normalize_for_phrases(p.strip()) for p in (closing_phrases or []) if p.strip()]
        self.ambient_max_turns = ambient_max_turns
        self.ambient_label = ambient_label
        self._clock = clock

        self._active = False
        self._last_directed_at: float = 0.0

        name_pat = _tolerant(name)
        vocatives = "|".join(_tolerant(w) for w in ("oye", "hey", "hola", "ok"))
        self._vocative_re = re.compile(rf"^(?:{vocatives})?\s*{name_pat}\b[,:;]?\s*", re.IGNORECASE)
        self._mention_re = re.compile(rf"\b{name_pat}\b", re.IGNORECASE)

    @property
    def active(self) -> bool:
        return self._active

    def _is_active(self, now: float) -> bool:
        return self._active and (now - self._last_directed_at) < self.window_s

    def process(self, transcript: str, now: float | None = None) -> GateDecision:
        """Decide what to do with one user transcript.

        - Closing phrase -> go idle, do not respond, do not store.
        - Directed turn (trigger match or open window) -> respond with cleaned text.
        - Otherwise -> ambient context, do not respond.
        """
        if now is None:
            now = self._clock()

        # Expire the window lazily so the public `active` flag stays accurate.
        if self._active and not self._is_active(now):
            self._active = False

        normalized = _normalize_for_phrases(transcript)

        if any(phrase and phrase in normalized for phrase in self.closing_phrases):
            self._active = False
            return GateDecision(respond=False, text="", closing=True)

        vocative = self._vocative_re.match(transcript)
        mentioned_with_question = (
            bool(self._mention_re.search(transcript))
            and _normalize(transcript).rstrip().endswith(("?", "¿"))
        )
        directed = bool(vocative) or mentioned_with_question or self._is_active(now)

        if directed:
            self._active = True
            self._last_directed_at = now
            text = transcript
            if vocative:
                text = transcript[vocative.end():].strip()
            return GateDecision(respond=True, text=text)

        return GateDecision(respond=False, text=f"{self.ambient_label} {transcript}")
