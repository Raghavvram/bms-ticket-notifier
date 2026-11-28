import os
import pytest
from main import matches_theatre, matches_format, matches_language, CONFIG, load_env_file

def test_matches_theatre():
    venue = "PVR: VR Chennai, Anna Nagar"
    assert matches_theatre(venue, "VR Mall") is True
    assert matches_theatre(venue, "PVR VR Mall") is True
    assert matches_theatre(venue, "VR Chennai") is True
    assert matches_theatre("PVR: Sathyam, Royapettah", "VR Mall") is False
    assert matches_theatre(venue, "") is True

def test_matches_format():
    assert matches_format("MS-Infinity Vsn 3d", "PXL", "PXL,MS-Infinity Vision") is True
    assert matches_format("MS - Infinity Vision", "", "Infinity Vision") is True
    assert matches_format("Regular", "PXL", "PXL") is True
    assert matches_format("2D", "", "PXL,MS-Infinity Vision") is False
    assert matches_format("2D", "", "") is True

def test_matches_language():
    assert matches_language("English", "English") is True
    assert matches_language("English", "eng") is True
    assert matches_language("Tamil", "English") is False
    assert matches_language("Tamil", "") is True

def test_config_defaults():
    assert CONFIG["location"] == "chennai"
    assert CONFIG["movie"] == "avengers-doomsday"
    assert CONFIG["theatre"] == "VR Chennai"
    assert CONFIG["date"] == "20261221"
    assert CONFIG["language"] == "English"
    assert CONFIG["format"] == "PXL,MS-Infinity Vision"
    assert CONFIG["alert_burst"] == 3
    assert "avengers-doomsday-ms-infinity-vsn/buytickets/ET00526306" in CONFIG["url"]


def test_load_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        '# comment line\n'
        'TEST_NEW_VAR="hello_world"\n'
        "TEST_QUOTED='single'\n"
        'TEST_EXISTING=from_file\n'
    )
    monkeypatch.delenv("TEST_NEW_VAR", raising=False)
    monkeypatch.delenv("TEST_QUOTED", raising=False)
    monkeypatch.setenv("TEST_EXISTING", "already_set")

    load_env_file(env_file)

    assert os.environ["TEST_NEW_VAR"] == "hello_world"
    assert os.environ["TEST_QUOTED"] == "single"
    assert os.environ["TEST_EXISTING"] == "already_set"
