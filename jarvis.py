#!/usr/bin/env python3
"""
Jarvis -- Entry Point
Detects platform, wires core + platform modules, runs the session.

Usage:
    python jarvis.py                  # daemon mode (wait for double snap)
    python jarvis.py --mode autostart # launch immediately (boot / Task Scheduler)
"""

import os
import sys
import time
import threading
import argparse
from pathlib import Path
from types import SimpleNamespace
from dotenv import load_dotenv

# Ensure the repo root is on the path so 'core' and 'platforms' are importable
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv(Path(__file__).parent / ".env")

# ─── ARGS ─────────────────────────────────────────────────────────────────────
_parser = argparse.ArgumentParser(description="Jarvis voice assistant")
_parser.add_argument("--mode", choices=["daemon", "autostart"], default="daemon")
_args, _ = _parser.parse_known_args()
MODE = _args.mode

WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", str(Path(__file__).parent))
STRATEGY_PATH  = os.path.join(WORKSPACE_PATH, "context", "profile.md")

# ─── PLATFORM DETECTION ───────────────────────────────────────────────────────
if sys.platform == "win32":
    from platforms.windows import launcher, window_manager, terminal
elif sys.platform == "darwin":
    from platforms.mac import launcher, window_manager, terminal
else:
    raise RuntimeError(f"Unsupported platform: {sys.platform}")

platform = SimpleNamespace(
    send_to_assistant=(
        terminal.send_to_codex if sys.platform == "win32"
        else terminal.send_to_claude_code
    ),
    arrange_windows=window_manager.arrange_windows,
    beep=terminal.beep,
    launcher=launcher,
)


# ─── SESSION ──────────────────────────────────────────────────────────────────

def _add_today_agenda(greeting_text, agenda_loader):
    """Append today's agenda locally without sending calendar data to the greeting model."""
    closing = "What shall we work on?"
    try:
        agenda = agenda_loader("calendar today")
    except Exception as exc:
        print(f"[calendar] Greeting agenda unavailable: {exc}", flush=True)
        return f"{greeting_text.rstrip()} {closing}".strip()

    return f"{greeting_text.rstrip()} {agenda.strip()} {closing}".strip()


def run_session(control=None):
    from core import speech, greeting
    from core.google_calendar import get_agenda
    from core import voice_loop as vl

    # Wallpaper Engine (Windows only) + Spotify -- fire immediately
    if sys.platform == "win32" and launcher.LAUNCH_WALLPAPER_ENGINE:
        launcher.launch_wallpaper_engine()
    spotify_thread = None
    if launcher.LAUNCH_SPOTIFY:
        spotify_thread = threading.Thread(target=launcher.launch_spotify, daemon=True)
        spotify_thread.start()

    # Pre-fetch greeting in background while Spotify loads
    _greeting_result = {}

    def _fetch_greeting():
        print("[jarvis] Generating greeting...", flush=True)
        loc = greeting.get_location()
        wth = greeting.get_weather(loc["lat"], loc["lon"])
        greeting_text = greeting.generate_greeting(loc, wth, STRATEGY_PATH)
        _greeting_result["text"] = _add_today_agenda(greeting_text, get_agenda)

    fetch_thread = threading.Thread(target=_fetch_greeting, daemon=True)
    fetch_thread.start()

    # Wait for greeting, then speak it
    time.sleep(2)
    fetch_thread.join()
    speak_thread = threading.Thread(
        target=speech.speak,
        args=(_greeting_result.get("text", "Welcome back, sir."),),
        daemon=True,
    )
    speak_thread.start()

    # Launch apps 2s after greeting starts
    time.sleep(2)
    launcher.launch_session(WORKSPACE_PATH, MODE)
    if launcher.LAUNCH_CHROME:
        launcher.launch_chrome()

    if launcher.ARRANGE_WINDOWS:
        def _delayed_arrange():
            time.sleep(4)
            platform.arrange_windows()
        threading.Thread(target=_delayed_arrange, daemon=True).start()

    speak_thread.join()

    if spotify_thread:
        spotify_thread.join(timeout=5)
        launcher.close_spotify()

    # Startup delay: 0 if we already waited, 3 in daemon mode for the coding agent to open
    delay = 0 if MODE == "autostart" else 3
    vl.run(platform, startup_delay=delay, control=control)
    print("[jarvis] Session launched. Voice loop started. Standing by.", flush=True)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

_single_instance_handle = None


def _acquire_single_instance():
    """Prevent multiple microphone listeners from running for this user session."""
    global _single_instance_handle
    if sys.platform != "win32":
        return True

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.CreateMutexW(None, False, "Local\\JarvisVoiceAssistant")
    if not handle:
        raise OSError("Unable to create the Jarvis single-instance mutex")
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        print("[jarvis] A listener is already running; exiting.", flush=True)
        return False
    _single_instance_handle = handle
    return True


def main():
    if not _acquire_single_instance():
        return
    from core.runtime import RuntimeControl

    control = RuntimeControl()
    tray = None
    if sys.platform == "win32":
        try:
            from platforms.windows.tray import start_tray
            tray = start_tray(control)
            print("[jarvis] System tray controls ready.", flush=True)
        except Exception as e:
            print(f"[jarvis] Tray unavailable: {e}", flush=True)

    try:
        if MODE == "autostart":
            print("[jarvis] Autostart mode -- launching session immediately...", flush=True)
            run_session(control=control)
        else:
            from core.snap import wait_for_double_snap
            print("[jarvis] Listening for double snap...", flush=True)
            if wait_for_double_snap(control=control):
                run_session(control=control)
    finally:
        if tray:
            tray.stop()


if __name__ == "__main__":
    main()
