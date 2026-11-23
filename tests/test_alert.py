import pytest
from unittest.mock import patch, MagicMock
from main import apply_request_jitter, build_alert_content, send_urgent_alert

def test_apply_request_jitter():
    with patch("time.sleep") as mock_sleep:
        jitter = apply_request_jitter(min_sec=0.1, max_sec=0.2)
        assert 0.1 <= jitter <= 0.2
        mock_sleep.assert_called_once_with(jitter)

def test_build_alert_content():
    changes = ["🚨 URGENT: 📅 DATE BOOKING OPENED: 20261221"]
    movie_info = {"name": "Avengers: Doomsday", "language": "English"}
    booking_url = "https://in.bookmyshow.com/movies/chennai/avengers-doomsday/buytickets/ET00526306"

    subject, plain, html = build_alert_content(
        changes, shows=[], movie_info=movie_info, booking_url=booking_url
    )

    assert "🚨 URGENT" in subject
    assert "AVENGERS: DOOMSDAY" in subject
    assert booking_url in plain
    assert f'href="{booking_url}"' in html
    assert "BOOK TICKETS NOW" in html

def test_send_urgent_alert_burst():
    changes = ["🚨 URGENT: 📅 DATE BOOKING OPENED: 20261221"]
    movie_info = {"name": "Avengers: Doomsday", "language": "English"}
    booking_url = "https://in.bookmyshow.com/movies/chennai/avengers-doomsday/buytickets/ET00526306"

    with patch("main.send_email_single") as mock_send_email, \
         patch("main.send_desktop_notification") as mock_desktop:
        mock_send_email.return_value = True

        sent_count = send_urgent_alert(
            changes, shows=[], movie_info=movie_info, booking_url=booking_url, burst_count=3
        )
        assert sent_count == 3
        assert mock_send_email.call_count == 3
        mock_desktop.assert_called_once()
