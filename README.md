# 🎤 Spotify Lyrics Overlay

A floating, always-on-top **subtitle for Spotify** — just like in a movie. The
lyrics sit in front of every other window, change line by line in time with the
song, and can be dragged anywhere with the mouse.

![style](https://img.shields.io/badge/style-movie%20subtitles-blue) source: **lrclib.net** (free, synced lyrics)

---

## ⚠️ Important: run it on Windows, not in WSL

The program draws on top of your regular Windows windows. That means it must be
run with **Windows Python**, not in WSL/the Linux terminal. The steps below are
for Windows.

> The files live in WSL. Open them in Windows by pasting this into the File
> Explorer address bar: `\\wsl.localhost\Ubuntu\home\<user>\spotify-lyrics-overlay`
> (replace `Ubuntu` with your Linux distro name if it's different). Copying the
> folder to e.g. `Documents` makes things easier.

---

## 1. Install Python (if you don't have it)

Download it from <https://www.python.org/downloads/> and **check
"Add Python to PATH"** during installation.

## 2. Install the program's dependencies

Open **Command Prompt** (search for "cmd" in Start), go to the folder and run:

```cmd
cd "C:\path\to\spotify-lyrics-overlay"
pip install -r requirements.txt
```

## 3. Create a free Spotify app (to read what's playing)

1. Go to <https://developer.spotify.com/dashboard> and log in.
2. Click **Create app**. The name/description doesn't matter.
3. In the **Redirect URI** field, enter exactly:
   `http://127.0.0.1:8888/callback` and click **Add**, then **Save**.
4. Open the app → **Settings**. Copy the **Client ID** and **Client secret**.

## 4. Add your keys

Copy `config.example.py` → `config.py` and paste in your values:

```python
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
```

> 🔒 **Your `config.py` is private.** It's listed in `.gitignore` and is never
> uploaded to GitHub, since it contains your own Spotify keys. The
> `.spotify_cache` file (your login) is ignored too. Always upload
> `config.example.py` – never `config.py`.

## 5. Start it!

Double-click **`run.bat`**, or run this in Command Prompt:

```cmd
python main.py
```

The first time, a browser opens where you log in to Spotify and approve access.
You're then redirected back automatically — this is only needed once.

Play a song in Spotify and the subtitles appear! 🎶

---

## Using the overlay

| What | How |
|-----|-----|
| **Move** | Drag with the left mouse button |
| **Open settings** | Click the taskbar tray icon, or right-click the lyrics → Settings |
| **Larger / smaller text** | Settings, or `+` / `–` |
| **Lock position** | Right-click the lyrics → Lock position |
| **Quit** | Tray icon → Quit, right-click → Quit, or `Esc` |

## Settings

Open the settings window via the **tray icon** (down by the clock) or
**right-click the lyrics → Settings**. Everything updates *live*:

- **Text size** and **text color / outline color**
- **Background** on/off and how **transparent** the dark backdrop is
- **Show upcoming line** on/off and **line spacing**
- **Sync offset** — shift the lyrics a few tenths of a second forward/back if
  they run ahead of or behind the song (`+` = lines change earlier)

All settings and the window position are **saved automatically** and kept until
next time. They're stored in `settings.json` in the app's data folder
(`…\AppData\Local\SpotifyLyricsOverlay`).

## System tray

The app puts a small icon down by the clock. **Click** it to open settings, or
**right-click** it for the menu (Settings / Quit). The app keeps running there
even if you close the settings window.

## Building an app file (.exe)

Want to skip cmd/Python entirely and get a double-clickable app?

1. Double-click **`build.bat`** (or run it in cmd).
2. Wait while it builds — it takes a minute or so.
3. Your finished app will be in **`dist\SpotifyLyricsOverlay.exe`**.

That file contains everything (code + Python + dependencies), so you can move it
anywhere and launch it with a double-click. Your login and settings are stored
in `AppData`, so they persist between launches.

> 🔒 Note: your Spotify keys are baked into the `.exe` file. That's fine for
> personal use, but don't share the file publicly.
>
> 🐞 Since the `.exe` runs without a console, status messages are written to
> `…\AppData\Local\SpotifyLyricsOverlay\log.txt` — check there if something
> goes wrong.

---

## Troubleshooting

- **"No synced lyrics found"** — the song is missing from lrclib.net, or only
  has unsynced lyrics. Common for very new or obscure songs.
- **Nothing happens** — is Spotify actually *playing* a song (not paused)?
  The Web API only reports active playback.
- **Lyrics are slightly behind/ahead** — the overlay re-syncs with Spotify
  every ~2 seconds. Small offsets can come from Spotify's own latency. You can
  also adjust the sync offset in Settings.
- **The login window never redirects back** — make sure the Redirect URI in
  your Spotify app is *exactly* `http://127.0.0.1:8888/callback`.

---

## How it works (briefly)

```
Spotify Web API  ──►  what's playing + position (every 2 sec)
lrclib.net       ──►  time-synced lyrics (LRC) for the song
main.py          ──►  works out the current line (interpolates between polls)
overlay.py       ──►  draws the line, borderless/transparent/always on top
```
