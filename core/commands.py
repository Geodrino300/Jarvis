"""
Shared voice command maps.
Imported by core/voice_loop.py and both platform terminal modules.
Keeping this separate avoids circular imports.
"""

# Maps spoken phrases to terminal keystrokes.
# Tuple: (keys_to_send, use_clipboard)
_SELECTION_MAP = {
    "yes":          ("y{ENTER}", False),
    "yeah":         ("y{ENTER}", False),
    "yep":          ("y{ENTER}", False),
    "confirm":      ("y{ENTER}", False),
    "no":           ("n{ENTER}", False),
    "nope":         ("n{ENTER}", False),
    "cancel":       ("n{ENTER}", False),
    "one":          ("1{ENTER}", False),
    "option one":   ("1{ENTER}", False),
    "first":        ("1{ENTER}", False),
    "two":          ("2{ENTER}", False),
    "option two":   ("2{ENTER}", False),
    "second":       ("2{ENTER}", False),
    "three":        ("3{ENTER}", False),
    "option three": ("3{ENTER}", False),
    "third":        ("3{ENTER}", False),
    "four":         ("4{ENTER}", False),
    "option four":  ("4{ENTER}", False),
    "fourth":       ("4{ENTER}", False),
    "five":         ("5{ENTER}", False),
    "option five":  ("5{ENTER}", False),
    "fifth":        ("5{ENTER}", False),
    "up":           ("{UP}",     False),
    "down":         ("{DOWN}",   False),
    "select":       ("{ENTER}",  False),
    "enter":        ("{ENTER}",  False),
    "back":         ("{ESC}",    False),
    "escape":       ("{ESC}",    False),
}

# Voice phrases that trigger a window layout arrange (no Claude Code needed)
_LAYOUT_TRIGGERS = {
    "load my setup", "arrange windows", "setup my workspace",
    "arrange my windows", "load my workspace", "set up my workspace",
    "my setup", "load setup",
}


def normalize_selection(text):
    """
    If the spoken text matches a known selection phrase, return the
    corresponding SendKeys string and a flag indicating clipboard isn't needed.
    Otherwise return (None, True) to proceed with normal clipboard paste.
    """
    lowered = text.strip().lower()
    if lowered in _SELECTION_MAP:
        keys, use_clipboard = _SELECTION_MAP[lowered]
        print(f"[voice] Selection mapped: '{lowered}' -> {keys}", flush=True)
        return keys, use_clipboard
    return None, True
