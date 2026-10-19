"""
Jarvis -- Voice Loop
Always-on wake word listener. Platform-agnostic.
Callers inject platform-specific functions via a SimpleNamespace.

Required platform interface:
    platform.send_to_assistant(text: str) -> None
    platform.arrange_windows()              -> None
    platform.beep()                         -> None
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import sounddevice as sd
import numpy as np
from dotenv import load_dotenv

from core.commands import _LAYOUT_TRIGGERS, normalize_selection
from core.hue import is_hue_command, parse_and_execute, HueBridge
from core.google_calendar import CalendarNotConfigured, get_agenda, is_calendar_query
from core import speech, transcription

load_dotenv(Path(__file__).parents[1] / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WORKSPACE_PATH    = os.getenv("WORKSPACE_PATH", "")
CLAUDE_MD_PATH    = os.path.join(WORKSPACE_PATH, "CLAUDE.md")
JARVIS_ROOT       = Path(__file__).parents[1]
PROFILE_PATH      = JARVIS_ROOT / "context" / "profile.md"
STARTUP_DELAY     = 3

conversation_history = []

_hue_bridge = None


def _get_hue_bridge():
    """Lazy-load the Hue bridge. Returns None if not configured."""
    global _hue_bridge
    if _hue_bridge is None:
        try:
            _hue_bridge = HueBridge()
        except RuntimeError as e:
            print(f"[hue] Not configured: {e}", flush=True)
            _hue_bridge = False
        except Exception as e:
            print(f"[hue] Load error: {e}", flush=True)
            _hue_bridge = False
    return _hue_bridge if _hue_bridge else None


def _read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _extract_announcement(profile_text):
    """Pull the scripted announcement out of the profile, if present."""
    marker = "## Announcement"
    idx = profile_text.find(marker)
    if idx == -1:
        return ""
    section = profile_text[idx:]
    # Grab text inside the first quoted block
    q_start = section.find('"')
    q_end   = section.find('"', q_start + 1)
    if q_start != -1 and q_end != -1:
        return section[q_start + 1:q_end]
    return ""


def get_voice_response(user_text):
    """
    Brief JARVIS-style acknowledgment for the spoken command.
    Called in parallel with the local coding-agent dispatch -- 1-2 sentences max.
    """
    if not ANTHROPIC_API_KEY:
        return "On it, sir."

    now         = datetime.now()
    claude_md   = _read_file(CLAUDE_MD_PATH)
    profile     = _read_file(str(PROFILE_PATH))
    announcement = _extract_announcement(profile)

    announce_block = ""
    if announcement:
        announce_block = f"""
SCRIPTED ANNOUNCEMENT (deliver word for word if asked about announcements):
{announcement}
"""

    system = f"""You are JARVIS, Tony Stark's AI assistant -- calm, British, precise, occasionally dry.

The user has just issued a voice command that has been sent to Codex for execution.
Your job: give a brief spoken acknowledgment (1-2 sentences MAX).
Do not use markdown, bullet points, or code blocks -- this is spoken aloud.
{announce_block}
If the user's command asks whether you have an announcement, something to say, or anything to announce --
respond with the scripted announcement above, word for word. Do not paraphrase or shorten it.

Current time: {now.strftime("%I:%M %p on %B %d")}

Project context (CLAUDE.md):
{claude_md[:600]}

User profile:
{profile[:400]}"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        conversation_history.append({"role": "user", "content": user_text})
        messages = conversation_history[-10:]

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            system=system,
            messages=messages,
        )
        reply = response.content[0].text.strip()
        conversation_history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        print(f"[voice] Claude API error: {e}", flush=True)
        return "On it, sir."


def handle_hue_command(text):
    """Execute a light command locally and speak the result."""
    bridge = _get_hue_bridge()
    if not bridge:
        speech.speak("Hue bridge is not configured, sir. Run the setup script to connect.")
        return
    try:
        result = parse_and_execute(text, bridge)
        if result:
            speech.speak(result)
        else:
            speech.speak("I didn't quite catch that light command, sir.")
    except Exception as e:
        print(f"[hue] Command error: {e}", flush=True)
        speech.speak("Something went wrong with the lights, sir.")


