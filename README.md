# Jarvis — AI Voice Assistant for Claude Code

Jarvis is a voice assistant that wraps around **Claude Code**. Double-snap near your microphone and your entire dev environment spins up: apps open, windows arrange themselves, and Jarvis greets you with the time, weather, and your daily briefing. Then just say **"Jarvis"** to send voice commands directly to your Claude Code session — hands-free AI pair programming.

> **This Windows checkout:** voice commands launch and target the installed local **Codex desktop app**. Automatic browser/Chrome launch is disabled.

Works on **Windows** and **macOS**.

---

## What It Does

### Snap to Wake
Double-snap near your mic — no button, no hotkey — and Jarvis:
- Plays your startup song in Spotify
- Opens VS Code, Chrome, Claude Desktop — whatever you've configured
- Auto-arranges every window to your saved layout
- Speaks an Iron Man-style greeting with the current time, weather, and a briefing based on your goals

### Voice to Claude Code
Say **"Jarvis"** followed by any command:
1. A beep confirms it's listening
2. You speak your command
3. Your words are transcribed and sent **directly into your Claude Code terminal** — as if you typed it
4. Simultaneously, Jarvis calls the Claude API and speaks a brief voice response

This is the core feature — a hands-free voice interface to Claude Code.

### Smart Greeting
Every session, Jarvis fetches your location and live weather, reads your personal context files, and asks Claude to generate a short, Jarvis-style briefing. Morning sessions get a task digest. Evening sessions get a casual check-in. All spoken aloud in a deep British voice via ElevenLabs.

### App Launcher
On double-snap, Jarvis launches any combination of:
- **VS Code** — opens in your workspace
- **Spotify** — plays a specific track from the beginning, every time
- **Chrome** — opens your browser
- **Claude Desktop** — opens the Claude GUI app

Each is an independent toggle. Turn on only what you use.

### Window Layout Manager
Jarvis repositions every window to a saved pixel-perfect layout after launch. Works on any monitor — 1080p, 1440p, ultrawide, super ultrawide. Say **"arrange windows"** at any time to re-apply without restarting.

### Philips Hue Light Control
Say **"Jarvis, dim the office"** and the lights respond instantly — handled directly on your local network, no cloud round-trip. Jarvis speaks back a confirmation. Supports rooms, brightness, color temperature, and named scenes.

### Offline Wake Word Detection
The "Jarvis" wake word is detected locally using **Vosk** — no internet, no API call, no latency. Speech-to-text uses Google STT by default, with an optional offline Whisper fallback.

---

## Requirements

