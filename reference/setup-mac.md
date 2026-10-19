# Jarvis Setup Guide — macOS

Get Jarvis running from scratch on macOS 12 Monterey or later. Follow these steps in order.

**Total time:** ~20–30 minutes

---

## Step 1: Check Your System

Open **Terminal** and run each check.

### Python
```bash
python3 --version
```
Need **3.10 or higher**. If missing or outdated:
→ Install via [Homebrew](https://brew.sh): `brew install python`
→ Or download from [python.org/downloads](https://python.org/downloads)

### Claude Code
```bash
claude --version
```
If missing: install from [claude.ai/download](https://claude.ai/download)

### Homebrew (recommended)
If you don't have Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

## Step 2: Clone the Repo

```bash
git clone https://github.com/Geodrino300/Jarvis.git
cd Jarvis
```

---

## Step 3: Install Python Packages

Python 3.12+ (including Homebrew's default Python) enforces isolated environments. Create a virtual environment inside the project folder first:

```bash
python3 -m venv venv
source venv/bin/activate
```

> **Note:** You'll need to run `source venv/bin/activate` any time you open a new terminal and want to run Jarvis manually. The startup script (`startup.sh`) activates it automatically.

Then install packages:

```bash
pip install sounddevice numpy requests anthropic elevenlabs edge-tts python-dotenv speechrecognition vosk pillow
```

> **Note:** `pywin32` and `psutil` are Windows-only — do not install them on Mac.

`sounddevice` requires PortAudio. If the install fails:
```bash
brew install portaudio
pip install sounddevice
```

**Optional — offline speech-to-text fallback (~2GB):**
```bash
pip install openai-whisper
```
Skip this if you have a reliable internet connection. Jarvis uses Google STT by default.

### Install the Vosk wake-word model

Vosk detects the "Jarvis" wake word offline.

1. Download `vosk-model-small-en-us-0.15` (~50MB) from [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)
2. Unzip it
3. Place the folder at:
   ```
   ~/.local/share/vosk/vosk-model-small-en-us-0.15
   ```
   Or anywhere — Vosk on Mac will auto-download on first run if not found.

Verify:
```bash
venv/bin/python3 -c "import vosk; print('Vosk OK')"
```

---

## Step 4: Grant Accessibility Permission

Jarvis sends keystrokes to your Claude Code terminal via AppleScript. macOS requires explicit permission for this.

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click **+** and add your terminal app:
   - **Terminal.app** → `/Applications/Utilities/Terminal.app`
   - **iTerm2** → `/Applications/iTerm.app` (if you use iTerm2)
3. Also add **Python** if prompted during first run

You only need to do this once.

> **Why is this needed?** macOS sandboxes apps from controlling each other. Jarvis uses AppleScript to find your Claude Code terminal window and paste your voice command into it — that requires Accessibility access.

---

## Step 5: Add Your API Keys

```bash
open -e .env      # opens in TextEdit, or use: nano .env
```

Fill in:
```
ELEVENLABS_API_KEY=your_key_here    # optional — leave blank to use Edge TTS for free
ANTHROPIC_API_KEY=your_key_here     # console.anthropic.com → API Keys
WORKSPACE_PATH=/Users/you/projects/myapp   # folder VS Code + Claude Code open in
```

**ElevenLabs** is optional. If you leave `ELEVENLABS_API_KEY` blank, Jarvis uses Microsoft Edge TTS — a free, neural-quality British voice with no API key required. ElevenLabs gives a higher quality voice if you have an account (free tier: 10,000 characters/month).

Verify keys are loading:
```bash
python3 -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print('EL:', 'OK' if os.getenv('ELEVENLABS_API_KEY') else 'MISSING'); print('Anthropic:', 'OK' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING')"
```

---

## Step 6: Configure Which Apps Launch

Open `platforms/mac/launcher.py` and toggle each app:

```python
LAUNCH_VSCODE          = True   # Opens VS Code in your workspace
LAUNCH_SPOTIFY         = True   # Opens Spotify and plays SPOTIFY_TRACK_URI
LAUNCH_CHROME          = True   # Opens Google Chrome
LAUNCH_CLAUDE_DESKTOP  = True   # Opens Claude Desktop
ARRANGE_WINDOWS        = True   # Auto-arranges windows after launch
```

Set any to `False` to skip it. The voice loop always runs — these are optional extras.

### Spotify startup track
1. Right-click any song in Spotify → **Share → Copy Song Link**
2. Extract the track ID from: `open.spotify.com/track/TRACK_ID`
3. Update in `launcher.py`:
   ```python
   SPOTIFY_TRACK_URI = "spotify:track:TRACK_ID"
   ```

### VS Code CLI
Make sure `code` is on your PATH:
```bash
code --version
```
If missing: open VS Code → **Command Palette** (`Cmd+Shift+P`) → **Shell Command: Install 'code' command in PATH**

---

## Step 7: Configure Your Window Layout (Optional)

If `ARRANGE_WINDOWS = True`, Jarvis repositions all windows after launch using AppleScript.

Open `platforms/mac/window_manager.py` and edit `WINDOW_LAYOUT`. Format: `(x, y, width, height)`.

```python
WINDOW_LAYOUT = {
    "chrome":  {"app": "Google Chrome",      "pos": (0,    0,    1280, 800)},
    "vscode":  {"app": "Visual Studio Code", "pos": (1280, 0,    1280, 800)},
    "spotify": {"app": "Spotify",            "pos": (0,    800,  640,  280)},
}
```

### Find your screen resolution
```bash
python3 -c "import subprocess; r = subprocess.run(['system_profiler', 'SPDisplaysDataType'], capture_output=True, text=True); print(r.stdout)" | grep Resolution
```

### Common layouts

| Monitor | Left half | Right half |
|---------|-----------|------------|
| 1440×900 (MacBook) | `(0, 0, 720, 900)` | `(720, 0, 720, 900)` |
| 1920×1080 | `(0, 0, 960, 1080)` | `(960, 0, 960, 1080)` |
| 2560×1440 | `(0, 0, 1280, 1440)` | `(1280, 0, 1280, 1440)` |
| 5120×1440 ultrawide | Four columns of `1280` each |

> **Note:** macOS window positioning via AppleScript sets the *content area* bounds. Results may vary slightly from pixel-perfect on Retina displays.

Say **"arrange windows"** at any time to re-apply the layout.

---

## Step 8: Tune Snap Sensitivity

Run the mic calibration tool and snap a few times:
```bash
source venv/bin/activate
python3 scripts/test-mic.py
```

Then edit `core/snap.py`:
```python
THRESHOLD = 0.07   # RMS spike threshold
MIN_GAP   = 0.1    # Minimum seconds between two snaps (debounce)
MAX_GAP   = 1.2    # Maximum seconds between snap 1 and snap 2
```

| Problem | Fix |
|---------|-----|
| Triggered by keyboard or talking | Increase `THRESHOLD` (try `0.10`, `0.15`) |
| Snaps not detected | Decrease `THRESHOLD` (try `0.05`, `0.03`) |
| Need more time between snaps | Increase `MAX_GAP` |
| Double-triggering on one snap | Increase `MIN_GAP` |

---

## Step 9: Set Up Philips Hue (Optional)

If you have Philips Hue lights:

```bash
source venv/bin/activate
python3 core/hue.py --setup
```

Press the button on your bridge when prompted. The script prints your `HUE_BRIDGE_IP` and `HUE_API_KEY` — paste them into `.env`.

Verify:
```bash
python3 core/hue.py --list
python3 core/hue.py --cmd "dim the office"
```

---

## Step 10: Set Your Context

Run `/context` inside Claude Code to fill in your personal context files (your name, goals, how you like to be briefed). Jarvis reads these every session.

---

## Step 11: First Run

Type `/jarvis` inside Claude Code to start.

> **Note:** If you just cloned the repo, you need to fully close and reopen Claude Code first — it won't recognise `/jarvis` until it's restarted.

Double-snap near your mic. Jarvis greets you and your apps open. Then say **"Jarvis"** followed by any command.

**Alternatively**, you can launch directly from Terminal:
```bash
chmod +x platforms/mac/startup.sh
./platforms/mac/startup.sh
```

---

## Launch Options

### Option A — Manual (default)
```bash
./platforms/mac/startup.sh
```

### Option B — Autostart mode (launch immediately, no snap)
```bash
./platforms/mac/startup.sh --mode autostart
```

### Option C — Desktop shortcut (one click per project)
```bash
bash ~/projects/jarvis/platforms/mac/create-shortcut.sh --project ~/projects/myapp
```
Double-click the `.app` on your Desktop — Claude Code opens in that project and Jarvis arms immediately. To add it to your Dock: drag it from the Desktop into the Dock.

Or run `/jarvis-shortcut` inside Claude Code.

### Option D — Auto-launch at login
```bash
bash platforms/mac/setup-autostart.sh
```
Run once. Jarvis + Claude Code start automatically every time you log in. Workspace is read from `WORKSPACE_PATH` in your `.env` file.

To remove:
```bash
bash platforms/mac/setup-autostart.sh --remove
```

Or run `/jarvis-autostart` inside Claude Code.

---

## Terminal App Support

Jarvis auto-detects which terminal you're using:

| Terminal | Supported | Notes |
|----------|-----------|-------|
| Terminal.app | Yes | Built into macOS, always available |
| iTerm2 | Yes | Detected automatically if running, takes priority |
| Other terminals | No | Commands will fall back to Terminal.app |

Jarvis finds your Claude Code window by looking for "claude" in the terminal window title. If it can't find it, it targets the front window.

---

## Troubleshooting

| Problem | Check |
|---------|-------|
| Nothing happens on snap | Run `python3 scripts/test-mic.py` — do you see RMS spikes when you snap? |
| "No module named X" | Activate venv first: `source venv/bin/activate`, then `pip install X` |
| Voice not working | Check `ELEVENLABS_API_KEY` in `.env` — Edge TTS kicks in as fallback |
| Commands not reaching Claude Code | Check Accessibility permission is granted (Step 4) |
| "Operation not permitted" on AppleScript | Re-check Accessibility in System Settings |
| Apps not opening | Check the toggle is `True` and the app is installed |
| `sounddevice` install fails | Run `brew install portaudio` first |
| Window layout not working | AppleScript window positioning requires the app to be visible and not minimised |
