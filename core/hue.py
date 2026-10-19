#!/usr/bin/env python3
"""
Jarvis — Philips Hue Integration
Controls lights via the local Hue Bridge REST API (v1/CLIP).

One-time setup:
    python scripts/hue.py --setup

List lights and rooms:
    python scripts/hue.py --list

Test a command:
    python scripts/hue.py --cmd "turn off the computer room"

Then add to .env:
    HUE_BRIDGE_IP=192.168.x.x
    HUE_API_KEY=your_key_here
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[1] / ".env")

BRIDGE_IP = os.getenv("HUE_BRIDGE_IP")
API_KEY   = os.getenv("HUE_API_KEY")

# ─── DEFAULT LEVELS ───────────────────────────────────────────────────────────
BRI_DIM      = 77    # 30% of 254
BRI_NORMAL   = 178   # 70%
BRI_BRIGHT   = 229   # 90%
CT_WARM      = 370   # 2700K — warm white
CT_NEUTRAL   = 250   # 4000K — neutral white
CT_COOL      = 156   # 6500K — daylight

# Voice phrase → scene name substrings to look up on the bridge
_SCENE_PRESETS = {
    "movie":      ["Movie", "Cinema", "Dimmed"],
    "reading":    ["Read", "Concentrate", "Bright"],
    "relax":      ["Relax"],
    "night":      ["Nightlight", "Night"],
    "energize":   ["Energize"],
    "focus":      ["Concentrate", "Focus"],
    "party":      ["Party"],
    "romance":    ["Romance"],
    "arctic":     ["Arctic Aurora"],
    "spring":     ["Spring Blossom"],
    "savanna":    ["Savanna Sunset"],
}

# Keywords that signal a light-control command
HUE_KEYWORDS = {
    "light", "lights", "lamp", "lamps",
    "dim", "dimmer", "dimming",
    "brighten", "brighter", "brightness",
    "movie mode", "reading mode", "relax mode", "night mode",
    "focus mode", "party mode", "romance mode", "energize",
    "warmer", "cooler", "daylight", "warm white", "cool white",
    "turn on the", "turn off the", "switch on", "switch off",
    "all off", "all on", "lights off", "lights on",
}


# ─── BRIDGE ───────────────────────────────────────────────────────────────────

class HueBridge:
    def __init__(self, ip=None, key=None):
        self.ip  = ip  or BRIDGE_IP
        self.key = key or API_KEY
        self._lights = None
        self._groups = None
        self._scenes = None

        if not self.ip:
            raise RuntimeError("HUE_BRIDGE_IP not set. Run: python scripts/hue.py --setup")
        if not self.key:
            raise RuntimeError("HUE_API_KEY not set. Run: python scripts/hue.py --setup")

    @property
    def base(self):
        return f"http://{self.ip}/api/{self.key}"

    def _get(self, path):
        r = requests.get(f"{self.base}/{path}", timeout=5)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data and "error" in data[0]:
            raise RuntimeError(data[0]["error"]["description"])
        return data

    def _put(self, path, payload):
        r = requests.put(f"{self.base}/{path}", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()

    # ─── CACHED RESOURCES ─────────────────────────────────────────────────────

    def lights(self, refresh=False):
        if self._lights is None or refresh:
            self._lights = self._get("lights")
        return self._lights

    def groups(self, refresh=False):
        if self._groups is None or refresh:
            self._groups = self._get("groups")
        return self._groups

    def scenes(self, refresh=False):
        if self._scenes is None or refresh:
            self._scenes = self._get("scenes")
        return self._scenes

    # ─── RAW CONTROL ──────────────────────────────────────────────────────────

    def set_light(self, light_id, **state):
        return self._put(f"lights/{light_id}/state", state)

    def set_group(self, group_id, **state):
        return self._put(f"groups/{group_id}/action", state)

    # Group 0 is a special "all lights" group in the Hue API
    def all_on(self):    return self.set_group(0, on=True,  bri=BRI_NORMAL)
    def all_off(self):   return self.set_group(0, on=False)

    # ─── LOOKUP ───────────────────────────────────────────────────────────────

    def find_group(self, name):
        """Return (id, group_dict) for the best partial name match, or (None, None)."""
        name_lower = name.lower()
        best_id, best_group, best_score = None, None, 0
        for gid, g in self.groups().items():
            gname = g["name"].lower()
            if name_lower == gname:
                return gid, g  # Exact match — return immediately
            if name_lower in gname or gname in name_lower:
                score = len(set(name_lower.split()) & set(gname.split()))
                if score > best_score:
                    best_id, best_group, best_score = gid, g, score
        return best_id, best_group

    def find_scene(self, name, group_id=None):
        """Return (id, scene_dict) for the best partial name match, optionally filtered by group."""
        name_lower = name.lower()
        for sid, s in self.scenes().items():
            if group_id and s.get("group") != str(group_id):
                continue
            if name_lower in s["name"].lower():
                return sid, s
        return None, None

    def room_names(self):
        """Return list of all room/zone names (for display)."""
        return sorted(
            g["name"] for g in self.groups().values()
            if g.get("type") in ("Room", "Zone", "LightGroup")
        )

    # ─── HIGH-LEVEL ACTIONS ───────────────────────────────────────────────────

    def set_brightness_pct(self, group_id, pct):
        """Set group brightness. pct: 0-100."""
        bri = max(1, min(254, round(pct * 254 / 100)))
        return self.set_group(group_id, on=True, bri=bri)

    def set_color_temp(self, group_id, ct):
        """Set group color temperature. ct: 153 (cool) to 500 (warm)."""
        return self.set_group(group_id, on=True, ct=ct)

    def activate_scene_by_name(self, scene_name, group_id=None):
        """Activate a scene by partial name. Returns the scene name or None."""
        sid, scene = self.find_scene(scene_name, group_id=group_id)
        if not sid:
            return None
        gid = group_id or scene.get("group")
        if gid:
            self.set_group(gid, scene=sid)
        return scene["name"]


# ─── NATURAL LANGUAGE PARSER ──────────────────────────────────────────────────

def is_hue_command(text):
    """Quick check: does this text sound like a light control command?"""
    lowered = text.lower()
    for kw in HUE_KEYWORDS:
        if kw in lowered:
            return True
    return False


def _extract_percent(text):
    """Extract a percentage from text like 'to 50 percent' or '50%'. Returns int or None."""
    import re
    m = re.search(r'\b(\d{1,3})\s*(?:percent|%)', text.lower())
    if m:
        return int(m.group(1))
    return None


def _extract_room(text, bridge):
    """Find a room name mentioned in the text. Returns (room_name, group_id) or (None, None)."""
    lowered = text.lower()
    # Try each known room — longest match wins to avoid "room" matching "computer room"
    best_name, best_gid, best_len = None, None, 0
    for gid, g in bridge.groups().items():
        room = g["name"].lower()
        if room in lowered and len(room) > best_len:
            best_name, best_gid, best_len = g["name"], gid, len(room)
    return best_name, best_gid


def parse_and_execute(text, bridge):
    """
    Parse a natural language light command and execute it.
    Returns a human-readable result string (spoken back by Jarvis).
    Returns None if the command couldn't be understood.
    """
    lowered = text.lower().strip()

    # ── ALL OFF ───────────────────────────────────────────────────────────────
    if any(p in lowered for p in ("all off", "everything off", "lights off", "kill the lights", "kill all")):
        bridge.all_off()
        return "All lights off, sir."

    # ── ALL ON ────────────────────────────────────────────────────────────────
    if any(p in lowered for p in ("all on", "lights on", "everything on", "all lights on")):
        bridge.all_on()
        return "All lights on, sir."

    # ── SCENE PRESETS ─────────────────────────────────────────────────────────
    for preset_key, scene_names in _SCENE_PRESETS.items():
        if preset_key in lowered or f"{preset_key} mode" in lowered:
            room_name, group_id = _extract_room(lowered, bridge)
            for sname in scene_names:
                activated = bridge.activate_scene_by_name(sname, group_id=group_id)
                if activated:
                    location = f" in the {room_name}" if room_name else ""
                    return f"{activated} scene activated{location}, sir."
            return f"I couldn't find a {preset_key} scene, sir."

    # ── ACTIVATE SCENE BY NAME ────────────────────────────────────────────────
    if "scene" in lowered or "activate" in lowered:
        import re
        m = re.search(r'(?:activate|scene|set)\s+(?:the\s+)?([a-z\s]+?)(?:\s+scene|\s+mode|$)', lowered)
        if m:
            scene_query = m.group(1).strip()
            room_name, group_id = _extract_room(lowered, bridge)
            activated = bridge.activate_scene_by_name(scene_query, group_id=group_id)
            if activated:
                location = f" in the {room_name}" if room_name else ""
                return f"{activated} scene activated{location}, sir."

    # ── COLOR TEMPERATURE ──────────────────────────────────────────────────────
    ct_map = {
        "warmer":     CT_WARM,
        "warm":       CT_WARM,
        "warm white": CT_WARM,
        "cooler":     CT_COOL,
        "cool":       CT_COOL,
        "cool white": CT_COOL,
        "daylight":   CT_COOL,
        "neutral":    CT_NEUTRAL,
        "white":      CT_NEUTRAL,
    }
    for phrase, ct in ct_map.items():
        if phrase in lowered:
            room_name, group_id = _extract_room(lowered, bridge)
            gid = group_id or 0
            bridge.set_color_temp(gid, ct)
            label = f"the {room_name}" if room_name else "all lights"
            temp_label = "warm" if ct >= 300 else ("daylight" if ct <= 160 else "neutral")
            return f"Set {label} to {temp_label} white, sir."

    # ── FIND ROOM (used by on/off/dim/brighten/percent) ───────────────────────
    room_name, group_id = _extract_room(lowered, bridge)

    # ── TURN ON ───────────────────────────────────────────────────────────────
    if any(p in lowered for p in ("turn on", "switch on", "lights on", "put on")):
        if group_id:
            bridge.set_group(group_id, on=True, bri=BRI_NORMAL)
            return f"{room_name} lights on, sir."
        bridge.all_on()
        return "All lights on, sir."

    # ── TURN OFF ──────────────────────────────────────────────────────────────
    if any(p in lowered for p in ("turn off", "switch off", "lights off", "shut off")):
        if group_id:
            bridge.set_group(group_id, on=False)
            return f"{room_name} lights off, sir."
        bridge.all_off()
        return "All lights off, sir."

    # ── SET TO PERCENT ────────────────────────────────────────────────────────
    pct = _extract_percent(lowered)
    if pct is not None:
        gid = group_id or 0
        bridge.set_brightness_pct(gid, pct)
        label = f"the {room_name}" if room_name else "all lights"
        return f"Set {label} to {pct}%, sir."

    # ── DIM ───────────────────────────────────────────────────────────────────
    if any(p in lowered for p in ("dim", "dimmer", "lower", "soften", "reduce")):
        gid = group_id or 0
        bridge.set_group(gid, on=True, bri=BRI_DIM)
        label = f"the {room_name}" if room_name else "all lights"
        return f"Dimmed {label} to 30%, sir."

    # ── BRIGHTEN ──────────────────────────────────────────────────────────────
    if any(p in lowered for p in ("bright", "brighter", "brighten", "raise", "increase", "full")):
        gid = group_id or 0
        bri = 254 if "full" in lowered else BRI_BRIGHT
        bridge.set_group(gid, on=True, bri=bri)
        label = f"the {room_name}" if room_name else "all lights"
        pct_label = "100" if bri == 254 else "90"
        return f"Brightened {label} to {pct_label}%, sir."

    return None


# ─── SETUP ────────────────────────────────────────────────────────────────────

def discover_bridge():
    """Try to find the Hue bridge IP via Philips' cloud discovery service."""
    print("[hue] Searching for Hue bridge...")
    try:
        r = requests.get("https://discovery.meethue.com/", timeout=8)
        bridges = r.json()
        if bridges:
            ip = bridges[0]["internalipaddress"]
            print(f"[hue] Found bridge at {ip}")
            return ip
    except Exception as e:
        print(f"[hue] Discovery failed: {e}")
    return None


