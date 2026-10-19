import unittest

from jarvis import _add_today_agenda


class GreetingAgendaTests(unittest.TestCase):
    def test_appends_today_agenda(self):
        result = _add_today_agenda(
            "Welcome back, sir.",
            lambda query: "You have one event for today: Class, Tuesday at 2:00 PM.",
        )

        self.assertEqual(
            result,
            "Welcome back, sir. You have one event for today: Class, Tuesday at 2:00 PM. "
            "What shall we work on?",
        )

    def test_keeps_greeting_when_calendar_is_unavailable(self):
        def unavailable(_query):
            raise RuntimeError("not connected")

        self.assertEqual(
            _add_today_agenda("Welcome back, sir.", unavailable),
            "Welcome back, sir. What shall we work on?",
        )


if __name__ == "__main__":
    unittest.main()
