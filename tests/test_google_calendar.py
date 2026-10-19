import unittest
from datetime import datetime, timezone

from core.google_calendar import friendly_event_title, format_agenda, get_agenda, is_calendar_query


class _Request:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class _Events:
    def __init__(self, payload):
        self.payload = payload
        self.kwargs = None

    def list(self, **kwargs):
        self.kwargs = kwargs
        return _Request(self.payload)


class _Service:
    def __init__(self, payload):
        self.resource = _Events(payload)

    def events(self):
        return self.resource


class GoogleCalendarTests(unittest.TestCase):
    def test_read_queries_do_not_match_write_requests(self):
        self.assertTrue(is_calendar_query("what is on my calendar tomorrow"))
        self.assertTrue(is_calendar_query("do I have any meetings"))
        self.assertTrue(is_calendar_query("when is my next exam"))
        self.assertFalse(is_calendar_query("schedule a meeting tomorrow"))

    def test_uses_friendly_course_names(self):
        self.assertEqual(friendly_event_title("COSC 336.003 - Class"), "Data Structures - Class")
        self.assertEqual(friendly_event_title("COSC290.101 � Quiz 2"), "Comp Sci 290 - Quiz 2")
        self.assertEqual(friendly_event_title("COSC 418 - Online class"), "Ethics - Online class")
        self.assertEqual(friendly_event_title("MATH 330 - Class"), "Statistics - Class")
        self.assertEqual(friendly_event_title("POSC108.001 - Class"), "Poli Sci - Class")

    def test_formats_events_and_uses_primary_calendar(self):
        service = _Service({"items": [{
            "summary": "Project review",
            "start": {"dateTime": "2026-10-13T14:00:00+00:00"},
        }]})
        now = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
        result = get_agenda("calendar tomorrow", service=service, now=now)
        self.assertIn("Project review", result)
        self.assertEqual(service.resource.kwargs["calendarId"], "primary")
        self.assertTrue(service.resource.kwargs["singleEvents"])

    def test_empty_agenda(self):
        self.assertEqual(format_agenda([], "today"), "Your calendar is clear for today.")

    def test_next_exam_skips_study_prep_and_uses_friendly_name(self):
        service = _Service({"items": [
            {
                "summary": "Study: COSC 336 quiz prep",
                "start": {"dateTime": "2026-10-13T16:00:00+00:00"},
            },
            {
                "summary": "COSC 290.101 - Quiz 2",
                "start": {"dateTime": "2026-10-14T20:30:00+00:00"},
            },
        ]})
        now = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)

        result = get_agenda("when is my next exam", service=service, now=now)

        self.assertIn("Your next exam is Comp Sci 290 - Quiz 2", result)
        self.assertNotIn("Study", result)


if __name__ == "__main__":
    unittest.main()
