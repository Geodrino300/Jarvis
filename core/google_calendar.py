"""Read-only Google Calendar access using Google's official OAuth client."""

import json
import os
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[1] / ".env")

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
ASSESSMENT_TERMS = ("exam", "quiz", "test", "midterm", "final")
COURSE_ALIASES = (
    (re.compile(r"\bCOSC\s*336(?:\.\d+)?\b", re.IGNORECASE), "Data Structures"),
    (re.compile(r"\bCOSC\s*290(?:\.\d+)?\b", re.IGNORECASE), "Comp Sci 290"),
    (re.compile(r"\bCOSC\s*418(?:\.\d+)?\b", re.IGNORECASE), "Ethics"),
    (re.compile(r"\bMATH\s*330(?:\.\d+)?\b", re.IGNORECASE), "Statistics"),
    (re.compile(r"\bPOSC\s*108(?:\.\d+)?\b", re.IGNORECASE), "Poli Sci"),
)


class CalendarNotConfigured(RuntimeError):
    """Raised when the one-time Google OAuth setup has not been completed."""


def _state_dir():
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    return Path(base) / "Jarvis"


def client_secret_path():
    configured = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "").strip()
    return Path(configured).expanduser() if configured else _state_dir() / "google-calendar-client.json"


def token_path():
    configured = os.getenv("GOOGLE_CALENDAR_TOKEN", "").strip()
    return Path(configured).expanduser() if configured else _state_dir() / "google-calendar-token.json"


def is_calendar_query(text):
    """Return True only for read-style agenda questions, never scheduling requests."""
    lowered = text.strip().lower()
    exact = {
        "agenda", "my agenda", "today's agenda", "todays agenda",
        "calendar today", "calendar tomorrow", "upcoming meetings",
        "what meetings do i have", "do i have any meetings",
    }
    if lowered in exact:
        return True
    topic = any(word in lowered for word in (
        "calendar", "agenda", "meeting", "appointments", *ASSESSMENT_TERMS,
    ))
    read_intent = any(word in lowered for word in (
        "what", "when", "show", "read", "check", "today", "tomorrow", "upcoming", "next", "have",
    ))
    write_intent = any(word in lowered for word in (
        "create", "add", "book", "schedule", "cancel", "delete", "move", "invite",
    ))
    return topic and read_intent and not write_intent


def _save_token(credentials):
    path = token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(credentials.to_json(), encoding="utf-8")


def authorize(interactive=False):
    """Load/refresh credentials; start browser consent only when explicitly requested."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise CalendarNotConfigured(
            "Google Calendar packages are missing. Install requirements-calendar.txt."
        ) from exc

    credentials = None
    token = token_path()
    if token.exists():
        try:
            credentials = Credentials.from_authorized_user_file(str(token), SCOPES)
        except (ValueError, json.JSONDecodeError):
            credentials = None

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        _save_token(credentials)
    if credentials and credentials.valid:
        return credentials

    if not interactive:
        raise CalendarNotConfigured(
            "Google Calendar is not connected. Run scripts/setup-google-calendar.py once."
        )

    secret = client_secret_path()
    if not secret.exists():
        raise CalendarNotConfigured(
            f"Put a Google Desktop OAuth client JSON at {secret}, then run this setup again."
        )

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    _save_token(credentials)
    return credentials


def _query_window(text, now):
    lowered = text.lower()
    local_now = now.astimezone()
    zone = local_now.tzinfo
    if "next" in lowered and any(term in lowered for term in ASSESSMENT_TERMS):
        return local_now, local_now + timedelta(days=365), "your next exam"
    if "tomorrow" in lowered:
        day = local_now.date() + timedelta(days=1)
        return (
            datetime.combine(day, time.min, zone),
            datetime.combine(day + timedelta(days=1), time.min, zone),
            "tomorrow",
        )
    if "today" in lowered or "agenda" in lowered:
        return (
            local_now,
            datetime.combine(local_now.date() + timedelta(days=1), time.min, zone),
            "today",
        )
    return local_now, local_now + timedelta(days=7), "the next seven days"


def _format_start(start, zone):
    if "dateTime" in start:
        value = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00")).astimezone(zone)
        return value.strftime("%A at %I:%M %p").replace(" 0", " ")
    if "date" in start:
        value = date.fromisoformat(start["date"])
        return value.strftime("%A") + " all day"
    return "at an unspecified time"


def friendly_event_title(title):
    """Replace known course codes with names that sound natural when spoken."""
    friendly = title.replace("\ufffd", "-").replace("–", "-").replace("—", "-")
    for pattern, replacement in COURSE_ALIASES:
        friendly = pattern.sub(replacement, friendly)
    return friendly


def _is_assessment_event(event):
    summary = (event.get("summary") or "").lower()
    if any(word in summary for word in ("study", "prep", "review")):
        return False
    return any(term in summary for term in ASSESSMENT_TERMS)


def format_agenda(events, period, now=None):
    now = now or datetime.now().astimezone()
    zone = now.astimezone().tzinfo
    if not events:
        return f"Your calendar is clear for {period}."

    items = []
    for event in events[:5]:
        title = friendly_event_title(event.get("summary") or "Untitled event")
        items.append(f"{title}, {_format_start(event.get('start', {}), zone)}")
    prefix = f"You have {len(events)} event{'s' if len(events) != 1 else ''} for {period}: "
    return prefix + "; ".join(items) + "."


def get_agenda(text, service=None, now=None):
    """Fetch upcoming primary-calendar events with read-only scope."""
    now = now or datetime.now().astimezone()
    start, end, period = _query_window(text, now)
    if service is None:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise CalendarNotConfigured(
                "Google Calendar packages are missing. Install requirements-calendar.txt."
            ) from exc
        service = build("calendar", "v3", credentials=authorize(), cache_discovery=False)

    result = service.events().list(
        calendarId="primary",
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        maxResults=100,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    events = result.get("items", [])
    lowered = text.lower()
    if any(term in lowered for term in ASSESSMENT_TERMS):
        assessments = [event for event in events if _is_assessment_event(event)]
        if not assessments:
            return "I couldn't find an upcoming exam on your calendar."
        if "next" in lowered:
            event = assessments[0]
            title = friendly_event_title(event.get("summary") or "Untitled exam")
            return f"Your next exam is {title}, {_format_start(event.get('start', {}), now.astimezone().tzinfo)}."
        events = assessments

    return format_agenda(events, period, now=now)
