"""Inställningar som sparas till disk, plus var appens datamapp ligger.

Datamappen (AppData) används för BÅDE settings.json och Spotify-token-cachen,
så att en .exe kommer ihåg inloggning och inställningar mellan starter.
"""

import json
import os

from PySide6.QtCore import QObject, QStandardPaths, Signal


def app_data_dir():
    """Stabil, skrivbar mapp för inställningar och token-cache. Skapas vid behov."""
    base = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".spotify-lyrics-overlay")
    os.makedirs(base, exist_ok=True)
    return base


def settings_path():
    return os.path.join(app_data_dir(), "settings.json")


# Fält + standardvärden. Endast dessa nycklar sparas/läses.
DEFAULTS = {
    "font_size": 34,          # 14–96
    "text_color": "#FFFFFF",
    "outline_color": "#000000",
    "show_bg": True,
    "bg_opacity": 51,         # 0–100 %
    "bg_fit_text": False,     # False = plattan är lika bred som fönstret,
                              # True  = bredden krymper till den text som visas
    "show_next": True,
    "line_gap": 18,           # 0–60 (radavstånd, skalas mot textstorleken)
    "sync_offset": 0.0,       # sekunder, −3.0…+3.0
    "pos_x": None,            # sparad fönsterposition (None = standard)
    "pos_y": None,
    "locked": False,          # lås position (drag av)
}


class Settings(QObject):
    """Håller inställningarna. `changed` skickas när något ändras (för live-uppdatering)."""

    changed = Signal()

    def __init__(self, values=None):
        super().__init__()
        data = dict(DEFAULTS)
        if values:
            data.update({k: v for k, v in values.items() if k in DEFAULTS})
        for key, value in data.items():
            setattr(self, key, value)

    def update(self, **changes):
        """Sätt ett eller flera fält, spara, och meddela lyssnare — om något faktiskt ändrades."""
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
            print("Kunde inte spara inställningar:", exc)

    @classmethod
    def load(cls):
        try:
            with open(settings_path(), "r", encoding="utf-8") as f:
                return cls(json.load(f))
        except (OSError, ValueError):
            return cls()