def handle_calendar_command(text):
    """Read the user's agenda without granting Calendar write access."""
    try:
        speech.speak(get_agenda(text))
    except CalendarNotConfigured as e:
        print(f"[calendar] {e}", flush=True)
        speech.speak("Google Calendar needs its one-time read-only setup, sir.")
    except Exception as e:
        print(f"[calendar] Query error: {e}", flush=True)
        speech.speak("I couldn't read the calendar just now, sir.")


def handle_command(text, platform):
    """
    Dispatch a transcribed command:
    1. Layout trigger  -> arrange windows via platform (local, instant)
    2. Hue command     -> control lights locally, speak result
    3. Calendar query -> read the primary Google Calendar
    4. Selection phrase -> send keypress via platform terminal
    5. Everything else -> send to Codex + speak acknowledgment
    """
    print(f"[voice] Command: {text}", flush=True)
    lowered = text.strip().lower()

    if lowered in _LAYOUT_TRIGGERS:
        threading.Thread(target=platform.arrange_windows, daemon=True).start()
        return

    if is_hue_command(lowered):
        threading.Thread(target=handle_hue_command, args=(text,), daemon=True).start()
        return

    if is_calendar_query(lowered):
        threading.Thread(target=handle_calendar_command, args=(text,), daemon=True).start()
        return

    t1 = threading.Thread(target=platform.send_to_assistant, args=(text,), daemon=True)
    t2 = threading.Thread(target=lambda: speech.speak(get_voice_response(text)), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


def voice_loop(vosk_model, platform, control=None):
    """
    Continuously listen for the wake word "Jarvis" using full-vocab Vosk.
    On detection: beep -> record -> transcribe -> dispatch.
    """
    from vosk import KaldiRecognizer

    chunk_size = 4000  # ~250ms at 16kHz
    print('[voice] Listening for "Jarvis"...', flush=True)

    while not (control and control.should_stop):
        if control and not control.wait_until_resumed():
            break
        wake_rec = KaldiRecognizer(vosk_model, transcription.SAMPLE_RATE)
        detected = False
        with sd.InputStream(
            samplerate=transcription.SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=chunk_size,
        ) as stream:
            while not (control and (control.is_paused or control.should_stop)):
                chunk, _ = stream.read(chunk_size)
                wake_rec.AcceptWaveform(chunk.tobytes())
                partial = json.loads(wake_rec.PartialResult()).get("partial", "").lower()
                if "jarvis" in partial:
                    detected = True
                    break

        if not detected:
            continue

        print("[voice] Wake word detected.", flush=True)
        platform.beep()
        # The beep call is blocking, so it has finished before recording starts.
        # Starting immediately avoids clipping short commands spoken after the beep.
        audio = transcription.record_until_silence(control=control)
        if control and (control.is_paused or control.should_stop):
            continue
        text = transcription.transcribe(audio, vosk_model=vosk_model) if audio.size else None
        if text:
            handle_command(text, platform)
        else:
            speech.speak("I didn't catch that, sir. Please try again.")
        print('[voice] Listening for "Jarvis"...', flush=True)


def run(platform, startup_delay=STARTUP_DELAY, control=None):
    """Load Vosk model and start the voice loop."""
    from vosk import Model, SetLogLevel
    SetLogLevel(-1)

    if startup_delay > 0:
        print(f"[voice] Starting in {startup_delay}s (waiting for the coding agent to open)...", flush=True)
        time.sleep(startup_delay)

    print("[voice] Loading Vosk model (downloads ~50MB on first run)...", flush=True)
    model = Model(lang="en-us")
    print("[voice] Vosk model ready.", flush=True)

    voice_loop(model, platform, control=control)
