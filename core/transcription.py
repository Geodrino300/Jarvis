"""
Jarvis -- Speech-to-Text
Records audio until silence, then transcribes.
Google STT (primary) with Whisper fallback.
Cross-platform: uses sounddevice and numpy only.
"""

import io
import json
import wave
import numpy as np
import sounddevice as sd

SAMPLE_RATE          = 16000  # Vosk requires 16kHz
SILENCE_TIMEOUT      = 1.5    # seconds of silence to stop recording
MAX_RECORD_SECS      = 10     # max recording duration
SILENCE_RMS          = 0.01   # RMS below this = silence

_whisper_model = None


def record_until_silence(control=None):
    """
    Record from mic at 16kHz until silence or max duration.
    Returns int16 numpy array.
    """
    chunk_size           = int(SAMPLE_RATE * 0.1)  # 100ms chunks
    max_chunks           = int(MAX_RECORD_SECS / 0.1)
    silent_chunks_needed = int(SILENCE_TIMEOUT / 0.1)

    frames       = []
    silent_count = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=chunk_size) as stream:
        for _ in range(max_chunks):
            if control and (control.is_paused or control.should_stop):
                break
            chunk, _ = stream.read(chunk_size)
            frames.append(chunk.copy())
            rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
            if rms < SILENCE_RMS * 32768:
                silent_count += 1
                if silent_count >= silent_chunks_needed:
                    break
            else:
                silent_count = 0

    if not frames:
        return np.array([], dtype=np.int16)
    return np.concatenate(frames, axis=0).flatten()


def audio_to_sr(audio_int16):
    """Convert int16 numpy array to speech_recognition.AudioData."""
    import speech_recognition as sr
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())
    buf.seek(0)
    with sr.AudioFile(buf) as source:
        return sr.Recognizer().record(source)


def _get_whisper_model():
    """Lazy-load Whisper tiny model (~75MB download on first use)."""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print("[stt] Loading Whisper tiny model...", flush=True)
        _whisper_model = whisper.load_model("tiny")
    return _whisper_model


def _transcribe_vosk(audio_int16, vosk_model):
    """Use the already-loaded wake-word model as an offline command fallback."""
    from vosk import KaldiRecognizer

    recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)
    recognizer.AcceptWaveform(audio_int16.tobytes())
    return json.loads(recognizer.FinalResult()).get("text", "").strip()


def transcribe(audio_int16, vosk_model=None):
    """
    Transcribe audio. Tries Google STT first, Whisper as fallback.
    Returns transcribed string or None.
    """
    import speech_recognition as sr
    r = sr.Recognizer()
    audio_data = audio_to_sr(audio_int16)

    try:
        text = r.recognize_google(audio_data)
        print(f"[stt] Google: {text}", flush=True)
        return text
    except sr.UnknownValueError:
        print("[stt] Google: couldn't understand audio, trying offline fallback...", flush=True)
    except Exception as e:
        print(f"[stt] Google failed ({e}), trying offline fallback...", flush=True)

    if vosk_model is not None:
        try:
            text = _transcribe_vosk(audio_int16, vosk_model)
            if text:
                print(f"[stt] Vosk: {text}", flush=True)
                return text
            print("[stt] Vosk: couldn't understand audio", flush=True)
        except Exception as e:
            print(f"[stt] Vosk failed ({e})", flush=True)

    try:
        model = _get_whisper_model()
        audio_float = audio_int16.astype(np.float32) / 32768.0
        result = model.transcribe(audio_float, fp16=False, language="en")
        text = result["text"].strip()
        print(f"[stt] Whisper: {text}", flush=True)
        return text if text else None
    except Exception as e:
        print(f"[stt] Whisper failed ({e})", flush=True)
        return None
