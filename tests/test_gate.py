"""Tests for the wake-word gate. Pure unit tests: no network, no event loop."""

import pytest

from gate import WakeWordGate


def make_gate(**kwargs):
    defaults = dict(
        name="Tony",
        window_s=30.0,
        closing_phrases=["gracias eso era todo", "eso es todo", "ya puedes irte"],
        ambient_label="[ambient]",
    )
    defaults.update(kwargs)
    return WakeWordGate(**defaults)


class TestTriggerMatcher:
    @pytest.mark.parametrize(
        "text",
        [
            "Tony, ¿cómo estás?",
            "oye Tony, dame un resumen",
            "Óye tony que opinas",
            "HEY TONY!",
            "hola Tony",
            "ok Tony, adelante",
        ],
    )
    def test_vocative_activates(self, text):
        gate = make_gate()
        decision = gate.process(text, now=0.0)
        assert decision.respond is True
        assert gate.active is True

    @pytest.mark.parametrize(
        "text",
        [
            "¿Tony nos ayudas?",
            "¿qué opinas tú, Tony?",
        ],
    )
    def test_mention_with_question_activates(self, text):
        gate = make_gate()
        decision = gate.process(text, now=0.0)
        assert decision.respond is True

    @pytest.mark.parametrize(
        "text",
        [
            "estábamos hablando de Tony sin preguntarle nada",
            "la reunión va bien",
            "¿qué opinan todos del tema?",
        ],
    )
    def test_non_directed_is_ambient(self, text):
        gate = make_gate()
        decision = gate.process(text, now=0.0)
        assert decision.respond is False
        assert decision.closing is False
        assert decision.text.startswith("[ambient] ")
        assert gate.active is False

    def test_name_at_start_activates(self):
        # Spec: `^(oye|hey|hola|ok)?\s*{NOMBRE}\b` — vocative word is optional,
        # the name at the start of a turn is a trigger by itself.
        gate = make_gate()
        decision = gate.process("Tony, ¿puedes ayudarnos?", now=0.0)
        assert decision.respond is True

    def test_antonym_partial_name_no_match(self):
        gate = make_gate()
        # "Antonio" contains "tony"? No — but let's ensure word boundary works
        decision = gate.process("Antonio dijo algo", now=0.0)
        assert decision.respond is False


class TestStrip:
    def test_strips_vocative_prefix(self):
        gate = make_gate()
        decision = gate.process("oye Tony, ¿cómo va todo?", now=0.0)
        assert decision.respond is True
        assert decision.text == "¿cómo va todo?"

    def test_strips_with_comma_and_accent(self):
        gate = make_gate()
        decision = gate.process("Óye Tony: dame el dato", now=0.0)
        assert decision.text == "dame el dato"

    def test_keeps_text_when_window_open(self):
        gate = make_gate()
        gate.process("oye Tony, hola", now=0.0)
        decision = gate.process("y luego qué pasó", now=1.0)
        assert decision.respond is True
        assert decision.text == "y luego qué pasó"


class TestStateMachine:
    def test_window_renews_on_each_directed_turn(self):
        gate = make_gate()
        gate.process("oye Tony, uno", now=0.0)
        d = gate.process("dos", now=29.0)  # within window -> renews
        assert d.respond is True
        d = gate.process("tres", now=58.0)  # 29s after renewal, still within 30s
        assert d.respond is True

    def test_window_expires(self):
        gate = make_gate()
        gate.process("oye Tony, uno", now=0.0)
        d = gate.process("hola de nuevo", now=31.0)  # expired
        assert d.respond is False
        assert gate.active is False

    def test_closing_phrase_goes_idle_and_silent(self):
        gate = make_gate()
        gate.process("oye Tony, uno", now=0.0)
        d = gate.process("gracias, eso era todo", now=1.0)
        assert d.respond is False
        assert d.closing is True
        assert gate.active is False
        # next turn without trigger is ambient again
        d = gate.process("otra cosa", now=2.0)
        assert d.respond is False

    @pytest.mark.parametrize(
        "text",
        ["Eso es todo.", "ya puedes irte", "Gracias, eso es todo"],
    )
    def test_closing_phrase_variants(self, text):
        gate = make_gate()
        gate.process("oye Tony, hola", now=0.0)
        d = gate.process(text, now=1.0)
        assert d.closing is True
        assert gate.active is False

    def test_closing_phrase_from_idle(self):
        gate = make_gate()
        d = gate.process("eso es todo", now=0.0)
        assert d.respond is False
        assert d.closing is True


class TestClockInjection:
    def test_uses_injected_clock(self):
        times = iter([100.0, 200.0])
        gate = make_gate(clock=lambda: next(times))
        gate.process("oye Tony, hola")  # uses 100.0
        d = gate.process("¿sigues ahí?")  # uses 200.0 -> window expired (100 > 30)
        assert d.respond is False