def setup():
    """
    Interactive one-time setup. Discovers the bridge, pairs with it,
    and prints the values to add to .env.
    """
    print("\n=== Philips Hue Setup ===\n")

    ip = BRIDGE_IP
    if not ip:
        ip = discover_bridge()
    if not ip:
        ip = input("Enter your Hue bridge IP address: ").strip()

    print(f"\nBridge IP: {ip}")
    print("\nPress the physical button on your Hue Bridge NOW, then press Enter...")
    input()

    try:
        r = requests.post(
            f"http://{ip}/api",
            json={"devicetype": "jarvis#windows"},
            timeout=10,
        )
        data = r.json()
        if isinstance(data, list):
            data = data[0]
        if "error" in data:
            print(f"\nError: {data['error']['description']}")
            print("Make sure you pressed the button on the bridge within the last 30 seconds.")
            return
        key = data["success"]["username"]
        print(f"\nPairing successful!")
        print(f"\nAdd these lines to your .env file:")
        print(f"\n  HUE_BRIDGE_IP={ip}")
        print(f"  HUE_API_KEY={key}\n")
    except Exception as e:
        print(f"\nSetup failed: {e}")


def list_devices():
    """Print all lights, rooms, and scenes."""
    try:
        bridge = HueBridge()
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    print("\n=== Lights ===")
    for lid, light in bridge.lights().items():
        state = light["state"]
        status = "ON" if state["on"] else "off"
        bri = f" bri={state.get('bri', '?')}" if state.get("on") else ""
        print(f"  [{lid}] {light['name']} — {status}{bri}")

    print("\n=== Rooms / Zones ===")
    for gid, g in bridge.groups().items():
        if g.get("type") in ("Room", "Zone", "LightGroup"):
            state = g.get("action", {})
            status = "ON" if state.get("on") else "off"
            print(f"  [{gid}] {g['name']} ({g.get('type', '?')}) — {status}")

    print("\n=== Scenes ===")
    for sid, s in sorted(bridge.scenes().items(), key=lambda x: x[1]["name"]):
        group = s.get("group", "-")
        print(f"  [{sid}] {s['name']} (group {group})")

    print()


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jarvis Hue controller")
    parser.add_argument("--setup", action="store_true", help="Pair with your Hue bridge")
    parser.add_argument("--list",  action="store_true", help="List lights, rooms, and scenes")
    parser.add_argument("--cmd",   type=str,            help="Test a voice command")
    args = parser.parse_args()

    if args.setup:
        setup()
    elif args.list:
        list_devices()
    elif args.cmd:
        try:
            bridge = HueBridge()
            result = parse_and_execute(args.cmd, bridge)
            print(result or "Command not understood.")
        except RuntimeError as e:
            print(f"Error: {e}")
    else:
        parser.print_help()
