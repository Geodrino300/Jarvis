"""
Jarvis -- Windows Window Manager
Positions app windows to a saved pixel-perfect layout using win32gui.

Edit WINDOW_LAYOUT below to match your monitor setup.
Format: (x, y, width, height)

Common single-monitor layouts (1920x1080):
  Left half:  (0, 0, 960, 1080)
  Right half: (960, 0, 960, 1080)

For dual monitors, the second monitor starts at x=<first monitor width>.
Run this to find your current window titles:
  python -c "import win32gui; win32gui.EnumWindows(lambda h,_: print(repr(win32gui.GetWindowText(h))) if win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h) else None, None)"
"""

import time
from core import speech

# --- Ultrawide layout (5120x1440, e.g. Samsung CRG 49") ---
# WINDOW_LAYOUT = {
#     "codex":    {"codex": True,                     "pos": (1280, 0,    1280, 1440)},
#     "vscode":   {"title": "Visual Studio Code",    "pos": (2560, 0,    1280, 1440)},
#     "spotify":  {"process": "Spotify",              "pos": (3840, 720,  1280, 720)},
# }

# --- Default layout: single 1920x1080 monitor ---
# Edit these positions to match your screen setup.
# Format: (x, y, width, height)
WINDOW_LAYOUT = {
    "codex":    {"codex": True,                     "pos": (960, 0, 960, 1080)},
    "vscode":   {"title": "Visual Studio Code",    "pos": (0,   0, 960, 1080)},
    "spotify":  {"process": "Spotify",              "pos": (960, 540, 960, 540)},
}


def _get_codex_hwnd():
    """
    Find the installed Codex desktop app's main HWND.
    """
    return _find_window_by_process("ChatGPT") or _find_window("Codex")


def _find_window(partial_title, exact=False):
    """Find a visible top-level window by title."""
    import win32gui
    matches = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if exact:
                if title == partial_title:
                    matches.append(hwnd)
            else:
                if partial_title.lower() in title.lower():
                    matches.append(hwnd)

    win32gui.EnumWindows(callback, None)
    return matches[0] if matches else None


def _find_window_by_process(process_name):
    """Find the main window of a running process by executable name."""
    import win32gui, win32process
    import psutil
    matches = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        if not win32gui.GetWindowText(hwnd):
            return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            if proc.name().lower().startswith(process_name.lower()):
                matches.append(hwnd)
        except Exception:
            pass

    win32gui.EnumWindows(callback, None)
    return matches[0] if matches else None


def _move_window(hwnd, x, y, w, h):
    """Restore (if minimised) then move/resize a window with DWM border compensation."""
    import win32gui, win32con, ctypes

    placement = win32gui.GetWindowPlacement(hwnd)
    if placement[1] == win32con.SW_SHOWMINIMIZED:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.2)

    win32gui.MoveWindow(hwnd, x, y, w, h, True)
    time.sleep(0.05)

    class RECT(ctypes.Structure):
        _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                    ('right', ctypes.c_long), ('bottom', ctypes.c_long)]

    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    frame = RECT()
    ctypes.windll.dwmapi.DwmGetWindowAttribute(
        hwnd, DWMWA_EXTENDED_FRAME_BOUNDS,
        ctypes.byref(frame), ctypes.sizeof(frame)
    )
    wr = win32gui.GetWindowRect(hwnd)
    left_pad   = frame.left  - wr[0]
    top_pad    = frame.top   - wr[1]
    right_pad  = wr[2]       - frame.right
    bottom_pad = wr[3]       - frame.bottom

    win32gui.MoveWindow(hwnd,
                        x - left_pad,
                        y - top_pad,
                        w + left_pad + right_pad,
                        h + top_pad  + bottom_pad,
                        True)

    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWCP_DONOTROUND = ctypes.c_int(1)
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(DWMWCP_DONOTROUND), ctypes.sizeof(DWMWCP_DONOTROUND)
        )
    except Exception:
        pass


def arrange_windows():
    """Position all windows to the saved layout."""
    try:
        import win32gui, win32con
    except ImportError:
        print("[layout] pywin32 not installed -- run: pip install pywin32", flush=True)
        speech.speak("pywin32 is not installed, sir. I can't move windows without it.")
        return

    moved, missing = [], []
    for name, cfg in WINDOW_LAYOUT.items():
        if cfg.get("codex"):
            hwnd = _get_codex_hwnd()
        elif "process" in cfg:
            hwnd = _find_window_by_process(cfg["process"])
        else:
            hwnd = _find_window(cfg["title"], exact=cfg.get("exact", False))

        if hwnd:
            x, y, w, h = cfg["pos"]
            try:
                _move_window(hwnd, x, y, w, h)
                moved.append(name)
                print(f"[layout] Moved {name} -> {cfg['pos']}", flush=True)
            except Exception as e:
                print(f"[layout] Failed to move {name}: {e}", flush=True)
                missing.append(name)
        else:
            label = cfg.get("process") or cfg.get("title")
            print(f"[layout] Window not found: {label}", flush=True)
            missing.append(name)

    if missing:
        print(f"[layout] Couldn't find: {', '.join(missing)}.", flush=True)