| | Windows | macOS |
|---|---|---|
| OS | Windows 10 or 11 | macOS 12 Monterey or later |
| Python | 3.10+ | 3.10+ |
| Claude Code | [claude.ai/download](https://claude.ai/download) | [claude.ai/download](https://claude.ai/download) |
| Microphone | Required | Required |
| ElevenLabs | Free tier works | Free tier works |
| Anthropic | Free tier works | Free tier works |
| Extra | — | Accessibility permission for terminal app |

---

## Setup

Pick your platform and follow the full setup guide:

### [Windows Setup →](reference/setup-windows.md)
### [macOS Setup →](reference/setup-mac.md)

### Windows background mode

Run Jarvis hidden and keep it enabled for the current user at login. A small tray icon shows Listening or Paused and provides Pause/Resume, Quit, and Quit & Disable Startup; no Jarvis terminal stays open.

```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\setup-autostart.ps1"
powershell -ExecutionPolicy Bypass -File "platforms\windows\startup.ps1" -Mode daemon -Background
```

Stop it without changing login startup:

```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\stop.ps1"
```

Stop it and disable login startup:

```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\stop.ps1" -DisableAutostart
```

### Google Calendar (read-only)

Jarvis can read the primary calendar for questions such as “what is on my calendar tomorrow?” It requests only Google's `calendar.readonly` scope and never starts OAuth during normal listening.

1. In Google Cloud, enable the Google Calendar API and create an **OAuth client ID → Desktop app**.
2. Download the client JSON to `%LOCALAPPDATA%\Jarvis\google-calendar-client.json`.
3. Run `python scripts\setup-google-calendar.py` once and approve read-only access in the browser.

The resulting refresh token stays under `%LOCALAPPDATA%\Jarvis`; OAuth files are ignored by Git.

---

## Usage

| Action | What happens |
|--------|-------------|
| Double-snap near mic | Full session launches — apps open, windows arrange, Jarvis greets you |
| Say **"Jarvis"** + command | Command is sent to Claude Code terminal; Jarvis speaks a response |
| Say **"arrange windows"** | Re-applies your window layout without restarting |
| Say **"Jarvis, dim the office"** | Controls Philips Hue lights by room — instant, local |
| Say **"Jarvis, movie mode"** | Activates a Hue scene across a room |
| `/jarvis` in Claude Code | Starts the snap daemon from the terminal |
| `/stop` in Claude Code | Kills the Jarvis process |
| `/context` in Claude Code | Guided setup for your personal context files |
| `/jarvis-shortcut` in Claude Code | Creates a per-project desktop shortcut |
| `/jarvis-autostart` in Claude Code | Registers Jarvis to launch at login |

---

## Customization

### Change Jarvis's voice

1. Go to [elevenlabs.io](https://elevenlabs.io) → Voice Library
2. Find a voice and copy its Voice ID
3. In `.env`:
```
ELEVENLABS_VOICE_ID=paste-voice-id-here
```
Free fallback voice (no credits): `en-GB-RyanNeural` via Edge TTS — set in `.env` as `EDGE_TTS_VOICE`.

### Configure which apps launch

In `platforms/windows/launcher.py` or `platforms/mac/launcher.py`:
```python
LAUNCH_VSCODE          = True
LAUNCH_SPOTIFY         = True
LAUNCH_CHROME          = True
LAUNCH_CLAUDE_DESKTOP  = True
ARRANGE_WINDOWS        = True
```

For Spotify, set your startup track:
1. Right-click any song → **Share → Copy Song Link**
2. Extract the track ID: `open.spotify.com/track/TRACK_ID`
3. Set `SPOTIFY_TRACK_URI = "spotify:track:TRACK_ID"` in your platform's `launcher.py`

### Configure your window layout

Edit `WINDOW_LAYOUT` in your platform's `window_manager.py`. Format: `(x, y, width, height)`.

```python
"chrome":  {"title": "Google Chrome", "pos": (0, 0, 960, 1080)},
"vscode":  {"title": "Visual Studio Code", "pos": (960, 0, 960, 1080)},
```

### Tune snap sensitivity

In `core/snap.py`:
```python
THRESHOLD = 0.07   # RMS spike threshold — increase if ambient noise triggers it
MIN_GAP   = 0.1    # Minimum seconds between two snaps (debounce)
MAX_GAP   = 1.2    # Maximum seconds between snap 1 and snap 2
```

Run `python scripts/test-mic.py` to watch live RMS levels.

### Control your Philips Hue lights

| Say... | What happens |
|--------|-------------|
| "turn off the office lights" | Office group off |
| "dim the living room" | Living room → 30% |
| "set the bedroom to 60 percent" | Bedroom → 60% |
| "movie mode" / "reading mode" / "relax mode" | Activates named scene |
| "warmer" / "daylight" | Shifts color temperature |
| "all lights off" | Everything off |

Setup: `python core/hue.py --setup`
List devices: `python core/hue.py --list`
Test a command: `python core/hue.py --cmd "dim the office"`

### Set your context

Run `/context` inside Claude Code to fill in your personal context files. Jarvis reads these every session to personalize your greeting and briefing.

---

## How the Voice Pipeline Works

```
You say "Jarvis"
    → Vosk detects wake word (offline, instant)
    → Beep plays
    → Google STT records + transcribes your command
    → Light command?  → core/hue.py controls bridge directly → Jarvis speaks confirmation
    → Layout command? → windows rearranged locally
    → Anything else?  → pasted into Claude Code terminal via clipboard
                        + Claude API generates brief spoken response in parallel
                        + ElevenLabs (or Edge TTS) speaks the response
```

Light and layout commands are handled entirely on your local network — sub-second, no Claude round-trip. Everything else goes to Claude Code as if you typed it.

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
│   │   ├── terminal.py          # Send to Claude Code via PowerShell
│   │   ├── startup.ps1          # Launch Jarvis + Claude Code terminal
│   │   ├── launch-session.ps1   # Open VS Code + Claude Code on snap
│   │   ├── create-shortcut.ps1  # Per-project desktop shortcut
│   │   └── setup-autostart.ps1  # Task Scheduler login trigger
│   └── mac/
│       ├── launcher.py          # App launching (macOS)
│       ├── window_manager.py    # AppleScript window positioning
│       ├── terminal.py          # Send to Claude Code via osascript
│       ├── startup.sh           # Launch Jarvis + Claude Code terminal
│       ├── create-shortcut.sh   # Per-project Desktop .app shortcut
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
        ├── context.md           # /context -- guided profile setup
        ├── jarvis-shortcut.md   # /jarvis-shortcut -- create desktop shortcut
        └── jarvis-autostart.md  # /jarvis-autostart -- register login autostart
```

---

## Technology

Jarvis uses:
- [Claude Code](https://claude.ai/download) — Anthropic's AI coding assistant
- [Anthropic API](https://console.anthropic.com) — Claude Haiku for voice responses and greetings
- [ElevenLabs](https://elevenlabs.io) — Text-to-speech (Edge TTS as free fallback)
- [Vosk](https://alphacephei.com/vosk/) — Offline wake word detection
- [Open-Meteo](https://open-meteo.com/) — Weather API (free, no key needed)
- [Philips Hue](https://developers.meethue.com/) — Local light control API
