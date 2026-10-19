"""
Jarvis -- Mac Window Manager
Positions app windows via AppleScript.

Requires Accessibility permission for the terminal app running Jarvis:
System Preferences > Privacy & Security > Accessibility

Layout tuned for 5120x1440 ultrawide -- edit WINDOW_LAYOUT for your display.
AppleScript bounds format: {left, top, right, bottom}
"""

import subprocess
import time
from core import speech

# Format: (x, y, width, height) -- same convention as Windows version.
# _move_window_mac converts to AppleScript's {left, top, right, bottom}.
#
# Display layout:
#   Left monitor  (1920x1080): x=-1142, y=-1080
#   Right monitor (1920x1080): x=778,   y=-1080
#   MacBook       (1512x982):  x=0,     y=0      (main display, centered below monitors)
WINDOW_LAYOUT = {
    "chrome":   {"process": "Google Chrome",  "pos": (-1142, -1080, 960,  1080)},  # left half of left monitor
    "terminal": {"claude_code": True,          "pos": (-182,  -1080, 960,  1080)},  # right half of left monitor
    "vscode":   {"process": "Code",            "pos": (778,   -1080, 960,  1080)},  # left half of right monitor
    "claude":   {"process": "Claude",          "pos": (1738,  -1080, 960,  540)},   # top-right quarter of right monitor
    "spotify":  {"process": "Spotify",         "pos": (1738,  -540,  960,  540)},   # bottom-right quarter of right monitor
    "jarvis":   {"title": "Jarvis",            "pos": (0,     0,     756,  982)},   # left half of MacBook
}


def _move_window_mac(process_name, x, y, w, h):
    """Move the front window of a process via System Events (works with Electron apps)."""
    script = f"""
tell application "System Events"
    tell process "{process_name}"
        set position of front window to {{{x}, {y}}}
        set size of front window to {{{w}, {h}}}
    end tell
end tell
"""
    result = subprocess.run(["osascript", "-e", script], capture_output=True)
    return result.returncode == 0


def _move_window_by_title(title, x, y, w, h):
    """Move a window by partial title match across all apps via System Events."""
    x2, y2 = x + w, y + h
    script = f"""
tell application "System Events"
    set targetWindow to missing value
    repeat with proc in (processes whose visible is true)
        repeat with w in windows of proc
            if name of w contains "{title}" then
                set position of w to {{{x}, {y}}}
                set size of w to {{{w}, {h}}}
                set targetWindow to w
                exit repeat
            end if
        end repeat
        if targetWindow is not missing value then exit repeat
    end repeat
end tell
"""
    result = subprocess.run(["osascript", "-e", script], capture_output=True)
    return result.returncode == 0


def _move_claude_code_window(x, y, w, h):
    """Move the Claude Code terminal window (iTerm2 tab or Terminal.app window)."""
    x2, y2 = x + w, y + h

    # Try iTerm2 first
    iterm_script = f"""
tell application "iTerm2"
    set targetWindow to missing value
    repeat with w in windows
        if (name of w) contains "claude" then
            set targetWindow to w
            exit repeat
        end if
    end repeat
    if targetWindow is not missing value then
        set bounds of targetWindow to {{{x}, {y}, {x2}, {y2}}}
        return "ok"
    end if
    return "notfound"
end tell
"""
    r = subprocess.run(["osascript", "-e", iterm_script], capture_output=True, text=True)
    if r.returncode == 0 and "ok" in r.stdout.strip():
        return True

    # Fall back to Terminal.app
    terminal_script = f"""
tell application "Terminal"
    set targetWindow to missing value
    repeat with w in windows
        if (name of w) contains "claude" then
            set targetWindow to w
            exit repeat
        end if
    end repeat
    if targetWindow is not missing value then
        set bounds of targetWindow to {{{x}, {y}, {x2}, {y2}}}
        return "ok"
    end if
    return "notfound"
end tell
"""
    r2 = subprocess.run(["osascript", "-e", terminal_script], capture_output=True, text=True)
    return r2.returncode == 0 and "ok" in r2.stdout.strip()


# Electron apps restore their own window position after a short delay.
# These get a second move pass after a brief wait.
ELECTRON_PROCESSES = {"Code"}


def arrange_windows():
    """Position all windows to the saved layout."""
    moved, missing = [], []

    for name, cfg in WINDOW_LAYOUT.items():
        x, y, w, h = cfg["pos"]
        ok = False

        if cfg.get("claude_code"):
            ok = _move_claude_code_window(x, y, w, h)
        elif "process" in cfg:
            ok = _move_window_mac(cfg["process"], x, y, w, h)
        elif "title" in cfg:
            ok = _move_window_by_title(cfg["title"], x, y, w, h)

        if ok:
            moved.append(name)
            print(f"[layout] Moved {name} -> {cfg['pos']}", flush=True)
        else:
            label = cfg.get("process") or cfg.get("title") or name
            print(f"[layout] Window not found: {label}", flush=True)
            missing.append(name)

    # Second pass for Electron apps that restore position after initial move
    electron_cfgs = [(n, c) for n, c in WINDOW_LAYOUT.items()
                     if c.get("process") in ELECTRON_PROCESSES]
    if electron_cfgs:
        time.sleep(1.5)
        for name, cfg in electron_cfgs:
            x, y, w, h = cfg["pos"]
            if _move_window_mac(cfg["process"], x, y, w, h):
                print(f"[layout] Re-settled {name} -> {cfg['pos']}", flush=True)

    if missing:
        print(f"[layout] Couldn't find: {', '.join(missing)}.", flush=True)
