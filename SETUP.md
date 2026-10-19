# Jarvis Setup

This guide gets Jarvis running from a clean checkout. Keep all API keys in your local `.env` file—never paste real keys into GitHub.

## 1. Requirements

- Windows 10/11 or macOS 12+
- Python 3.10 or newer
- Git
- A microphone
- The Codex desktop app or Claude Code, depending on the terminal integration you use
- An Anthropic API key for generated responses
- Optional: an ElevenLabs API key for premium text-to-speech

## 2. Download Jarvis

The repository is private, so sign in to GitHub before cloning it.

```bash
git clone https://github.com/Geodrino300/Jarvis.git
cd Jarvis
```

You can also download the repository as a ZIP from GitHub's **Code** menu and extract it.

## 3. Create a virtual environment

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### macOS Terminal

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. Install dependencies

With the virtual environment active, run:

```bash
pip install sounddevice numpy requests anthropic elevenlabs edge-tts python-dotenv speechrecognition vosk pillow
```

Windows also needs:

```powershell
pip install pywin32 psutil
```

On macOS, install PortAudio first if `sounddevice` fails:

```bash
brew install portaudio
pip install sounddevice
```

Optional offline speech-to-text fallback:

```bash
pip install openai-whisper
```

## 5. Configure local settings safely

Create your private `.env` file from the included template.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
notepad .env
```

### macOS Terminal

```bash
cp .env.example .env
open -e .env
```

Fill in only the values you use:

```dotenv
ELEVENLABS_API_KEY=
ANTHROPIC_API_KEY=
WORKSPACE_PATH=
HUE_BRIDGE_IP=
HUE_API_KEY=
```

Security rules:

- Never commit `.env`.
- Never put real keys in `.env.example`, screenshots, issues, or chat messages.
- The repository's `.gitignore` blocks `.env` and common credential files.
- If a real key is ever committed, remove it and rotate it with the provider immediately.

ElevenLabs is optional. If its key is blank, Jarvis can use Edge TTS.

## 6. Install the Vosk wake-word model

Download `vosk-model-small-en-us-0.15` from [Vosk models](https://alphacephei.com/vosk/models), extract it, and place it here:

- Windows: `%LOCALAPPDATA%\vosk\vosk-model-small-en-us-0.15`
- macOS: `~/.local/share/vosk/vosk-model-small-en-us-0.15`

Verify the package:

```bash
python -c "import vosk; print('Vosk OK')"
```

Use `python3` instead of `python` on macOS if required.

## 7. Configure optional features

- App launching: edit `platforms/windows/launcher.py` or `platforms/mac/launcher.py`.
- Window positions: edit the matching `window_manager.py` file.
- Microphone sensitivity: run `python scripts/test-mic.py`, then adjust `THRESHOLD`, `MIN_GAP`, and `MAX_GAP` in `core/snap.py`.
- Philips Hue: run `python core/hue.py --setup`, then store the bridge address and generated key in `.env`.
- Google Calendar: install `requirements-calendar.txt`, place the OAuth client file in your local Jarvis application-data folder, and run `python scripts/setup-google-calendar.py`. OAuth files must stay outside the repository.

On macOS, grant your terminal app Accessibility permission under **System Settings → Privacy & Security → Accessibility** so Jarvis can send commands to it.

## 8. Start Jarvis

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\startup.ps1"
```

Run in the background and configure login startup:

```powershell
powershell -ExecutionPolicy Bypass -File "platforms\windows\setup-autostart.ps1"
powershell -ExecutionPolicy Bypass -File "platforms\windows\startup.ps1" -Mode daemon -Background
```

### macOS

```bash
chmod +x platforms/mac/*.sh
./platforms/mac/startup.sh
```

Configure login startup:

```bash
bash platforms/mac/setup-autostart.sh
```

## 9. Test the installation

1. Run `python scripts/test-mic.py` and confirm the input level reacts to a snap.
2. Start Jarvis using the command for your operating system.
3. Double-snap near the microphone.
4. Say **“Jarvis”**, wait for the beep, and speak a short command.
5. If enabled, test Hue with `python core/hue.py --cmd "dim the office"`.

## Troubleshooting

| Problem | What to check |
|---|---|
| Python module is missing | Activate `venv`, then install the missing package. |
| Snaps are not detected | Run `scripts/test-mic.py` and lower `THRESHOLD` in `core/snap.py`. |
| Normal sounds trigger Jarvis | Increase `THRESHOLD`. |
| No spoken response | Check local `.env` settings; Edge TTS is the fallback when ElevenLabs is blank. |
| Commands do not reach the terminal | Make sure the target app is running; on macOS, verify Accessibility permission. |
| Apps do not launch | Check the feature toggles and app paths in the platform launcher. |
| Calendar does not work | Confirm the Calendar API is enabled and rerun the one-time OAuth setup script. |

For platform-specific details, see [Windows setup](reference/setup-windows.md) or [macOS setup](reference/setup-mac.md).
