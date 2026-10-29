"""Spotify Lyrics Overlay — floating, synced subtitles for Spotify.

Run with Windows Python (not in WSL):  python main.py
See README.md for full setup and how to build an .exe.
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

POLL_MS = 2000       # how often we ask Spotify "what's playing?"
TICK_MS = 100        # how often we update which line is shown
LYRICS_TIMEOUT = 25  # give up the lyrics search after this many seconds


class Controller:
    def __init__(self, overlay, spotify, lyrics, settings):
        self.overlay = overlay
        self.spotify = spotify
        self.lyrics = lyrics
        self.settings = settings

        self.track_id = None
        self.lines = []          # [(seconds, text), ...]
        self._times = []         # just the timestamps, for fast lookup
        self.no_lyrics = False

        self.is_playing = False
        self.base_progress = 0.0   # track position (sec) at the last poll
        self.base_time = time.monotonic()

        # Lyrics are fetched in a background thread so the window never freezes
        self._lyrics_lock = threading.Lock()
        self._lyrics_result = None       # (track_id, lrc string) set by the thread
        self._pending_track = None       # which track we are waiting for lyrics for
        self._lyrics_started = 0.0

        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll)
        self.poll_timer.start(POLL_MS)

        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self.tick)
        self.tick_timer.start(TICK_MS)

        self.poll()  # do a first fetch right away

    def poll(self):
        playback = self.spotify.current_playback()
        if not playback or not playback.get("item"):
            self.is_playing = False
            self.overlay.set_lines("", "")  # fully invisible when nothing is playing
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
        """Starts a lyrics search in a background thread (doesn't block the window)."""
        title = item["name"]
        artist = ", ".join(a["name"] for a in item["artists"])
        album = item.get("album", {}).get("name", "")
        duration = (item.get("duration_ms") or 0) / 1000.0
        track_id = item.get("id")

        print(f"▶ Now playing: {title} — {artist}")
        print("   searching for lyrics…")

        # Reset right away so old lyrics disappear on track change
        self.lines = []
        self._times = []
        self.no_lyrics = False
        self._pending_track = track_id
        self._lyrics_started = time.monotonic()

        def work():
            try:
                synced = self.lyrics.get_synced(title, artist, album, duration)
            except Exception as exc:  # noqa: BLE001
                print("   error while searching for lyrics:", exc)
                synced = None
            with self._lyrics_lock:
                self._lyrics_result = (track_id, synced)

        threading.Thread(target=work, daemon=True).start()

    def _check_lyrics(self):
        """Runs on the main thread – picks up results from the background thread."""
        with self._lyrics_lock:
            result = self._lyrics_result
            self._lyrics_result = None

        if result is not None:
            track_id, synced = result
            if track_id == self.track_id:  # ignore results for a track that has already changed
                self.lines = parse_lrc(synced)
                self._times = [t for t, _ in self.lines]
                self.no_lyrics = not self.lines
                self._pending_track = None
                if self.no_lyrics:
                    print("   (no synced lyrics found for this track)")
                else:
                    print(f"   lyrics found ({len(self.lines)} lines)")
        elif self._pending_track is not None:
            if time.monotonic() - self._lyrics_started > LYRICS_TIMEOUT:
                print("   lyrics search took too long – skipping")
                self._pending_track = None
                self.no_lyrics = True

    def tick(self):
        self._check_lyrics()

        if not self.is_playing:
            return
        if not self.lines:
            self.overlay.set_lines("", "")  # no lines → invisible (see the log for info)
            return

        # Sync offset: + makes lines change earlier
        position = (self.base_progress
                    + (time.monotonic() - self.base_time)
                    + self.settings.sync_offset)

        # Last line whose timestamp <= current position
        idx = bisect.bisect_right(self._times, position) - 1
        current = self.lines[idx][1] if idx >= 0 else ""
        nxt = self.lines[idx + 1][1] if 0 <= idx + 1 < len(self.lines) else ""
        self.overlay.set_lines(current, nxt)


def _setup_logging():
    """As an .exe (--windowed) there is no console → log to a file instead."""
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
    # Keep the app alive in the system tray even when the settings window is closed
    app.setQuitOnLastWindowClosed(False)

    _setup_logging()
    print("=== Spotify Lyrics Overlay starting ===")

    settings = Settings.load()

    print("Logging in to Spotify (a browser may open the first time)...")
    try:
        spotify = SpotifyClient()
    except Exception as exc:  # noqa: BLE001
        print("Could not start Spotify login:", exc)
        print("Have you created config.py? See README.md.")
        return 1

    print("Logged in. The overlay window and tray icon are running.")
    print("Open settings via the icon by the clock, or right-click the lyrics.")

    settings_window = SettingsWindow(settings)
    overlay = OverlayWindow(settings, on_open_settings=settings_window.show_raise)
    overlay.show()

    controller = Controller(overlay, spotify, LyricsProvider(), settings)

    # System tray icon
    tray = QSystemTrayIcon(app_qicon())
    tray.setToolTip("Spotify Lyrics Overlay")
    tray_menu = QMenu()
    tray_menu.addAction("Settings…", settings_window.show_raise)
    tray_menu.addSeparator()
    tray_menu.addAction("Quit", app.quit)
    tray.setContextMenu(tray_menu)
    tray.activated.connect(
        lambda reason: settings_window.show_raise()
        if reason == QSystemTrayIcon.Trigger else None
    )
    tray.show()

    # Keep everything alive (otherwise Python garbage-collects the objects → timers die)
    app._keepalive = (overlay, controller, settings_window, tray, settings)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
