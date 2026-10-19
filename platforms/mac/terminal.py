"""
Jarvis -- Mac Terminal Integration
Sends commands to Claude Code via AppleScript.
Supports Terminal.app and iTerm2 (auto-detected).
"""

import subprocess
from core.commands import normalize_selection

# ─── KEY MAP ─────────────────────────────────────────────────────────────────
# Converts SendKeys-style tokens to AppleScript keystrokes / key codes.
_KEY_MAP = {
    "{ENTER}": "key code 36",
    "{ESC}":   "key code 53",
    "{UP}":    "key code 126",
    "{DOWN}":  "key code 125",
    "{TAB}":   "key code 48",
}


def beep():
    """Short confirmation beep via afplay (ships with macOS)."""
    subprocess.Popen(
        ["afplay", "/System/Library/Sounds/Tink.aiff"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _is_iterm2_running():
    result = subprocess.run(["pgrep", "-x", "iTerm2"], capture_output=True)
    return result.returncode == 0


def _sendkeys_to_applescript(sendkeys_str):
    """
    Convert a SendKeys-style string (e.g. 'y{ENTER}') to AppleScript keystroke lines.
    Returns a newline-joined block ready to embed in a 'tell application "System Events"' block.
    """
    lines = []
    i = 0
    while i < len(sendkeys_str):
        if sendkeys_str[i] == "{":
            end = sendkeys_str.index("}", i)
            token = sendkeys_str[i:end + 1]
            as_key = _KEY_MAP.get(token)
            if as_key:
                lines.append(as_key)
            i = end + 1
        else:
            char = sendkeys_str[i]
            escaped = char.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'keystroke "{escaped}"')
            i += 1
    return "\n        ".join(lines) if lines else ""


def _send_to_iterm2(text):
    """Send text or keypresses to iTerm2 via AppleScript."""
    keys, use_clipboard = normalize_selection(text)

    if not use_clipboard and keys:
        as_keys = _sendkeys_to_applescript(keys)
        script = f"""
tell application "iTerm2"
    activate
end tell
tell application "System Events"
    {as_keys}
end tell
"""
    else:
        # Set clipboard via pbcopy, then Cmd+V + Return in iTerm2
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        script = """
tell application "iTerm2"
    activate
end tell
delay 0.4
tell application "System Events"
    keystroke "v" using command down
    delay 0.1
    key code 36
end tell
"""
    subprocess.run(["osascript", "-e", script], capture_output=True)


def _send_to_terminal_app(text):
    """Send text or keypresses to Terminal.app via AppleScript."""
    keys, use_clipboard = normalize_selection(text)

    # Find the Terminal window containing "claude" in its title
    activate_script = """
tell application "Terminal"
    activate
    set targetWindow to missing value
    repeat with w in windows
        if (name of w) contains "claude" then
            set targetWindow to w
            set index of w to 1
            exit repeat
        end if
    end repeat
end tell
"""

    if not use_clipboard and keys:
        as_keys = _sendkeys_to_applescript(keys)
        script = activate_script + f"""
delay 0.4
tell application "System Events"
    {as_keys}
end tell
"""
    else:
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        script = activate_script + """
delay 0.4
tell application "System Events"
    keystroke "v" using command down
    delay 0.1
    key code 36
end tell
"""
    subprocess.run(["osascript", "-e", script], capture_output=True)


def send_to_claude_code(text):
    """Route to iTerm2 or Terminal.app based on what's running."""
    if _is_iterm2_running():
        _send_to_iterm2(text)
    else:
        _send_to_terminal_app(text)
