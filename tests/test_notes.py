"""Tests for notes.py helpers. Pure unit tests: no network, no LLM."""

from datetime import datetime

from notes import (
    build_notes_filename,
    extract_meet_code,
    render_notes_document,
    save_notes,
    transcript_from_chat_ctx,
)


class TestExtractMeetCode:
    def test_google_meet_url(self):
        assert extract_meet_code("https://meet.google.com/abc-defg-hij") == "abc-defg-hij"

    def test_google_meet_trailing_slash(self):
        assert extract_meet_code("https://meet.google.com/abc-defg-hij/") == "abc-defg-hij"

    def test_zoom_url(self):
        code = extract_meet_code("https://us06web.zoom.us/j/12345678901?pwd=abc123")
        assert code == "zoom-12345678901"

    def test_fallback_sanitizes(self):
        code = extract_meet_code("https://teams.live.com/meet/123 456?p=x")
        assert " " not in code and "?" not in code


class TestFilename:
    def test_format(self):
        now = datetime(2026, 8, 31, 15, 30)
        assert build_notes_filename("abc-defg-hij", now) == "abc-defg-hij-20260831-1530.md"


class TestRenderDocument:
    def test_header_with_objective(self):
        now = datetime(2026, 8, 31, 15, 30)
        doc = render_notes_document("## Acciones\n- [ ] X", "abc-defg-hij", objective="Cierre de taller", now=now)
        assert "Acciones y Decisiones — abc-defg-hij" in doc
        assert "2026-08-31 15:30" in doc
        assert "Objetivo de la sesión: Cierre de taller" in doc
        assert "## Acciones" in doc

    def test_header_without_objective(self):
        doc = render_notes_document("body", "abc-defg-hij", now=datetime(2026, 8, 31))
        assert "Objetivo" not in doc


class TestSaveNotes:
    def test_creates_dir_and_writes(self, tmp_path):
        out = tmp_path / "memoria"
        path = save_notes(out, "meet-1.md", "contenido")
        assert path.exists()
        assert path.read_text(encoding="utf-8") == "contenido"


class TestTranscript:
    def test_flattens_roles(self):
        class FakeItem:
            def __init__(self, role, text):
                self.role = role
                self.text_content = text

        class FakeCtx:
            items = [
                FakeItem("user", "hola"),
                FakeItem("assistant", "qué tal"),
                FakeItem("system", "ignorado"),
            ]

        text = transcript_from_chat_ctx(FakeCtx())
        assert "Participante: hola" in text
        assert "Asistente: qué tal" in text
        assert "ignorado" not in text
