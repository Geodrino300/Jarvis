# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

---

## What This Is

**Jarvis** is a voice assistant for a local coding agent. On this Windows checkout it launches the installed Codex desktop app; the macOS adapter retains its original Claude Code integration. It listens for a double-snap near your microphone, launches your dev environment, and then listens for the wake word "Jarvis" to relay spoken commands hands-free.

Works on **Windows** and **macOS**.

---

## Agent Name

This agent's name is **Jarvis**. Respond accordingly.

---

## Wake Up Trigger

When the user says **"wake up"** or **"wake up Jarvis"** in the chat, treat it the same as running `/jarvis` — load context and start the snap daemon.

---

## Project Structure

```
jarvis/
├── jarvis.py                    # Entry point -- platform detection + wiring
├── core/                        # Shared logic, platform-agnostic
│   ├── snap.py                  # Double-snap detection (sounddevice)
│   ├── greeting.py              # Location, weather, Claude greeting
│   ├── speech.py                # ElevenLabs TTS + Edge TTS fallback
│   ├── transcription.py         # Google STT + Whisper fallback
│   ├── voice_loop.py            # Wake word loop, command dispatch
│   ├── hue.py                   # Philips Hue local API
│   └── commands.py              # Shared voice command maps
├── platforms/
│   ├── windows/
│   │   ├── launcher.py          # App launching (Windows)
│   │   ├── window_manager.py    # win32gui window positioning
│   │   ├── terminal.py          # Send to Codex desktop via PowerShell
│   │   ├── startup.ps1          # Launch Jarvis + Claude Code terminal
│   │   ├── launch-session.ps1   # Open VS Code + Claude Code on snap
│   │   ├── create-shortcut.ps1  # Per-project desktop shortcut
│   │   └── setup-autostart.ps1  # Task Scheduler login trigger
│   └── mac/
│       ├── launcher.py          # App launching (macOS)
│       ├── window_manager.py    # AppleScript window positioning
│       ├── terminal.py          # Send to Claude Code via osascript
│       ├── startup.sh           # Launch Jarvis + Claude Code terminal
│       ├── create-shortcut.sh   # Create Desktop .app shortcut per project
│       └── setup-autostart.sh   # Register launchd login agent
├── context/
│   └── profile.md               # Personal context template (fill in via /context)
├── scripts/
│   └── test-mic.py              # Mic calibration utility
├── reference/
│   ├── setup-windows.md         # Full Windows setup guide
│   └── setup-mac.md             # Full macOS setup guide
├── venv/                        # Python virtual environment (auto-generated, not committed)
├── .env                         # Local API keys (not committed)
└── .claude/
    └── commands/
        ├── jarvis.md            # /jarvis -- start snap daemon
        ├── stop.md              # /stop -- kill daemon
        ├── setup.md             # /setup -- onboarding flow
        └── context.md           # /context -- guided profile setup
```

---

## Platform Architecture

`jarvis.py` detects the platform and wires core modules to platform-specific implementations via `SimpleNamespace`:

```python
platform = SimpleNamespace(
    send_to_claude_code=terminal.send_to_claude_code,
    arrange_windows=window_manager.arrange_windows,
    beep=terminal.beep,
    launcher=launcher,
)
```

All `core/` modules are platform-agnostic and receive the platform adapter via injection. Never import from `platforms/` inside `core/`.

---

## How It Works

1. **Snap trigger** (`core/snap.py`) -- listens for an RMS spike pattern matching a double-snap
2. **Session launch** (`jarvis.py` + `platform.launcher`) -- opens apps, generates greeting, arranges windows
3. **Voice loop** (`core/voice_loop.py`) -- Vosk detects wake word "Jarvis"; on detection: beep + record + transcribe + dispatch
4. **Command dispatch** (`core/voice_loop.py:handle_command`):
   - Layout trigger -- `platform.arrange_windows()`
   - Hue command -- `core/hue.py` local bridge call + speak result
   - Anything else -- `platform.send_to_claude_code(text)` + parallel voice response via Claude API

---

## Commands

| Command | Effect |
|---------|--------|
| `/jarvis` | Start the snap daemon |
| `/stop` | Kill the Jarvis process |
| `/context` | Guided setup for `context/profile.md` |
| `/jarvis-shortcut` | Create a per-project desktop shortcut (optional) |
| `/jarvis-autostart` | Register Jarvis to launch at login (optional) |

---

## API Keys (.env)

```
ELEVENLABS_API_KEY=    # elevenlabs.io -> Profile -> API Key
ANTHROPIC_API_KEY=     # console.anthropic.com -> API Keys
WORKSPACE_PATH=        # e.g. C:\projects\myapp -- folder VS Code + Claude Code open in
HUE_BRIDGE_IP=         # your Hue bridge local IP (set via: python core/hue.py --setup)
HUE_API_KEY=           # your Hue username/key (set via: python core/hue.py --setup)
```

---

## Running Locally

**Windows (hidden background listener):**
```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\startup.ps1" -Mode daemon -Background
```

**macOS:**
```bash
./platforms/mac/startup.sh
```

---

## Personal Context Files

`context/profile.md` is a blank template committed to the repo. Run `/context` to fill it in -- git is configured to ignore local changes to this file so personal details are never committed.

Run `/context` inside Claude Code to fill it in interactively.
