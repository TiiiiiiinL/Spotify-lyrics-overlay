"""Hämtar tidssynkade låttexter (LRC) från det gratis API:t lrclib.net.

Spotify ger inte ut låttexter via sitt API, så vi använder lrclib som källa.
"""

import re
import requests

try:
    # Söker i flera texttjänster samtidigt (lrclib, NetEase, Musixmatch m.fl.)
    import syncedlyrics
except ImportError:
    syncedlyrics = None

LRCLIB = "https://lrclib.net/api"
USER_AGENT = "spotify-lyrics-overlay (https://github.com/local/overlay)"

# Matchar en tidsstämpel som [01:23.45] eller [01:23]
_TAG_RE = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def parse_lrc(text):
    """Gör om en LRC-sträng till en sorterad lista av (sekund, rad)."""
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
        """Returnerar en LRC-sträng eller None om inget synkat hittas."""
        key = (title.lower(), artist.lower(), round(duration))
        if key in self._cache:
            return self._cache[key]
        synced = self._fetch(title, artist, album, duration)
        self._cache[key] = synced
        return synced

    def _fetch(self, title, artist, album, duration):
        headers = {"User-Agent": USER_AGENT}

        # 0) syncedlyrics – söker i FLERA tjänster på en gång (bäst täckning)
        if syncedlyrics is not None:
            try:
                lrc = syncedlyrics.search(f"{title} {artist}")
                if lrc and _TAG_RE.search(lrc):  # bara om den är tidssynkad
                    return lrc
            except Exception:  # noqa: BLE001 - falla tillbaka på lrclib nedan
                pass

        # 1) Exakt träff via /get (bäst om metadatan stämmer)
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

        # 2) Fallback: sök och välj den som ligger närmast i längd
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
