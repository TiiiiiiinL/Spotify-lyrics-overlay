"""Liten wrapper runt Spotifys Web API via spotipy.

Sköter inloggning (OAuth) och hämtar vad som spelas just nu.
"""

import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import config
from settings import app_data_dir

SCOPE = "user-read-currently-playing user-read-playback-state"


class SpotifyClient:
    def __init__(self):
        # Token-cachen ligger i AppData (stabil plats) så inloggningen kommer ihåg
        # även när appen körs som .exe (som annars kör i en temp-mapp).
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
            requests_timeout=10,  # ge Spotify mer tid vid segt nät
            retries=3,            # försök igen automatiskt vid tillfälliga fel
        )

    def current_playback(self):
        """Returnerar Spotifys playback-dict, eller None vid fel/inget spelas."""
        try:
            return self.sp.current_playback()
        except Exception as exc:  # noqa: BLE001 - vi vill aldrig krascha overlayn
            print("Spotify-fel:", exc)
            return None
