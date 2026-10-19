"""Small Windows system-tray presence for the Jarvis listener."""

import threading
import winreg


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "Jarvis"


def _disable_startup():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, RUN_VALUE)
    except FileNotFoundError:
        pass


def _icon_image(paused=False):
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = (245, 180, 45, 255) if paused else (52, 199, 89, 255)
    draw.ellipse((8, 8, 56, 56), fill=(24, 28, 36, 255), outline=color, width=5)
    if paused:
        draw.rectangle((23, 21, 29, 43), fill=color)
        draw.rectangle((35, 21, 41, 43), fill=color)
    else:
        draw.ellipse((26, 18, 38, 36), fill=color)
        draw.arc((20, 22, 44, 46), 0, 180, fill=color, width=4)
        draw.line((32, 46, 32, 52), fill=color, width=4)
    return image


class TrayController:
    def __init__(self, control):
        import pystray

        self.control = control
        self.pystray = pystray
        self.icon = pystray.Icon(
            "Jarvis",
            _icon_image(False),
            "Jarvis - Listening",
            menu=pystray.Menu(
                pystray.MenuItem(self._status_text, None, enabled=False),
                pystray.MenuItem(self._pause_text, self._toggle_pause),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit),
                pystray.MenuItem("Quit && Disable Startup", self._quit_and_disable),
            ),
        )
        control.subscribe(self._sync)
        self._thread = threading.Thread(target=self.icon.run, name="jarvis-tray", daemon=True)

    def _status_text(self, _item):
        return "Status: Paused" if self.control.is_paused else "Status: Listening"

    def _pause_text(self, _item):
        return "Resume Listening" if self.control.is_paused else "Pause Listening"

    def _sync(self, _control):
        try:
            self.icon.title = "Jarvis - Paused" if self.control.is_paused else "Jarvis - Listening"
            self.icon.icon = _icon_image(self.control.is_paused)
            self.icon.update_menu()
        except Exception:
            pass

    def _toggle_pause(self, _icon, _item):
        self.control.toggle_pause()

    def _quit(self, _icon, _item):
        self.control.quit()
        self.icon.stop()

    def _quit_and_disable(self, _icon, _item):
        _disable_startup()
        self.control.quit()
        self.icon.stop()

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        try:
            self.icon.stop()
        except Exception:
            pass


def start_tray(control):
    return TrayController(control).start()
