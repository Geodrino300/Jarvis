"""
Jarvis — Shared TTS
ElevenLabs (primary) with Microsoft Edge TTS fallback.
Works on Windows and Mac.
"""

import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[1] / ".env")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "onwK4e9ZLuTAKqWW03F9")
EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "en-GB-RyanNeural")


def _play_mp3_bytes(audio_bytes):
    """Platform-aware MP3 playback."""
    if sys.platform == "win32":
        _play_mp3_bytes_windows(audio_bytes)
    else:
        _play_mp3_bytes_mac(audio_bytes)


def _play_mp3_bytes_windows(audio_bytes):
    """Play MP3 bytes using Windows MCI (no external packages)."""
    import ctypes

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    try:
        winmm = ctypes.windll.winmm
        winmm.mciSendStringW(f'open "{temp_path}" type mpegvideo alias jarvis_audio', None, 0, None)
        winmm.mciSendStringW('play jarvis_audio', None, 0, None)  # non-blocking

        buf = ctypes.create_unicode_buffer(128)
        while True:
            winmm.mciSendStringW('status jarvis_audio mode', buf, 128, None)
            if buf.value != 'playing':
                break
            time.sleep(0.1)

        winmm.mciSendStringW('stop jarvis_audio', None, 0, None)
        winmm.mciSendStringW('close jarvis_audio', None, 0, None)
    finally:
        try:
            os.unlink(temp_path)
        except Exception:
            pass


def _play_mp3_bytes_mac(audio_bytes):
    """Play MP3 bytes using afplay (ships with macOS)."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    try:
        subprocess.run(["afplay", temp_path], check=True)
    except Exception as e:
        print(f"[speech] afplay error: {e}", flush=True)
    finally:
        try:
            os.unlink(temp_path)
        except Exception:
            pass


def _speak_edge(text):
    """Speak via Microsoft Edge TTS — free, no API key, neural quality."""
    import asyncio
    import edge_tts

    async def _generate():
        communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        return audio_bytes

    audio_bytes = asyncio.run(_generate())
    _play_mp3_bytes(audio_bytes)


def speak(text):
    """
    Speak text aloud.
    Uses ElevenLabs if available; falls back to Edge TTS on quota or missing key.
    """
    print(f"[jarvis] {text}", flush=True)
    if ELEVENLABS_API_KEY:
        try:
            from elevenlabs.client import ElevenLabs
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            audio_gen = client.text_to_speech.convert(
                voice_id=ELEVENLABS_VOICE_ID,
                text=text,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128",
            )
            audio_bytes = b"".join(audio_gen)
            _play_mp3_bytes(audio_bytes)
            return
        except Exception as e:
            if "quota_exceeded" in str(e):
                print("[speech] ElevenLabs quota exceeded -- switching to Edge TTS.", flush=True)
            else:
                print(f"[speech] ElevenLabs error: {e}", flush=True)
    try:
        _speak_edge(text)
    except Exception as e:
        print(f"[speech] Edge TTS error: {e}", flush=True)
