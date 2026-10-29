"""Small wrapper around Spotify's Web API via spotipy.

Handles login (OAuth) and fetches what's currently playing.
"""

import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import config
from settings import app_data_dir

SCOPE = "user-read-currently-playing user-read-playback-state"


class SpotifyClient:
    def __init__(self):
        # The token cache lives in AppData (a stable location) so the login is remembered
        # even when the app runs as an .exe (which otherwise runs in a temp folder).
        cache_path = os.path.join(app_data_dir(), ".spotify_cache")
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=config.CLIENT_ID,
                client_secret=config.CLIENT_SECRET,
                redirect_uri=config.REDIRECT_URI,
                scope=SCOPE,
                cache_path=cache_path,
                open_browser=True,
            ),
            requests_timeout=10,  # give Spotify more time on a slow network
            retries=3,            # retry automatically on temporary errors
        )

    def current_playback(self):
        """Returns Spotify's playback dict, or None on error/nothing playing."""
        try:
            return self.sp.current_playback()
        except Exception as exc:  # noqa: BLE001 - we never want to crash the overlay
            print("Spotify error:", exc)
            return None
