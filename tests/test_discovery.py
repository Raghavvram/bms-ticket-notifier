import pytest
from main import discover_format_event_codes, detect_dual_triggers

SAMPLE_BMS_DATA = {
    "data": {
        "bottomSheetData": {
            "format-selector": {
                "widgets": [
                    {
                        "type": "chip-list",
                        "text": "English",
                        "data": [
                            {
                                "title": "2D",
                                "cta": {
                                    "analytics": {"format": "2D"},
                                    "additionalData": {
                                        "eventCode": "ET00439706",
                                        "language": "English",
                                    }
                                }
                            },
                            {
                                "title": "MS - Infinity Vision",
                                "cta": {
                                    "analytics": {"format": "MS - Infinity Vision"},
                                    "additionalData": {
                                        "eventCode": "ET00526287",
                                        "language": "English",
                                    }
                                }
                            },
                            {
                                "title": "MS-Infinity Vsn 3d",
                                "cta": {
                                    "analytics": {"format": "MS-Infinity Vsn 3d"},
                                    "additionalData": {
                                        "eventCode": "ET00526306",
                                        "language": "English",
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "type": "chip-list",
                        "text": "Tamil",
                        "data": [
                            {
                                "title": "MS-Infinity Vsn 3d",
                                "cta": {
                                    "analytics": {"format": "MS-Infinity Vsn 3d"},
                                    "additionalData": {
                                        "eventCode": "ET00526312",
                                        "language": "Tamil",
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
    }
}

def test_discover_format_event_codes_matching():
    # Matching English + Infinity Vision
    res = discover_format_event_codes(SAMPLE_BMS_DATA, target_lang="English", target_format="Infinity Vision")
    event_codes = [x[0] for x in res]
    assert "ET00526287" in event_codes
    assert "ET00526306" in event_codes
    assert "ET00439706" not in event_codes
    assert "ET00526312" not in event_codes

def test_discover_format_event_codes_fallback():
    # Non-matching format filter falls back to all active formats to prevent missing tickets
    res = discover_format_event_codes(SAMPLE_BMS_DATA, target_lang="English", target_format="NonExistentFormat")
    event_codes = [x[0] for x in res]
    assert len(event_codes) == 4

def test_detect_dual_triggers_date_opened():
    old_state = {
        "dates": {"20261221": "NOT_OPEN"},
        "shows": {}
    }
    new_state = {
        "dates": {"20261221": "BOOKABLE"},
        "shows": {}
    }
    triggers = detect_dual_triggers(old_state, new_state, target_date="20261221")
    assert any("DATE BOOKING OPENED: 20261221" in t for t in triggers)
    assert any("🚨 URGENT" in t for t in triggers)

def test_detect_dual_triggers_tickets_available():
    key = "PCAN|13221|20261221|PRIME"
    old_state = {
        "dates": {"20261221": "BOOKABLE"},
        "shows": {key: {"venue": "PVR: VR Chennai, Anna Nagar", "time": "09:35 AM", "date": "20261221", "cat": "PRIME", "price": "270", "status": "0"}}
    }
    new_state = {
        "dates": {"20261221": "BOOKABLE"},
        "shows": {key: {"venue": "PVR: VR Chennai, Anna Nagar", "time": "09:35 AM", "date": "20261221", "cat": "PRIME", "price": "270", "status": "3"}}
    }
    triggers = detect_dual_triggers(old_state, new_state, target_date="20261221")
    assert any("TICKETS OPEN" in t for t in triggers)
    assert any("AVAILABLE" in t for t in triggers)
