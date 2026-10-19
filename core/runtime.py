"""Thread-safe lifecycle controls shared by the listener and tray UI."""

import threading


class RuntimeControl:
    def __init__(self):
        self._paused = threading.Event()
        self._shutdown = threading.Event()
        self._listeners = []
        self._lock = threading.Lock()

    @property
    def is_paused(self):
        return self._paused.is_set()

    @property
    def should_stop(self):
        return self._shutdown.is_set()

    def subscribe(self, callback):
        with self._lock:
            self._listeners.append(callback)

    def _notify(self):
        with self._lock:
            listeners = list(self._listeners)
        for callback in listeners:
            try:
                callback(self)
            except Exception:
                pass

    def pause(self):
        self._paused.set()
        self._notify()

    def resume(self):
        self._paused.clear()
        self._notify()

    def toggle_pause(self):
        self.resume() if self.is_paused else self.pause()

    def quit(self):
        self._shutdown.set()
        self._paused.clear()
        self._notify()

    def wait_until_resumed(self, interval=0.2):
        while self.is_paused and not self.should_stop:
            self._shutdown.wait(interval)
        return not self.should_stop
