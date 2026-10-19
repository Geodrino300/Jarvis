"""Jarvis -- Windows app launcher."""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")

WORKSPACE_PATH       = os.getenv("WORKSPACE_PATH", str(Path(__file__).parents[2]))
SPOTIFY_TRACK_URI    = "spotify:track:39shmbIHICJ2Wxnk1fPSdz?si=d61d5cf1a105422d"

# Toggle each app on or off
LAUNCH_VSCODE          = True
LAUNCH_SPOTIFY         = True
LAUNCH_CHROME          = False  # Browser launch is intentionally disabled.
LAUNCH_CODEX           = True
ARRANGE_WINDOWS        = True
LAUNCH_WALLPAPER_ENGINE = False  # [BETA] Sends Shift+F1 to Wallpaper Engine


def launch_session(workspace_path, mode="daemon"):
    """Open the workspace and the installed Codex desktop app."""
    script_path = str(Path(__file__).parent / "launch-session.ps1")
    args = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path,
            "-WorkspacePath", workspace_path]
    if not LAUNCH_CODEX:
        args.append("-SkipCodex")
    subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW)


def launch_spotify(track_uri=None):
    """Kill and relaunch Spotify, playing the configured track from the start."""
    uri = track_uri or SPOTIFY_TRACK_URI
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "Spotify.exe"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            capture_output=True,
        )
        time.sleep(3.0)
        os.startfile(uri)
        print(f"[jarvis] Spotify opening: {uri}", flush=True)
    except Exception as e:
        print(f"[jarvis] Spotify error: {e}", flush=True)


def close_spotify():
    """Close Spotify after the activation greeting finishes."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "Spotify.exe"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            capture_output=True,
        )
        print("[jarvis] Spotify closed after greeting.", flush=True)
    except Exception as e:
        print(f"[jarvis] Spotify close error: {e}", flush=True)


def launch_chrome():
    """Open Google Chrome."""
    try:
        subprocess.Popen(["chrome"], creationflags=subprocess.CREATE_NO_WINDOW)
        print("[jarvis] Chrome opening...", flush=True)
    except FileNotFoundError:
        try:
            subprocess.Popen(
                [r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            print("[jarvis] Chrome opening (full path)...", flush=True)
        except Exception as e:
            print(f"[jarvis] Chrome error: {e}", flush=True)
    except Exception as e:
        print(f"[jarvis] Chrome error: {e}", flush=True)


def launch_wallpaper_engine():
    """Focus Wallpaper Engine then send Shift+F1 to trigger the hotkey."""
    try:
        import ctypes
        import win32gui, win32con

        INPUT_KEYBOARD  = 1
        KEYEVENTF_KEYUP = 0x0002
        VK_SHIFT        = 0x10
        VK_F1           = 0x70

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk",         ctypes.c_ushort),
                ("wScan",       ctypes.c_ushort),
                ("dwFlags",     ctypes.c_ulong),
                ("time",        ctypes.c_ulong),
                ("dwExtraInfo", ctypes.c_ulonglong),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type",    ctypes.c_ulong),
                ("ki",      KEYBDINPUT),
                ("padding", ctypes.c_ubyte * 8),
            ]

        def make_key(vk, flags=0):
            i = INPUT()
            i.type    = INPUT_KEYBOARD
            i.ki.wVk  = vk
            i.ki.dwFlags = flags
            return i

        # Find and focus Wallpaper Engine window before sending hotkey
        hwnd = win32gui.FindWindow("Progman", None)
        matches = []
        def cb(h, _):
            t = win32gui.GetWindowText(h)
            if "wallpaper" in t.lower():
                matches.append(h)
        win32gui.EnumWindows(cb, None)
        if matches:
            win32gui.SetForegroundWindow(matches[0])
            time.sleep(0.2)

        inputs = (INPUT * 4)(
            make_key(VK_SHIFT),
            make_key(VK_F1),
            make_key(VK_F1,    KEYEVENTF_KEYUP),
            make_key(VK_SHIFT, KEYEVENTF_KEYUP),
        )
        ctypes.windll.user32.SendInput(4, inputs, ctypes.sizeof(INPUT))
        print("[jarvis] Wallpaper Engine activated (Shift+F1)", flush=True)
    except Exception as e:
        print(f"[jarvis] Wallpaper Engine error: {e}", flush=True)
