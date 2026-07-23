"""Spotify Lyrics Overlay — flytande, synkad undertext för Spotify.

Kör med Windows-Python (inte i WSL):  python main.py
Se README.md för full installation och hur man bygger en .exe.
"""

import bisect
import os
import sys
import threading
import time

from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PySide6.QtCore import QTimer

from appicon import app_qicon
from overlay import OverlayWindow
from settings import Settings, app_data_dir
from settings_window import SettingsWindow
from spotify_client import SpotifyClient
from lyrics_provider import LyricsProvider, parse_lrc

POLL_MS = 2000       # hur ofta vi frågar Spotify "vad spelas?"
TICK_MS = 100        # hur ofta vi uppdaterar vilken rad som visas
LYRICS_TIMEOUT = 25  # ge upp textsökningen efter så här många sekunder


class Controller:
    def __init__(self, overlay, spotify, lyrics, settings):
        self.overlay = overlay
        self.spotify = spotify
        self.lyrics = lyrics
        self.settings = settings

        self.track_id = None
        self.lines = []          # [(sekund, text), ...]
        self._times = []         # bara tiderna, för snabb sökning
        self.no_lyrics = False

        self.is_playing = False
        self.base_progress = 0.0   # låtens position (sek) vid senaste poll
        self.base_time = time.monotonic()

        # Textsökning sker i en bakgrundstråd så fönstret aldrig fryser
        self._lyrics_lock = threading.Lock()
        self._lyrics_result = None       # (track_id, lrc-sträng) satt av tråden
        self._pending_track = None       # vilken låt vi väntar text för
        self._lyrics_started = 0.0

        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll)
        self.poll_timer.start(POLL_MS)

        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self.tick)
        self.tick_timer.start(TICK_MS)

        self.poll()  # gör en första hämtning direkt

    def poll(self):
        playback = self.spotify.current_playback()
        if not playback or not playback.get("item"):
            self.is_playing = False
            self.overlay.set_lines("", "")  # helt osynlig när inget spelas
            return

        item = playback["item"]
        self.is_playing = playback.get("is_playing", False)
        self.base_progress = (playback.get("progress_ms") or 0) / 1000.0
        self.base_time = time.monotonic()

        track_id = item.get("id")
        if track_id != self.track_id:
            self.track_id = track_id
            self._start_lyrics_fetch(item)

    def _start_lyrics_fetch(self, item):
        """Startar textsökning i en bakgrundstråd (blockerar inte fönstret)."""
        title = item["name"]
        artist = ", ".join(a["name"] for a in item["artists"])
        album = item.get("album", {}).get("name", "")
        duration = (item.get("duration_ms") or 0) / 1000.0
        track_id = item.get("id")

        print(f"▶ Spelar nu: {title} — {artist}")
        print("   söker text…")

        # Nollställ direkt så gammal text försvinner vid låtbyte
        self.lines = []
        self._times = []
        self.no_lyrics = False
        self._pending_track = track_id
        self._lyrics_started = time.monotonic()

        def work():
            try:
                synced = self.lyrics.get_synced(title, artist, album, duration)
            except Exception as exc:  # noqa: BLE001
                print("   fel vid textsökning:", exc)
                synced = None
            with self._lyrics_lock:
                self._lyrics_result = (track_id, synced)

        threading.Thread(target=work, daemon=True).start()

    def _check_lyrics(self):
        """Körs på huvudtråden – plockar upp resultat från bakgrundstråden."""
        with self._lyrics_lock:
            result = self._lyrics_result
            self._lyrics_result = None

        if result is not None:
            track_id, synced = result
            if track_id == self.track_id:  # ignorera svar för en redan bytt låt
                self.lines = parse_lrc(synced)
                self._times = [t for t, _ in self.lines]
                self.no_lyrics = not self.lines
                self._pending_track = None
                if self.no_lyrics:
                    print("   (ingen synkad text hittades för den här låten)")
                else:
                    print(f"   text hittad ({len(self.lines)} rader)")
        elif self._pending_track is not None:
            if time.monotonic() - self._lyrics_started > LYRICS_TIMEOUT:
                print("   textsökningen tog för lång tid – hoppar över")
                self._pending_track = None
                self.no_lyrics = True

    def tick(self):
        self._check_lyrics()

        if not self.is_playing:
            return
        if not self.lines:
            self.overlay.set_lines("", "")  # inga rader → osynlig (se loggen för info)
            return

        # Synk-justering: + gör att texten byts tidigare
        position = (self.base_progress
                    + (time.monotonic() - self.base_time)
                    + self.settings.sync_offset)

        # Sista raden vars tidsstämpel <= nuvarande position
        idx = bisect.bisect_right(self._times, position) - 1
        current = self.lines[idx][1] if idx >= 0 else ""
        nxt = self.lines[idx + 1][1] if 0 <= idx + 1 < len(self.lines) else ""
        self.overlay.set_lines(current, nxt)


def _setup_logging():
    """Som .exe (--windowed) finns ingen konsol → logga till fil istället."""
    if getattr(sys, "frozen", False):
        try:
            log = open(os.path.join(app_data_dir(), "log.txt"), "a",
                       encoding="utf-8", buffering=1)
            sys.stdout = log
            sys.stderr = log
        except OSError:
            pass


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SpotifyLyricsOverlay")
    app.setWindowIcon(app_qicon())
    # Appen ska leva kvar i aktivitetsfältet även när inställningsfönstret stängs
    app.setQuitOnLastWindowClosed(False)

    _setup_logging()
    print("=== Spotify Lyrics Overlay startar ===")

    settings = Settings.load()

    print("Loggar in på Spotify (en webbläsare kan öppnas första gången)...")
    try:
        spotify = SpotifyClient()
    except Exception as exc:  # noqa: BLE001
        print("Kunde inte starta Spotify-inloggning:", exc)
        print("Har du skapat config.py? Se README.md.")
        return 1

    print("Inloggad. Overlay-fönstret och aktivitetsfält-ikonen är igång.")
    print("Öppna inställningar via ikonen nere vid klockan, eller högerklicka på texten.")

    settings_window = SettingsWindow(settings)
    overlay = OverlayWindow(settings, on_open_settings=settings_window.show_raise)
    overlay.show()

    controller = Controller(overlay, spotify, LyricsProvider(), settings)

    # Aktivitetsfält-ikon (system tray)
    tray = QSystemTrayIcon(app_qicon())
    tray.setToolTip("Spotify Lyrics Overlay")
    tray_menu = QMenu()
    tray_menu.addAction("Inställningar…", settings_window.show_raise)
    tray_menu.addSeparator()
    tray_menu.addAction("Avsluta", app.quit)
    tray.setContextMenu(tray_menu)
    tray.activated.connect(
        lambda reason: settings_window.show_raise()
        if reason == QSystemTrayIcon.Trigger else None
    )
    tray.show()

    # Håll allt vid liv (annars städar Python bort objekten → timrarna dör)
    app._keepalive = (overlay, controller, settings_window, tray, settings)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
