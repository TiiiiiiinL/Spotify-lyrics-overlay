"""Fetches time-synced lyrics (LRC) from the free lrclib.net API.

Spotify doesn't expose lyrics through its API, so we use lrclib as the source.
"""

import re
import requests

try:
    # Searches several lyrics services at once (lrclib, NetEase, Musixmatch, etc.)
    import syncedlyrics
except ImportError:
    syncedlyrics = None

LRCLIB = "https://lrclib.net/api"
USER_AGENT = "spotify-lyrics-overlay (https://github.com/local/overlay)"

# Matches a timestamp like [01:23.45] or [01:23]
_TAG_RE = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def parse_lrc(text):
    """Turns an LRC string into a sorted list of (seconds, line)."""
    out = []
    if not text:
        return out
    for raw in text.splitlines():
        tags = list(_TAG_RE.finditer(raw))
        if not tags:
            continue
        content = raw[tags[-1].end():].strip()
        for m in tags:
            minutes = int(m.group(1))
            seconds = float(m.group(2))
            out.append((minutes * 60 + seconds, content))
    out.sort(key=lambda item: item[0])
    return out


class LyricsProvider:
    def __init__(self):
        self._cache = {}

    def get_synced(self, title, artist, album, duration):
        """Returns an LRC string, or None if nothing synced is found."""
        key = (title.lower(), artist.lower(), round(duration))
        if key in self._cache:
            return self._cache[key]
        synced = self._fetch(title, artist, album, duration)
        self._cache[key] = synced
        return synced

    def _fetch(self, title, artist, album, duration):
        headers = {"User-Agent": USER_AGENT}

        # 0) syncedlyrics – searches SEVERAL services at once (best coverage)
        if syncedlyrics is not None:
            try:
                lrc = syncedlyrics.search(f"{title} {artist}")
                if lrc and _TAG_RE.search(lrc):  # only if it is time-synced
                    return lrc
            except Exception:  # noqa: BLE001 - fall back to lrclib below
                pass

        # 1) Exact match via /get (best when the metadata matches)
        try:
            r = requests.get(
                f"{LRCLIB}/get",
                params={
                    "track_name": title,
                    "artist_name": artist,
                    "album_name": album,
                    "duration": int(duration),
                },
                headers=headers,
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("syncedLyrics"):
                    return data["syncedLyrics"]
        except requests.RequestException:
            pass

        # 2) Fallback: search and pick the one closest in duration
        try:
            r = requests.get(
                f"{LRCLIB}/search",
                params={"track_name": title, "artist_name": artist},
                headers=headers,
                timeout=10,
            )
            if r.status_code == 200:
                candidates = [d for d in r.json() if d.get("syncedLyrics")]
                if candidates:
                    best = min(
                        candidates,
                        key=lambda d: abs((d.get("duration") or 0) - duration),
                    )
                    return best["syncedLyrics"]
        except requests.RequestException:
            pass

        return None
