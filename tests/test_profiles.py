import pytest

from profiles import (
    AVATARS,
    DEFAULT_VOICE_ID,
    UNIVERSITIES,
    VOICES,
    get_voice_id,
    resolve_profile,
)


def test_get_voice_id_known_names():
    assert get_voice_id("mateo") == VOICES["mateo"]
    assert get_voice_id("daniela") == VOICES["daniela"]
    assert get_voice_id("MATEO") == VOICES["mateo"]


def test_get_voice_id_custom_uuid():
    custom_uuid = "12345678-1234-1234-1234-123456789abc"
    assert get_voice_id(custom_uuid) == custom_uuid


def test_get_voice_id_none():
    assert get_voice_id(None) == DEFAULT_VOICE_ID


def test_resolve_profile_defaults():
    name, image_url, voice_id, instructions, aliases = resolve_profile()
    assert name == "Tony"
    assert image_url == AVATARS["Tony"]["image_url"]
    assert voice_id == VOICES["mateo"]
    assert "Eres Tony" in instructions
    assert "Toni" in aliases


def test_resolve_profile_clau_tec():
    name, image_url, voice_id, instructions, aliases = resolve_profile("Clau", "TEC")
    assert name == "Clau"
    assert image_url == AVATARS["Clau"]["image_url"]
    assert voice_id == VOICES["daniela"]
    assert "Eres Clau" in instructions
    assert "Tecnologico de Monterrey" in instructions
    assert "Claudia" in aliases


def test_resolve_profile_julius_unam():
    name, image_url, voice_id, instructions, aliases = resolve_profile("Julius", "UNAM")
    assert name == "Julius"
    assert image_url == AVATARS["Julius"]["image_url"]
    assert voice_id == VOICES["mateo"]
    assert "Eres Julius" in instructions
    assert "Universidad Nacional Autonoma de Mexico" in instructions
    assert "Yulius" in aliases
    assert "Julio" in aliases


def test_resolve_profile_invalid_avatar():
    with pytest.raises(ValueError, match="Avatar 'Desconocido' no valido"):
        resolve_profile("Desconocido", "UP")


def test_resolve_profile_invalid_university():
    with pytest.raises(ValueError, match="Universidad 'HARVARD' no valida"):
        resolve_profile("Tony", "HARVARD")
