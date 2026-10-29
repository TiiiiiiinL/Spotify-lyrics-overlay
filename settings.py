"""Settings persisted to disk, plus where the app's data folder lives.

The data folder (AppData) is used for BOTH settings.json and the Spotify token cache,
so an .exe remembers the login and settings between launches.
"""

import json
import os

from PySide6.QtCore import QObject, QStandardPaths, Signal


def app_data_dir():
    """Stable, writable folder for settings and the token cache. Created if needed."""
    base = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".spotify-lyrics-overlay")
    os.makedirs(base, exist_ok=True)
    return base


def settings_path():
    return os.path.join(app_data_dir(), "settings.json")


# Fields + default values. Only these keys are saved/loaded.
DEFAULTS = {
    "font_size": 34,          # 14–96
    "text_color": "#FFFFFF",
    "outline_color": "#000000",
    "show_bg": True,
    "bg_opacity": 51,         # 0–100 %
    "bg_fit_text": False,     # False = backdrop is as wide as the window,
                              # True  = width shrinks to the text shown
    "show_next": True,
    "line_gap": 18,           # 0–60 (line spacing, scaled to the text size)
    "sync_offset": 0.0,       # seconds, −3.0…+3.0
    "pos_x": None,            # saved window position (None = default)
    "pos_y": None,
    "locked": False,          # lock position (dragging disabled)
}


class Settings(QObject):
    """Holds the settings. `changed` is emitted when anything changes (for live updates)."""

    changed = Signal()

    def __init__(self, values=None):
        super().__init__()
        data = dict(DEFAULTS)
        if values:
            data.update({k: v for k, v in values.items() if k in DEFAULTS})
        for key, value in data.items():
            setattr(self, key, value)

    def update(self, **changes):
        """Set one or more fields, save, and notify listeners — if anything actually changed."""
        changed = False
        for key, value in changes.items():
            if key in DEFAULTS and getattr(self, key) != value:
                setattr(self, key, value)
                changed = True
        if changed:
            self.save()
            self.changed.emit()

    def reset(self):
        for key, value in DEFAULTS.items():
            setattr(self, key, value)
        self.save()
        self.changed.emit()

    def save(self):
        data = {key: getattr(self, key) for key in DEFAULTS}
        try:
            with open(settings_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as exc:
            print("Could not save settings:", exc)

    @classmethod
    def load(cls):
        try:
            with open(settings_path(), "r", encoding="utf-8") as f:
                return cls(json.load(f))
        except (OSError, ValueError):
            return cls()
