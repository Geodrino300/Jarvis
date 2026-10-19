"""
Jarvis -- Double-Snap Detection
Listens for two quick sounds (snaps) within a time window.
Cross-platform: uses sounddevice and numpy only.
"""

import time
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 44100
BLOCK_SIZE  = 1024
THRESHOLD   = 0.12   # RMS spike threshold (tune with test-mic.py)
MIN_GAP     = 0.1    # Minimum seconds between two snaps (debounce)
MAX_GAP     = 1.2    # Maximum seconds between two snaps (double-snap window)

_last_snap_time = 0.0
_snap_count     = 0
_triggered      = False


def reset():
    global _last_snap_time, _snap_count, _triggered
    _last_snap_time = 0.0
    _snap_count     = 0
    _triggered      = False


def _audio_callback(indata, frames, time_info, status):
    global _last_snap_time, _snap_count, _triggered
    if _triggered:
        return
    now = time.time()
    rms = float(np.sqrt(np.mean(indata ** 2)))
    if rms > THRESHOLD:
        gap = now - _last_snap_time
        if gap < MIN_GAP:
            return  # Debounce -- same snap still ringing
        if gap <= MAX_GAP and _snap_count >= 1:
            print("[jarvis] Double snap detected! Launching session...", flush=True)
            _triggered = True
        else:
            _snap_count = 1
            print("[jarvis] Snap 1 detected -- waiting for snap 2...", flush=True)
        _last_snap_time = now


def wait_for_double_snap(control=None):
    """Block until a double snap, releasing the microphone while paused."""
    while not (control and control.should_stop):
        if control and not control.wait_until_resumed():
            return False
        reset()
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype="float32",
            callback=_audio_callback,
        ):
            while not _triggered:
                if control and (control.is_paused or control.should_stop):
                    break
                time.sleep(0.1)
        if _triggered:
            return True
    return False
