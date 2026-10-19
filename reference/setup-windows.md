# Jarvis Setup Guide — Windows

Get Jarvis running from scratch on Windows 10 or 11. Follow these steps in order.

**Total time:** ~20–30 minutes

---

## Step 1: Check Your System

Open a **new PowerShell window** and run each check.

### Python
```powershell
python --version
```
Need **3.10 or higher**. If missing or outdated:
→ Download from [python.org/downloads](https://python.org/downloads)
→ During install, check **"Add Python to PATH"**
→ Re-open PowerShell after installing

### Claude Code
```powershell
claude --version
```
If missing: install from [claude.ai/download](https://claude.ai/download)

---

## Step 2: Clone the Repo

```powershell
git clone https://github.com/chichen/jarvis.git
cd jarvis
```

---

## Step 3: Install Python Packages

```powershell
pip install sounddevice numpy requests anthropic elevenlabs edge-tts python-dotenv speechrecognition pywin32 psutil vosk pillow
```

**Optional — offline speech-to-text fallback (~2GB):**
```powershell
pip install openai-whisper
```
Skip this if you have a reliable internet connection. Jarvis uses Google STT by default and only falls back to Whisper if Google fails.

### Install the Vosk wake-word model

Vosk detects the "Jarvis" wake word offline.

1. Download `vosk-model-small-en-us-0.15` (~50MB) from [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)
2. Unzip it
3. Place the folder at:
   ```
   C:\Users\<YourUsername>\AppData\Local\vosk\vosk-model-small-en-us-0.15
   ```

Verify:
```powershell
python -c "import vosk; print('Vosk OK')"
```

---

## Step 4: Add Your API Keys

```powershell
notepad .env
```

Fill in:
```
ELEVENLABS_API_KEY=your_key_here    # elevenlabs.io → Profile → API Key
ANTHROPIC_API_KEY=your_key_here     # console.anthropic.com → API Keys
WORKSPACE_PATH=C:\projects\myapp    # folder VS Code + Claude Code open in
```

**ElevenLabs** is optional. If you leave `ELEVENLABS_API_KEY` blank, Jarvis uses Microsoft Edge TTS — a free, neural-quality British voice with no API key required. ElevenLabs gives a higher quality voice if you have an account (free tier: 10,000 characters/month).

Verify keys are loading:
```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print('EL:', 'OK' if os.getenv('ELEVENLABS_API_KEY') else 'MISSING'); print('Anthropic:', 'OK' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING')"
```

---

## Step 5: Configure Which Apps Launch

Open `platforms/windows/launcher.py` and toggle each app:

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

### Claude Desktop app ID
If Claude Desktop doesn't open, find your app ID:
```powershell
Get-AppxPackage | Where-Object { $_.Name -like "*Claude*" } | Select-Object PackageFamilyName
```
Update `launch_claude_desktop()` in `launcher.py` with the correct ID.

---

## Step 6: Configure Your Window Layout (Optional)

If `ARRANGE_WINDOWS = True`, Jarvis repositions all windows after launch.

Open `platforms/windows/window_manager.py` and edit `WINDOW_LAYOUT`. Format: `(x, y, width, height)`.

### Find your window titles
```powershell
python -c "import win32gui; win32gui.EnumWindows(lambda h,_: print(repr(win32gui.GetWindowText(h))) if win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h) else None, None)"
```

### Common layouts

| Monitor | Left half | Right half |
|---------|-----------|------------|
| 1920×1080 | `(0, 0, 960, 1080)` | `(960, 0, 960, 1080)` |
| 2560×1440 | `(0, 0, 1280, 1440)` | `(1280, 0, 1280, 1440)` |
| 3440×1440 ultrawide | `(0, 0, 1720, 1440)` | `(1720, 0, 1720, 1440)` |
| 5120×1440 super ultrawide | Four columns of `1280` each |

Say **"arrange windows"** at any time to re-apply the layout.

---

## Step 7: Set Up Wallpaper Engine (Optional)

Jarvis can trigger a live video wallpaper on double-snap using **Wallpaper Engine** — a Steam app (~$4) that replaces your desktop background with looping videos, animations, or scenes.

### Install Wallpaper Engine
1. Buy and install [Wallpaper Engine on Steam](https://store.steampowered.com/app/431960/Wallpaper_Engine/)
2. Launch it and set a wallpaper you like — the [Steam Workshop](https://steamcommunity.com/app/431960/workshop/) has thousands of free options

### Set up a looping video wallpaper
1. In Wallpaper Engine, find a wallpaper you want (video or scene)
2. Right-click it → **Edit** (or open its settings)
3. Make sure **Loop** is enabled

### Assign the Shift+F1 hotkey
Jarvis activates Wallpaper Engine by sending the `Shift+F1` global hotkey on double-snap. You need to configure this in Wallpaper Engine:

1. Open Wallpaper Engine → **Settings** (gear icon)
2. Go to **Hotkeys**
3. Find **"Replace wallpaper"** or **"Next wallpaper"** — set it to `Shift+F1`

> Jarvis sends `Shift+F1` via Windows SendInput, so it works even when Wallpaper Engine is in the background.

### Enable in Jarvis
In `platforms/windows/launcher.py`:
```python
LAUNCH_WALLPAPER_ENGINE = True
```

When enabled, Jarvis fires the `Shift+F1` hotkey at the very start of the double-snap sequence — before apps open, before the greeting. The wallpaper activates first, then everything else follows.

### Disable it
```python
LAUNCH_WALLPAPER_ENGINE = False
```

---

## Step 8: Tune Snap Sensitivity

Run the mic calibration tool and snap a few times:
```powershell
python scripts/test-mic.py
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

```powershell
python core/hue.py --setup
```

Press the button on your bridge when prompted. The script prints your `HUE_BRIDGE_IP` and `HUE_API_KEY` — paste them into `.env`.

Verify:
```powershell
python core/hue.py --list
python core/hue.py --cmd "dim the office"
```

---

## Step 10: Set Your Context

Run `/context` inside Claude Code to fill in your personal context files (your name, goals, how you like to be briefed). Jarvis reads these every session.

---

## Step 11: First Run

Type `/jarvis` inside Claude Code to start.

> **Note:** If you just cloned the repo, you need to fully close and reopen Claude Code first — it won't recognise `/jarvis` until it's restarted.

Double-snap near your mic. Jarvis greets you and your apps open. Then say **"Jarvis"** followed by any command.

**Alternatively**, you can launch directly from PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\startup.ps1"
```

---

## Launch Options

### Option A — Manual (default)
```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\startup.ps1"
```

### Option B — Desktop shortcut (one click per project)
```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\create-shortcut.ps1" -ProjectPath "C:\projects\myapp"
```
Double-click the desktop shortcut — Claude Code opens in that project and Jarvis arms immediately.

### Option C — Auto-launch at login
```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\setup-autostart.ps1"
```
Run once. Jarvis + Claude Code start automatically every time you sign in.

To remove:
```powershell
Unregister-ScheduledTask -TaskName "Jarvis Autostart" -Confirm:$false
```

---

## Troubleshooting

| Problem | Check |
|---------|-------|
| Nothing happens on snap | Run `python scripts/test-mic.py` — do you see RMS spikes when you snap? |
| "No module named X" | Run `pip install X` |
| Voice not working | Check `ELEVENLABS_API_KEY` in `.env` — Edge TTS will kick in as fallback |
| Claude Code not receiving commands | Make sure Claude Code is running in a PowerShell window |
| Apps not opening | Check the toggle is `True` and the app is installed |
| Window layout wrong | Run `python -c "import win32gui; ..."` to find exact window titles |
