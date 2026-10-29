"""Fetches time-synced lyrics (LRC) from the free lrclib.net API.

Spotify doesn't expose lyrics through its API, so we use lrclib as the source.
Every result is checked against the track's artist and duration — showing no
lyrics is better than showing the wrong song's lyrics.
"""

import re
import unicodedata

import requests

try:
    # Searches several lyrics services at once (lrclib, NetEase, Musixmatch, etc.)
    import syncedlyrics
except ImportError:
    syncedlyrics = None

LRCLIB = "https://lrclib.net/api"
USER_AGENT = "spotify-lyrics-overlay (https://github.com/TiiiiiiinL/Spotify-lyrics-overlay)"

# Max difference (seconds) between Spotify's duration and a search result's
DURATION_TOLERANCE = 3

# Matches a timestamp like [01:23.45] or [01:23]
_TAG_RE = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")
# Matches an artist header like [ar: Some Artist]
_ARTIST_TAG_RE = re.compile(r"^\[ar:\s*(.*?)\s*\]", re.IGNORECASE | re.MULTILINE)


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


def _normalize(name):
    """Lowercase, strip accents and everything that isn't a letter/digit.
    "Beyoncé" → "beyonce", "AC/DC" → "acdc". Non-Latin letters are kept."""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return "".join(c for c in name.lower() if c.isalnum())


def _artist_matches(candidate, artists):
    """True if any of the track's artists appears in the candidate's artist
    string (or vice versa), e.g. "Drake feat. Rihanna" matches ["Drake"]."""
    cand = _normalize(candidate or "")
    if not cand:
        return False
    for artist in artists:
        a = _normalize(artist)
        if a and (a in cand or cand in a):
            return True
    return False


def _plausible_lrc(lrc, artists, duration):
    """Sanity check for results without metadata (syncedlyrics): the lyrics must
    fit within the track and, if the LRC names an artist, it must match."""
    lines = parse_lrc(lrc)
    if not lines:
        return False
    last = lines[-1][0]
    if duration and not (duration * 0.5 <= last <= duration + DURATION_TOLERANCE):
        return False
    tag = _ARTIST_TAG_RE.search(lrc)
    if tag and tag.group(1) and not _artist_matches(tag.group(1), artists):
        return False
    return True


class LyricsProvider:
    def __init__(self):
        self._cache = {}

    def get_synced(self, title, artists, album, duration):
        """Returns an LRC string, or None if nothing synced (and matching) is found.
        `artists` is the list of artist names from Spotify."""
        key = (title.lower(), tuple(a.lower() for a in artists), round(duration))
        if key in self._cache:
            return self._cache[key]
        synced = self._fetch(title, artists, album, duration)
        self._cache[key] = synced
        return synced

    def _fetch(self, title, artists, album, duration):
        headers = {"User-Agent": USER_AGENT}
        primary = artists[0] if artists else ""
        joined = ", ".join(artists)

        # 1) Exact match via /get (title + artist + album + duration must all match).
        #    Try the full artist list first, then just the main artist.
        for artist_name in dict.fromkeys([joined, primary]):
            try:
                r = requests.get(
                    f"{LRCLIB}/get",
                    params={
                        "track_name": title,
                        "artist_name": artist_name,
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

        # 2) Search, but only accept results with the right artist and duration
        try:
            r = requests.get(
                f"{LRCLIB}/search",
                params={"track_name": title, "artist_name": primary},
                headers=headers,
                timeout=10,
            )
            if r.status_code == 200:
                candidates = [
                    d for d in r.json()
                    if d.get("syncedLyrics")
                    and _artist_matches(d.get("artistName"), artists)
                    and abs((d.get("duration") or 0) - duration) <= DURATION_TOLERANCE
                ]
                if candidates:
                    best = min(
                        candidates,
                        key=lambda d: abs((d.get("duration") or 0) - duration),
                    )
                    return best["syncedLyrics"]
        except requests.RequestException:
            pass

        # 3) Last resort: syncedlyrics searches SEVERAL services, but returns only
        #    the lyrics text — so it has to pass a plausibility check.
        if syncedlyrics is not None:
            try:
                lrc = syncedlyrics.search(f"{title} {primary}")
                if lrc and _plausible_lrc(lrc, artists, duration):
                    return lrc
            except Exception:  # noqa: BLE001 - never crash on a lyrics lookup
                pass

        return None
