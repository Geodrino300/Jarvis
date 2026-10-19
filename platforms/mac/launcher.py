"""
Jarvis -- Mac App Launcher
Opens VS Code, Spotify, Chrome, Claude Desktop via 'open' and AppleScript.
"""

import os
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")

WORKSPACE_PATH    = os.getenv("WORKSPACE_PATH", os.path.expanduser("~/projects/jarvis"))
SPOTIFY_TRACK_URI = "spotify:track:39shmbIHICJ2Wxnk1fPSdz"

LAUNCH_VSCODE          = True
LAUNCH_SPOTIFY         = True
LAUNCH_CHROME          = True
LAUNCH_CLAUDE_DESKTOP  = True
ARRANGE_WINDOWS        = True
LAUNCH_WALLPAPER_ENGINE = False  # Not applicable on Mac


def launch_vscode(workspace_path=None):
    """Open VS Code in the workspace directory."""
    path = workspace_path or WORKSPACE_PATH
    try:
        subprocess.Popen(["code", path])
        print("[jarvis] VS Code opening...", flush=True)
    except FileNotFoundError:
        # 'code' CLI not in PATH -- try the app bundle directly
        cli = "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
        try:
            subprocess.Popen([cli, path])
            print("[jarvis] VS Code opening (bundle path)...", flush=True)
        except Exception as e:
            print(f"[jarvis] VS Code error: {e}", flush=True)
    except Exception as e:
        print(f"[jarvis] VS Code error: {e}", flush=True)


def launch_spotify(track_uri=None):
    """Kill and relaunch Spotify, playing the configured track."""
    uri = track_uri or SPOTIFY_TRACK_URI
    try:
        subprocess.run(["pkill", "-x", "Spotify"], capture_output=True)
        time.sleep(3.0)
        subprocess.Popen(["open", uri])
        print(f"[jarvis] Spotify opening: {uri}", flush=True)
    except Exception as e:
        print(f"[jarvis] Spotify error: {e}", flush=True)


def close_spotify():
    """Close Spotify after the activation greeting finishes."""
    try:
        subprocess.run(["pkill", "-x", "Spotify"], capture_output=True)
        print("[jarvis] Spotify closed after greeting.", flush=True)
    except Exception as e:
        print(f"[jarvis] Spotify close error: {e}", flush=True)


def launch_chrome():
    """Open Google Chrome."""
    try:
        subprocess.Popen(["open", "-a", "Google Chrome"])
        print("[jarvis] Chrome opening...", flush=True)
    except Exception as e:
        print(f"[jarvis] Chrome error: {e}", flush=True)


def launch_claude_desktop():
    """Open Claude Desktop app."""
    try:
        subprocess.Popen(["open", "-a", "Claude"])
        print("[jarvis] Claude Desktop opening...", flush=True)
    except Exception as e:
        print(f"[jarvis] Claude Desktop error: {e}", flush=True)


def launch_session(workspace_path=None, mode="daemon"):
    """
    Open VS Code and Claude Code in a new terminal tab.
    Prefers iTerm2 if running, falls back to Terminal.app.
    """
    path = workspace_path or WORKSPACE_PATH

    iterm_script = f"""
tell application "iTerm2"
    tell current window
        create tab with default profile
        tell current session of current tab
            write text "cd '{path}' && claude --continue"
        end tell
    end tell
end tell
"""
    terminal_script = f"""
tell application "Terminal"
    do script "cd '{path}' && claude --continue"
    activate
end tell
"""
    result = subprocess.run(["pgrep", "-x", "iTerm2"], capture_output=True)
    if result.returncode == 0:
        subprocess.Popen(["osascript", "-e", iterm_script])
        print("[jarvis] Claude Code opening in iTerm2...", flush=True)
    else:
        subprocess.Popen(["osascript", "-e", terminal_script])
        print("[jarvis] Claude Code opening in Terminal.app...", flush=True)

    launch_vscode(path)
